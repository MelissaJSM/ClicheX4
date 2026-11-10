"""수용한 나나 마스터에서 대기/정지 사격을 만들고 원래 스트림에 재삽입한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_idle import breathe
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import edit_frame_indices
from src.psx_compress import replace_stream,encode_stream

PARENT=ROOT/'out/ver_rin_nana/rin_common_20261029T051459667484Z'
PARENT_SHA='5434083adbcbb4dd651a4b6e83228dd6cbc2ca6a03291d882db13ba58de55571'
PILOT=ROOT/'out/ver_rin_nana/nana_pilot_v9'
ART=ROOT/'work/ver_rin_nana/nana_art/idle_shot_v1'
INV=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'
IDS=(0,85,86,87,92,115,116,117,118,119)

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def world(a,bounds):
    r=np.zeros((80,96),np.uint8);x,y=48+bounds[0],40+bounds[1];r[y:y+a.shape[0],x:x+a.shape[1]]=a;return r
def shifted(a,dx,dy):
    r=np.zeros_like(a);ys,xs=np.nonzero(a);xx,yy=xs+dx,ys+dy
    if np.any(xx<0)|np.any(xx>=a.shape[1])|np.any(yy<0)|np.any(yy>=a.shape[0]):raise ValueError('Shift would clip art')
    r[yy,xx]=a[ys,xs];return r
def generated_section(im,i,words,width=None):
    pic=im.crop((i*im.width//2,0,(i+1)*im.width//2,im.height));a=np.array(pic);ys,xs=np.nonzero(a[:,:,3]>=128)
    crop=pic.crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))
    width=width or round(crop.width*45/crop.height)
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    a=np.array(crop);labels=np.zeros(a.shape[:2],np.uint8)
    for y in range(len(a)):
        diff=a[y,:,:3].astype(np.int32)[:,None,:]-colors[None,1:,:]
        labels[y]=1+(diff*diff).sum(2).argmin(1)
    votes=[np.array(Image.fromarray(np.where(labels==i,a[:,:,3],0).astype(np.uint8)).resize((width,45),Image.Resampling.BOX)) for i in range(1,16)]
    v=(1+np.stack(votes).argmax(0)).astype(np.uint8)
    v[np.array(crop.getchannel('A').resize((width,45),Image.Resampling.BOX))<128]=0
    feet=np.nonzero(v[-3:])[1];x=round(47-(int(feet.min())+int(feet.max()))/2)
    r=np.zeros((80,96),np.uint8);r[18:63,x:x+width]=v;return r

def prepare(out):
    out=out.resolve()
    if not out.is_relative_to(ROOT/'work/ver_rin_nana/nana_production') or out.exists():raise ValueError('Fresh isolated production output required')
    project=json.loads((ROOT/'projects/ver_rin_nana/project.json').read_text('utf8'));approval=project['nana_style_approval']
    if not project['nana_pilot']['art_approved'] or digest(PILOT/'nana_000_indexed.png')!=approval['master_sha256'] or digest(PILOT/'palette.bin')!=approval['palette_sha256']:raise ValueError('Approved master differs')
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent build differs')
    arc=(PARENT/'common/PL00_U.ARC').read_bytes();es=psx_arc(arc)
    def entry(t):
        e=next(e for e in es if int(e['type'],16)==t);return e,arc[e['offset']:e['offset']+e['size']]
    gm,gfx=entry(2);cm,parts=entry(3);pm,palette=entry(9)
    inv=json.loads(INV.read_text('utf8'));words=struct.unpack('<16H',(PILOT/'palette.bin').read_bytes())
    master=np.array(Image.open(PILOT/'nana_000_indexed.png'));base=world(master,(-19,-25))
    source=Image.open(ART/'generated.png').convert('RGBA');closed_source=generated_section(source,0,words,26)
    # Only the original visible eye pixel is writable, never the adjacent fringe.
    eye=(13,15);eye_world=(28,44)
    options=[(y,x,int(closed_source[y,x])) for y in range(28,31) for x in range(44,47) if closed_source[y,x] in (1,2)]
    if not options:raise ValueError('Generated eyelid has no usable dark pixel')
    pick=min(options,key=lambda q:abs(q[0]-eye_world[0])+abs(q[1]-eye_world[1]))
    blink=master.copy();blink[eye]=pick[2]
    if master[eye]!=14 or np.count_nonzero(blink!=master)!=1:raise ValueError('Blink escaped the eye')
    frames={0:base,115:world(breathe(master,1),(-19,-25)),119:world(breathe(master,-1),(-19,-25))}
    for n in (116,117,118):frames[n]=world(breathe(blink,1),(-19,-25))
    shot=shifted(world(np.array(Image.open(PILOT/'nana_085_indexed.png')),(-27,-25)),1,0)
    recovery=generated_section(source,1,words)
    # Lock face/hair above shoulder, chest center, skirt center and every leg/sole pixel.
    yy,xx=np.indices(base.shape);wx,wy=xx-48,yy-40
    left=(wx<-6)&(wy>=-14)&(wy<7)
    right=(wx>=4)&(wy>=-7)&(wy<7)
    arms=left|right
    fire=base.copy();fire[arms]=shot[arms]
    recoil=base.copy();moved=shifted(shot,1,0);recoil[arms]=moved[arms]
    returning=base.copy();returning[left]=recovery[left];returning[right]=shot[right]
    frames.update({85:fire,86:recoil,87:returning,92:base.copy()})
    for n in (85,86,87,92):
        if np.any(frames[n][~arms]!=base[~arms]):raise ValueError('Protected common body changed')
    if not np.array_equal(frames[0],base):raise ValueError('Approved idle changed')
    out.mkdir(parents=True)
    for n,a in frames.items():save_image(a.tobytes(),(96,80),words,out/f'frame_{n:03d}.png')
    save_image(closed_source.tobytes(),(96,80),words,out/'generated_blink_registered.png')
    save_image(recovery.tobytes(),(96,80),words,out/'generated_recovery_registered.png')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    board=Image.new('RGB',(5*230,2*270),'#222630');draw=ImageDraw.Draw(board)
    for i,n in enumerate((0,115,116,117,119,85,86,87,92,118)):
        x,y=i%5*230,i//5*270;draw.text((x+6,y+6),f'Nana {n:03d}',font=font,fill='white')
        pic=Image.open(out/f'frame_{n:03d}.png').convert('RGBA').crop((19,12,76,66)).resize((228,216),Image.Resampling.NEAREST);board.paste(pic,(x,y+30),pic)
    board.save(out/'family_4x.png')
    for name,sequence,durations in [('idle',[q['frame'] for q in inv['idle_animation']['steps']],[q['duration_ticks'] for q in inv['idle_animation']['steps']]),('standing',[0,85,86,85,87,92,0],[30,2,4,6,4,8,30])]:
        pics=[]
        for n in sequence:
            im=Image.new('RGB',(288,240),'#222630');pic=Image.open(out/f'frame_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);im.paste(pic,(0,0),pic);pics.append(im)
        pics[0].save(out/f'{name}_preview.gif',save_all=True,append_images=pics[1:],duration=[round(t*1000/60) for t in durations],loop=0)
    nparts=bytearray(parts)
    for n in (115,116,117,118):
        for q in composition_frame(parts,0,n)['parts']:
            if q['tile']==2:struct.pack_into('<bb',nparts,q['record_offset']+2,-19,-25)
            elif q['tile']==5:struct.pack_into('<bb',nparts,q['record_offset']+2,-3,-25)
    changed_records={q['record_offset']+j for n in (115,116,117,118) for q in composition_frame(parts,0,n)['parts'] if q['tile'] in (2,5) for j in (2,3)}
    for q in composition_frame(parts,0,87)['parts']:
        if q['tile']==0:
            struct.pack_into('<b',nparts,q['record_offset']+3,-9);changed_records.add(q['record_offset']+3)
    diffs=[i for i,(a,b) in enumerate(zip(parts,nparts)) if a!=b]
    if not set(diffs)<=changed_records:raise ValueError('Unexpected composition write')
    for bi,off in enumerate(bank_offsets(parts)):
        for n in range(struct.unpack_from('<I',parts,off)[0]>>16):
            if bi==0 and n in (87,115,116,117,118):continue
            if composition_frame(parts,bi,n)!=composition_frame(nparts,bi,n):raise ValueError('Shared composition changed')
    bank=graphics_bank(gfx,0,allow_bank_aliases=True);newgfx=gfx;reports=[]
    def target(n,packed):
        f=bank['frames'][n];comp=composition_frame(nparts,0,n);_,size,bb,_=compose_indices(packed,f['tile_count'],comp)
        x,y=48+bb[0],40+bb[1];desired=frames[n][y:y+size[1],x:x+size[0]]
        if np.count_nonzero(desired)!=np.count_nonzero(frames[n]):raise ValueError(f'Frame {n} outside canvas')
        return desired.tobytes(),size,comp
    for n,refs in ((0,[0]),(85,[85]),(86,[86]),(87,[87]),(92,[92]),(115,[115,116,117,118]),(119,[119])):
        f=bank['frames'][n]
        if inv['stream_sharing'][str(f['offset'])]!=[[0,k] for k in refs]:raise ValueError('Unexpected shared stream')
        raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        pixels,size,comp=target(n,raw);packed=edit_frame_indices(raw,f['tile_count'],comp,pixels,size)
        writable={q['tile'] for k in refs for q in composition_frame(nparts,0,k)['parts']}
        armor={q['tile'] for bi in range(5,9) for k in refs for q in composition_frame(parts,bi,k)['parts']}
        if writable&armor:raise ValueError('Base/armor tile collision')
        if n==115:
            _,mapping,_=indexed_atlas(packed,f['tile_count']);work=bytearray(packed)
            for k in refs[1:]:
                c=composition_frame(nparts,0,k);overlay=next(q for q in c['parts'] if q['tile'] in (6,7,8));t=overlay['tile']
                for y in range(16):
                    for x in range(16):
                        off,sh=mapping[((t>>4)*16+y)*256+(t&15)*16+x];work[off]&=~(15<<sh)
                for y,x in np.argwhere(frames[k]!=frames[115]):
                    ox,oy=int(x)-48-overlay['x'],int(y)-40-overlay['y'];value=int(frames[k][y,x])
                    if not (0<=ox<16 and 0<=oy<16) or not value:raise ValueError('Eye exceeds native overlay')
                    off,sh=mapping[((t>>4)*16+oy)*256+(t&15)*16+ox];work[off]=(work[off]&~(15<<sh))|(value<<sh)
            packed=bytes(work)
        oldatlas=indexed_atlas(raw,f['tile_count'])[0];newatlas=indexed_atlas(packed,f['tile_count'])[0]
        for t in range(f['tile_count']):
            for y in range(16):
                start=((t>>4)*16+y)*256+(t&15)*16
                if t not in writable and oldatlas[start:start+16]!=newatlas[start:start+16]:raise ValueError('Nonbase tile changed')
        for k in refs:
            pix,sz,c=target(k,packed)
            if compose_indices(packed,f['tile_count'],c)[:2]!=(pix,sz):raise ValueError('Frame raster mismatch')
            for q in c['parts']:
                t=q['tile']
                if t%16==0 and any(newatlas[((t>>4)*16+y)*256] for y in range(16)):raise ValueError('GPU U=0 mirror clipping')
        encoded=encode_stream(packed)
        print(json.dumps({'frames':refs,'bytes':len(encoded),'capacity':f['limit']-f['offset']}),flush=True)
        newgfx,rep=replace_stream(newgfx,f,packed);reports.append({'frames':refs,**rep})
    changed=[];checked=0
    for bi in range(len(bank_offsets(gfx,allow_aliases=True))):
        for f in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
            a=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;b=decode_stream(newgfx,f['offset'],f['limit'],f['tile_count']*128).data;checked+=1
            if a!=b:changed.append([bi,f['index']])
    if changed!=[[0,n] for n in IDS]:raise ValueError('Unexpected changed references')
    patched=bytearray(arc);patched[gm['offset']:gm['offset']+gm['size']]=newgfx;patched[cm['offset']:cm['offset']+cm['size']]=nparts;patched[pm['offset']:pm['offset']+32]=(PILOT/'palette.bin').read_bytes()
    allowed=[(gm['offset']+r['start'],gm['offset']+r['start']+r['encoded_bytes']) for r in reports]+[(cm['offset']+i,cm['offset']+i+1) for i in diffs]+[(pm['offset'],pm['offset']+32)]
    if len(patched)!=len(arc) or any(a!=b and not any(lo<=i<hi for lo,hi in allowed) for i,(a,b) in enumerate(zip(arc,patched))):raise ValueError('ARC change escaped declared ranges')
    (out/'modified.arc').write_bytes(patched);(out/'palette.bin').write_bytes((PILOT/'palette.bin').read_bytes())
    recipe={'task':'x_nana','scope':'idle_and_standing_10','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,
        'parent_archive_sha256':sha256(arc),'modified_archive_sha256':sha256(patched),'frames':list(IDS),'compression':reports,
        'changed_composition_bytes':diffs,'changed_bitmap_references':changed,'checked_bitmap_references':checked,
        'armor_tiles_preserved':True,'animation_and_other_entries_preserved':True,'resources_relocated':False,
        'master_sha256':approval['master_sha256'],'palette_sha256':approval['palette_sha256'],
        'idle_master_exact':True,'standing_outside_arm_mask_exact':True,'eye_changed_pixels':1,'eyelid_source_pixel':pick,
        'breathing_coherent_through_thigh':True,'breathing_transition_rows':[35,43],'soles_preserved':True,
        'frame_sha256':{str(n):digest(out/f'frame_{n:03d}.png') for n in IDS},'generated_source_sha256':digest(ART/'generated.png'),
        'original_idle_animation':inv['idle_animation'],'original_standing_animation':inv['animations'][88],
        'preview_timing_note':'60Hz assumption; standing preview adds waiting time and does not interpret native 96 control as duration',
        'game_applied':False,'runtime_verified':False,'known_limit':'미제작 X 동작도 공유 팔레트0행의 나나 색으로 표시됨. 나나 아머 미제작.'}
    write(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'sha256':sha256(patched),'checked':checked}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
