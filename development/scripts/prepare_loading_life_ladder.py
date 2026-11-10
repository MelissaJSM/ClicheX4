"""Prepare bounded UI and ladder fixes on the accepted Ultimate build."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_closing
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_loading_life_ladder import load,D,PARENT,PARENT_HASH,SOURCE_HASH
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.discover_inputs import sha256,psx_arc
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.prepare_shibuki_armor_motion import identical
from scripts.register_shibuki_ultimate_production import component,bbox
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_ui_atlas import local_composition,aliased_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static,patch_static
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

def render_texture(raw):
    a=np.frombuffer(raw,np.uint8);out=np.empty(len(a)*2,np.uint8);out[::2]=a&15;out[1::2]=a>>4
    return out.reshape(-1,256)

def text_image(font,text):
    glyphs=[]
    for ch in text:
        # Native 16x16 uppercase alphabet: A starts after ten decimal digits.
        i=10+ord(ch)-ord('A');a=font[i//16*16:i//16*16+16,i%16*16:i%16*16+16]
        y,x=np.nonzero(a)
        if not len(x):raise ValueError('Empty font glyph')
        glyphs.append(a[:,int(x.min()):int(x.max())+1])
    return np.concatenate([a for a in glyphs],axis=1)

def loading(files,out):
    menu=files['MOJIPAT.ARC'];arc=files['LOAD_U.ARC'];tex=entry(arc,0x10008);font=render_texture(entry(arc,0x10001))
    targets={5:text_image(font,'SHIBUKI'),6:text_image(font,'RIKO')}
    # Preserve a 32px right edge, extending Shibuki's label left into spare space.
    images={};limits={5:48,6:32}
    for n,a in targets.items():
        limit=limits[n]
        if a.shape[1]>limit-4:a=np.array(Image.fromarray(a).resize((limit-4,16),Image.Resampling.NEAREST))
        image=np.zeros((16,limit),np.uint8);image[:,:a.shape[1]]=a;images[n]=image
        Image.fromarray(image*17).resize((limit*6,96),Image.Resampling.NEAREST).save(out/f'loading_name_{n}.png')
    count=aliased_composition(menu,2,0)['bank_frame_count'];used=set()
    for n in range(count):
        if n not in targets:used|={p['page']*256+p['tile'] for p in aliased_composition(menu,2,n)['parts']}
    available=[t for t in range(len(tex)//128) if t not in used]
    required=sum(limits.values())//16
    if len(available)<required:raise ValueError('Loading atlas has no isolated name space')
    newtex=bytearray(tex);replacement={};allocated={}
    for n,a in images.items():
        length=a.shape[1]//16
        first=next((t for t in available if t%16+length<=16 and all(v in available for v in range(t,t+length))),None)
        if first is None:raise ValueError('No contiguous loading label space')
        rr=[];tiles=[]
        for x in range(0,a.shape[1],16):
            t=first+x//16;available.remove(t);tiles.append(t);write_tile(newtex,t,a[:,x:x+16].tobytes());rr.append(struct.pack('<BBbb',t//256,t%256,x+(32-a.shape[1]),0))
        replacement[n]=b''.join(rr);allocated[n]=tiles
    # The logo's upper-left 16x16 cell is entirely transparent. Omit its draw
    # record to fit Shibuki's third cell without expanding the existing bank.
    logo=aliased_composition(menu,2,1);blank=logo['parts'][0]
    if (blank['page'],blank['tile'],blank['x'],blank['y'])!=(0,112,0,0) or any(tile_pixels(tex,112)):
        raise ValueError('Expected transparent logo cell missing')
    replacement[1]=records(menu,2,1)[4:]
    newmenu,slack=repack_parts(menu,2,replacement)
    checked=0
    for n in range(count):
        cp=aliased_composition(newmenu,2,n);got=compose_static(newtex,local_composition(cp))
        if n in targets:
            if got[:2]!=(images[n].tobytes(),(images[n].shape[1],16)):raise ValueError('Loading name roundtrip differs')
        elif (n!=1 and records(menu,2,n)!=records(newmenu,2,n)) or got[:3]!=compose_static(tex,local_composition(aliased_composition(menu,2,n)))[:3]:raise ValueError('Unrelated loading/menu frame changed')
        else:checked+=1
    # The loading renderer uses a separate fixed-rectangle table in the EXE,
    # not MOJIPAT. Prepare a bounded data-only proposal, never modify a BIN here.
    exe=files['SLUS_005.61'];ne=bytearray(exe);table=0xDED04
    original=bytes.fromhex('2000c000080101001000c0000a0201003000c0000c040100')
    if exe[table+24:table+48]!=original:raise ValueError('Loading draw table differs')
    ne[table+24:table+48]=struct.pack('<hhBBBB',16,192,allocated[5][0],3,1,0)+struct.pack('<hhBBBB',32,192,allocated[6][0],2,1,0)+struct.pack('<hhBBBB',64,192,12,4,1,0)
    edits=[{'file_offset':i,'ram_address':i-0x800+0x80010000,'before':a,'after':b} for i,(a,b) in enumerate(zip(exe,ne)) if a!=b]
    if len(edits)!=5:raise ValueError('Unexpected EXE proposal scope')
    atlas=render_texture(bytes(newtex))
    for n,x in ((5,16),(6,32)):
        preview=np.zeros((240,320),np.uint8);t=allocated[n][0];w=limits[n]
        preview[192:208,x:x+w]=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+w]
        preview[192:208,64:128]=atlas[:16,192:256]
        preview[96:112,96:224]=atlas[:16,:128]
        Image.fromarray(preview*17).resize((640,480),Image.Resampling.NEAREST).save(out/f'loading_layout_{n}.png')
    return replace_entry(arc,0x10008,bytes(newtex)),newmenu,bytes(ne),{'labels':{'5':'SHIBUKI','6':'RIKO'},'tiles':allocated,'parts_slack':slack,'protected_ui_frames':checked,'exe_data_proposal':edits,'exe_approval_required':True,'loading_name_right_edge':64,'loading_phrase_x':64,'transparent_logo_record_removed':True}

def make_head(path,character,words,source_words=None):
    im=Image.open(path).convert('RGBA');i=0 if character=='shibuki' else 1
    im=im.crop((i*im.width//2,0,(i+1)*im.width//2,im.height));a=np.array(im);mask=a[:,:,3]>160
    im=im.crop(bbox(mask));im=im.resize((18,20),Image.Resampling.NEAREST);a=np.array(im)
    colors=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in (source_words or words)[1:]],np.int32)
    diff=((a[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors)**2).sum(3)
    result=np.where(a[:,:,3]>=160,diff.argmin(2)+1,0).astype(np.uint8)
    if source_words:
        # Preserve hair/skin categories when reducing Riko to the existing
        # pickup palette. Euclidean RGB alone turns pale green hair into skin.
        remap=np.array([0,11,2,10,2,3,1,9,1,13,1,12,9,12,8,8],np.uint8)
        result=remap[result]
    return result

def pickups(arc,character,out,label):
    texture=entry(arc,0x10206);c=entry(arc,3);pal=entry(arc,9);face_clut=1 if character=='riko' else 0
    words=struct.unpack_from('<16H',pal,(11+face_clut)*32)
    head=make_head(D/'life_icons_generated.png',character,words,struct.unpack_from('<16H',pal,0) if face_clut else None);save_image(head.tobytes(),(18,20),words,out/f'{character}_head.png')
    cps={};targets={};reports=[]
    for n in range(89,99):
        cp=composition_frame(c,3,n);parts=[p for p in cp['parts'] if p['page']*256+p['tile'] not in (513,514,515)]
        if not parts:continue # Final blank bubble contains no old face.
        cp=local_composition({**cp,'parts':parts});px,size,bb,cov=compose_static(texture,cp)
        width,height=(18,20) if n in (89,96,97,98) else (14,14) if n<=92 else (10,10) if n==93 else (6,6)
        small=np.array(Image.fromarray(head).resize((width,height),Image.Resampling.NEAREST))
        a=np.zeros((size[1],size[0]),np.uint8);x=max(0,min(size[0]-width,-width//2-bb[0]));y=max(0,min(size[1]-height,-height//2-bb[1]))
        a[y:y+height,x:x+width]=small;mask=np.array([bool(v) for v in cov]).reshape(size[1],size[0]);a[~mask]=0
        cps[n]=cp;targets[n]=(a.tobytes(),size)
        reports.append({'frame':n,'size':size,'body_pixels':int(np.count_nonzero(a))})
    newtex=patch_static(texture,cps,targets);changed_tiles={t for t in range(len(texture)//128) if tile_pixels(texture,t)!=tile_pixels(newtex,t)}
    allowed={p['page']*256+p['tile'] for cp in cps.values() for p in cp['parts']}
    if not changed_tiles<=allowed:raise ValueError('Pickup patch escaped face tiles')
    checked=0
    for bi in range(len(bank_offsets(c))):
        count=composition_frame(c,bi,0)['bank_frame_count']
        for n in range(count):
            if bi==3 and n in cps:continue
            cp=composition_frame(c,bi,n);used={p['page']*256+p['tile'] for p in cp['parts']}
            if used&changed_tiles:raise ValueError(f'Shared pickup tile used outside scope: {bi}/{n}')
            checked+=1
    nc=bytearray(c)
    if face_clut:
        for cp in cps.values():
            for p in cp['parts']:nc[p['record_offset']]=(p['flags']&~12)|(face_clut<<2)
        for bi in range(len(bank_offsets(c))):
            for n in range(composition_frame(c,bi,0)['bank_frame_count']):
                if bi==3 and n in cps:continue
                if records(c,bi,n)!=records(nc,bi,n):raise ValueError('Pickup CLUT edit aliases another frame')
    for n in range(89,99):
        cp=local_composition(composition_frame(nc,3,n));px,size,bb,_=compose_static(newtex,cp)
        save_image(px,size,words,out/f'{label}_pickup_{n}.png')
    return replace_entry(replace_entry(arc,0x10206,newtex),3,bytes(nc)),{'faces':reports,'changed_tiles':sorted(changed_tiles),'protected_compositions':checked,'palette_geometry_timing_preserved':True,'face_clut_offset':face_clut}

def ladder(arc,out):
    g,c,pal=[entry(arc,k) for k in (2,3,9)];bank=graphics_bank(g,0,allow_bank_aliases=True);f=bank['frames'][183]
    refs=[q['index'] for q in bank['frames'] if q['offset']==f['offset']]
    if refs!=[183]:raise ValueError('Unexpected ladder sharing')
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    b=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,0,183)))
    reg=np.array(Image.open(ROOT/'work/ver_buki_riko/shibuki_art/ultimate_v1/production_layers03/master_183.png'))
    yy,xx=np.indices(b.shape);neck,hip,cx,ht=86,98,81,75
    # Crouched rear head is above the tail. The old connected-component rule
    # mistook the larger tail for the head and placed the neck at y109.
    haircore=(b>0)&np.isin(b,[5,8,14]);hair=haircore|(binary_dilation(haircore)&np.isin(b,[2,15]))
    head=(xx>=74)&(xx<=87)&(yy<neck)
    hands=np.isin(b,[12,13])&((xx<70)|(xx>92))&(yy<98)
    garment=(b>0)&~hair&~head&~hands
    coords=np.argwhere((reg>0)&~np.isin(reg,[5,8,14]));target=np.zeros_like(b)
    for y,x in np.argwhere(garment):
        cost=(coords[:,0]-y)**2*3+(coords[:,1]-x)**2;sy,sx=coords[cost.argmin()];target[y,x]=reg[sy,sx]
    edge=(b>0)&~(np.roll(b>0,1,0)&np.roll(b>0,-1,0)&np.roll(b>0,1,1)&np.roll(b>0,-1,1))
    target[garment&edge&np.isin(b,[1,2,15])]=2
    ornament=np.isin(b,[4,10,11])&(yy<neck-2)&(yy>=ht+4)&(xx>cx+3);target[ornament]=4
    keep={q['tile'] for bi in (0,6,7,8) for q in composition_frame(c,bi,183)['parts']};pool=set(range(f['tile_count']))-keep
    count=len(composition_frame(c,5,183)['parts']);nr,assignment=identical(raw,f['tile_count'],target,pool,count)
    assignment+=assignment[-1:]*(count-len(assignment));rr=b''.join(struct.pack('<BBbb',0,t,x-80,y-80) for t,x,y in assignment)
    nc,parts_slack=repack_parts(c,5,{183:rr});code=encode_stream(nr)
    if len(code)<=f['limit']-f['offset']:ng,report=replace_stream(g,f,nr)
    else:ng,report=repack_graphics_bank(g,0,{183:code})
    nb=graphics_bank(ng,0,allow_bank_aliases=True);checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        old=graphics_bank(g,bi,allow_bank_aliases=True);new=graphics_bank(ng,bi,allow_bank_aliases=True)
        for a,z in zip(old['frames'],new['frames']):
            before=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;after=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
            if after!=(nr if bi==0 and a['index']==183 else before):raise ValueError('Unrelated compressed sprite changed')
            checked+=1
    for bi in (0,5,6,7,8):
        got=canvas_from_parts(nr,f['tile_count'],local_composition(composition_frame(nc,bi,183)))
        expected=target if bi==5 else canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,bi,183)))
        if not np.array_equal(got,expected):raise ValueError('Ladder target/base differs')
    result=replace_entry(replace_entry(arc,2,ng),3,nc)
    words=struct.unpack_from('<16H',pal,32);save_image(target.tobytes(),(160,160),words,out/'ultimate_ladder_183_overlay.png')
    im=Image.open(D/'inventory/PL02_U.ARC_183_0.png').convert('RGBA');im.alpha_composite(Image.open(out/'ultimate_ladder_183_overlay.png').convert('RGBA'));im.save(out/'ultimate_ladder_183_full.png')
    return result,{'frame':183,'old_neck_y':109,'new_neck_y':86,'old_overlay_pixels':66,'new_overlay_pixels':int(np.count_nonzero(target)),'decoded_references_checked':checked,'parts_slack':parts_slack,'compression':report,'base_palette_timing_preserved':True}

def main(out):
    out=out.resolve()
    if not out.is_relative_to(D) or out.exists():raise ValueError('Fresh isolated output required')
    records_,files=load();out.mkdir();before=dict(files);reports={}
    files['LOAD_U.ARC'],files['MOJIPAT.ARC'],files['SLUS_005.61'],reports['loading']=loading(files,out)
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        files[name],reports[name]=pickups(files[name],'riko' if name=='PL01_U.ARC' else 'shibuki',out,name)
    files['PL02_U.ARC'],reports['ladder']=ladder(files['PL02_U.ARC'],out)
    changes={}
    for name,b in files.items():
        if b==before[name]:continue
        if len(b)!=len(before[name]):raise ValueError('Resource length changed')
        (out/name).write_bytes(b);changes[name]={'before':sha256(before[name]),'after':sha256(b)}
    recipe={'kind':'loading_life_ladder_fix','parent':str(PARENT.relative_to(ROOT)),'parent_sha256':PARENT_HASH,'source_sha256':SOURCE_HASH,'records':{n:records_[n] for n in changes},'files':changes,'checks':reports,'generated_icons_sha256':sha256((D/'life_icons_generated.png').read_bytes()),'prompt_sha256':sha256((D/'life_icons_prompt.txt').read_bytes()),'runtime_verified':False}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2));print(json.dumps({'output':str(out),'changes':list(changes),'checks':reports}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
