"""나나 HUD 심볼과 분홍 메뉴. X 기본/얼티밋의 공통 UI만 변경한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_hud_emblems import all_compositions,composed,inner_slice,render_pixels,TARGETS,RECT,require
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_ui_revision import pause_background
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from src.psx_ui_atlas import aliased_composition,tile_pixels,write_tile

PARENT=ROOT/'out/ver_rin_nana/nana_weapon_get_20261030T042743148999Z'
PARENT_SHA='63640d64c8cf0b15e20890bcd330c58a6d18e7ea37ac0b2df48d1442f84f822e'
ART=ROOT/'work/ver_rin_nana/nana_hud_theme_v1'
SLOTS={0:[15],1:list(range(8,15)),2:list(range(6,15)),3:list(range(11,16)),4:list(range(8,16)),5:list(range(8,16)),11:list(range(1,16))}
STATIC_BANKS={1,2,3,4,*range(9,22)}

def sources():
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted parent differs')
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));raw={};records={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size)
        iso={q['path']:q for q in d.inspect()['files']}
        for name,file in(('PL00_U.ARC','modified.arc'),('PL02_U.ARC','PL02_U.ARC')):
            q=iso['/ARC/'+name+';1'];a=d.read(q['lba'],q['size']);require(a==(PARENT/file).read_bytes(),'Parent player readback differs');raw[name]=a;records[name]={**q,'sha256':sha256(a)}
        q=iso['/ARC/COL00_0X.ARC;1'];pal=entry(d.read(q['lba'],q['size']),5)[17*32:18*32]
    require(sha256(raw['PL00_U.ARC'])==m['modified_archive_sha256'],'Parent player differs')
    return m,records,raw,pal

def menu_palette(data):
    out=bytearray(data);changes=[]
    for row,indices in SLOTS.items():
        for i in indices:
            pos=row*32+2*i;w=struct.unpack_from('<H',data,pos)[0]
            r,g,b=(w>>s&31 for s in (0,5,10));lo,hi=min(r,g,b),max(r,g,b)
            rgb=(hi,round(lo+(hi-lo)*.20),round(lo+(hi-lo)*.62))
            nw=(w&0x8000)|sum(v<<(j*5) for j,v in enumerate(rgb))
            struct.pack_into('<H',out,pos,nw)
            if nw!=w:changes.append({'row':row,'index':i,'before':w,'after':nw})
    require(bytes(out[320:352])==data[320:352],'Portrait CLUT changed')
    require(all((a==0)==(b==0) and (a&0x8000)==(b&0x8000) for a,b in zip(struct.unpack('<1024H',data),struct.unpack('<1024H',out))),'Palette transparency/STP changed')
    return bytes(out),changes

def make_overlay(raw,palette):
    native,_,bounds,_=composed(entry(raw,0x10206),aliased_composition(entry(raw,3),1,69))
    desired=native.copy();cfg=json.loads((ROOT/'config/riko_hud_mark_us.json').read_text('utf8'))
    for y,x1,x2 in cfg['background_rows']:desired[y,x1:x2+1]=14
    ys,xs=inner_slice(bounds);region=desired[ys,xs];base=native[ys,xs]
    # Remove the remaining colored original letter while retaining neutral chrome.
    region[(base>=1)&(base<=9)|(base==15)]=14
    im=Image.open(ART/'generated.png').convert('RGBA')
    alpha=im.getchannel('A');box=alpha.point(lambda a:255 if a>=128 else 0).getbbox()
    require(box is not None,'Empty generated symbol')
    im=im.crop(box);scale=min(15/im.width,13/im.height)
    size=(round(im.width*scale),round(im.height*scale));small=im.resize(size,Image.Resampling.LANCZOS)
    a=np.array(small);indices=np.array([10,11,12,13,14],np.uint8)
    words=struct.unpack('<16H',palette)
    colors=np.array([[((words[int(i)]>>s)&31)*255//31 for s in (0,5,10)] for i in indices],np.int32)
    dist=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
    px=indices[dist.argmin(2)];mask=a[:,:,3]>=100
    x=(23-size[0])//2;y=(13-size[1])//2
    require(not np.any(mask&(base[y:y+size[1],x:x+size[0]]==0)),'Symbol clips native HUD alpha')
    region[y:y+size[1],x:x+size[0]][mask]=px[mask]
    require(np.array_equal(native>0,desired>0),'Art changed original HUD alpha')
    outside=np.ones(native.shape,bool);outside[ys,xs]=False
    require(np.array_equal(native[outside],desired[outside]),'Art changed outside emblem')
    return region.copy(),{'size':list(size),'offset_in_23x13':[x,y],'crop':list(box),'uniform_scale':scale,'symbol_opaque_pixels':int(mask.sum())}

def patch(raw,overlay):
    require(overlay.shape==(13,23) and np.issubdtype(overlay.dtype,np.integer) and 0<=overlay.min()<=overlay.max()<=15,'Invalid native overlay')
    texture,parts=entry(raw,0x10206),entry(raw,3);comps=all_compositions(parts)
    used={p['page']*256+p['tile'] for c in comps.values() for p in c['parts']}
    free=iter(sorted(set(range(len(texture)//128))-used));mapping={}
    # Every bank, including compressed bodies, participates in the reservation scan.
    for tile in (76,77,78,145):
        slot=next(free,None);require(slot is not None,'No private HUD tile capacity');mapping[tile]=slot
    ng=bytearray(texture);np_=bytearray(parts);allowed=set()
    for old,new in mapping.items():write_tile(ng,new,tile_pixels(texture,old))
    for key in TARGETS:
        for p in comps[key]['parts']:
            tile=p['page']*256+p['tile']
            if tile in mapping:
                dest=mapping[tile];off=p['record_offset']
                np_[off:off+2]=bytes(((p['flags']&~3)|dest//256,dest%256));allowed.update((off,off+1))
    newparts=bytes(np_);cloned=bytes(ng);newcomps=all_compositions(newparts);demands={};targets={};details=[]
    for key in sorted(TARGETS):
        before,size,bounds,_=composed(texture,comps[key]);same,sz,bb,sources_=composed(cloned,newcomps[key])
        require(np.array_equal(before,same) and size==sz and bounds==bb,'Tile cloning changed frame')
        ys,xs=inner_slice(bounds);require(np.array_equal(overlay>0,before[ys,xs]>0),'HUD alpha changed')
        after=before.copy();after[ys,xs]=overlay;targets[key]=after
        for y,x in zip(*np.where(after!=before)):
            locations=sources_[int(y)*size[0]+int(x)]
            visible=[(off,shift) for off,shift in locations if (cloned[off]>>shift)&15]
            require(bool(visible),'No visible native owner');off,shift=visible[-1]
            tile=off//128//16*16+(off%128)//8
            require(tile in mapping.values(),'Edit escaped private tiles')
            value=int(after[y,x]);require((off,shift) not in demands or demands[off,shift]==value,'Aliased frame pixels conflict')
            demands[off,shift]=value
        details.append({'frame':key[1],'size':list(size),'bounds':list(bounds),'changed_pixels':int(np.count_nonzero(after!=before))})
    for (off,shift),value in demands.items():ng[off]=(ng[off]&~(15<<shift))|(value<<shift)
    ng=bytes(ng);checked=0
    for key,c in comps.items():
        nc=newcomps[key]
        if key not in TARGETS:require(c==nc,'Protected part record changed')
        if key[0] in STATIC_BANKS:
            before,sz,bb,_=composed(texture,c);after,ns,nb,_=composed(ng,nc)
            require(sz==ns and bb==nb and np.array_equal(after,targets.get(key,before)),'Static display changed unexpectedly '+str(key));checked+=1
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(parts,newparts))),'Parts bytes outside tile references changed')
    for tile in range(len(texture)//128):
        if tile not in mapping.values():require(tile_pixels(texture,tile)==tile_pixels(ng,tile),'Unowned texture tile changed')
    pal,colors=menu_palette(entry(raw,0x11));result=replace_entry(replace_entry(replace_entry(raw,0x10206,ng),3,newparts),0x11,pal)
    layout=lambda a:[{k:v for k,v in e.items() if k!='sha256'} for e in psx_arc(a)]
    require(len(result)==len(raw) and layout(raw)==layout(result),'Archive layout changed')
    spans=[(e['offset'],e['offset']+e['size']) for e in psx_arc(raw) if int(e['type'],16) in (3,0x10206,0x11)]
    permitted=bytearray(len(raw))
    for lo,hi in spans:permitted[lo:hi]=bytes([1])*(hi-lo)
    require(all(a==b or permitted[i] for i,(a,b) in enumerate(zip(raw,result))),'Other player entry/padding changed')
    return result,{'hud_frames':details,'tile_mapping':{str(k):v for k,v in mapping.items()},'all_bank_references_scanned':len(comps),'static_compositions_checked':checked,
        'protected_static_compositions':checked-9,'all_other_parts_exact':True,'alpha_and_outside_rectangle_exact':True,
        'parts_geometry_order_clut_flip_timing_preserved':True,'only_private_hud_tiles_changed':True,
        'menu_color_changes':colors,'portrait_palette_row10_exact':True,'palette_transparency_stp_preserved':True,
        'arc_offsets_lengths_and_unowned_bytes_exact':True,'runtime_verified':False}

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ART) and out!=ART and not out.exists(),'New art subdirectory required')
    m,records,original,pal=sources();old=original['PL00_U.ARC'];overlay,art=make_overlay(old,pal);modified={};checks={}
    for n,raw in original.items():modified[n],checks[n]=patch(raw,overlay)
    new=modified['PL00_U.ARC'];out.mkdir();Image.fromarray(overlay).save(out/'overlay.png')
    for n,data in modified.items():(out/n).write_bytes(data)
    (out/'native_hud_palette.bin').write_bytes(pal)
    board=Image.new('RGB',(768,460),'#243347');draw=ImageDraw.Draw(board)
    for i,n in enumerate((69,77)):
        for j,(label,raw) in enumerate((('before',old),('after',new))):
            a,sz,bb,_=composed(entry(raw,0x10206),aliased_composition(entry(raw,3),1,n));im=render_pixels(a,pal);im.save(out/f'hud_{n}_{label}.png')
            im=im.resize((sz[0]*4,sz[1]*4),Image.Resampling.NEAREST);x=(i*2+j)*192
            draw.text((x+4,4),f'{n} {label}',fill='white');board.paste(im,(x,30),im)
    board.save(out/'hud_comparison.png');pause_background(new).resize((640,480),Image.Resampling.NEAREST).save(out/'menu_background.png')
    r={'kind':'nana_hud_theme','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'files':[{'file':n,'source':records[n],'sha256':sha256(modified[n])}for n in sorted(modified)],
        'overlay_sha256':digest(out/'overlay.png'),'tool':'built-in image_gen','art':art,'world_rect':list(RECT),
        'inputs':{f:digest(ART/f) for f in ('generated.png','prompt.txt','refine_prompt.txt')},'reference_sha256':digest(ROOT/'character/ver_rin_nana/nana(X)_mark.webp'),
        'palette_sha256':sha256(pal),'verification':checks}
    (out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'checks':{n:{'mapping':v['tile_mapping'],'checked':v['static_compositions_checked'],'menu_colors':len(v['menu_color_changes'])}for n,v in checks.items()}}))

def inventory():
    m,records,raw,pal=sources();ART.mkdir(parents=True,exist_ok=True);words=struct.unpack('<16H',pal)
    a,sz,bb,_=composed(entry(raw['PL00_U.ARC'],0x10206),aliased_composition(entry(raw['PL00_U.ARC'],3),1,69));render_pixels(a,pal).resize((sz[0]*6,sz[1]*6),Image.Resampling.NEAREST).save(ART/'original_hud_6x.png')
    (ART/'sources.json').write_text(json.dumps({'records':records,'hud_palette_sha256':sha256(pal),'hud_bounds':bb,'hud_palette_rgb':[[int(w>>s&31)*255//31 for s in(0,5,10)]for w in words]},indent=2)+'\n','utf8');print(json.dumps({'size':sz,'bounds':bb,'rgb':[[int(w>>s&31)*255//31 for s in(0,5,10)]for w in words]}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();inventory()if a.inventory else prepare(a.output)
