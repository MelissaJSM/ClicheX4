"""등장/승리/귀환 의상을 원래 몸·총구·발 기준에 등록한다."""
import argparse,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,distance_transform_edt
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_ceremony_reference import PARENT,PARENT_SHA,FRAMES,ORDER,PRESERVED
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_sprite_batch import canvas_from_parts

SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/ceremony_v1/generated_first.png'
SOURCE_SHA='4573fcf12f6b7ef08c22d2fe583db171ff72442f6716100355878d21989f77b0'
HIPS={138:84,156:87,204:85,205:85,206:85,207:84}
CONTACTS={138:[(65,45,80,57),(69,57,78,60)],156:[(72,72,77,80)],204:[(66,75,71,80)],205:[(72,62,78,67)],206:[(65,68,72,77)],207:[(58,40,74,54),(58,54,72,59)]}
ARM_BOXES={138:[(65,63)],156:[(67,70),(80,74)],204:[(64,70),(78,72)],205:[(65,62),(79,73)],206:[(63,66),(79,73)],207:[(61,57),(78,71)]}

def shift(v,dy):
    out=np.zeros_like(v)
    if dy<0:out[:dy]=v[-dy:]
    elif dy>0:out[dy:]=v[:-dy]
    else:out[:]=v
    return out

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor art directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Source changed')
    arc=(PARENT/'modified.arc').read_bytes();c=entry(arc,3);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    src=Image.open(SOURCE).convert('RGBA');lo,hi=src.getchannel('A').getextrema();require(lo==0 and hi>=250,'Transparent source required');out.mkdir(parents=True)
    yy,xx=np.indices((160,160));targets={};layers={};records=[]
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];by,bx=np.nonzero(base);bb=[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)];hip=HIPS[n]
        a=np.array(src.crop((i%3*src.width//3,i//3*src.height//2,(i%3+1)*src.width//3,(i//3+1)*src.height//2)))
        lab,count=label(a[:,:,3]>=192);sizes=np.bincount(lab.flat);sizes[0]=0;keep=lab==sizes.argmax();sy,sx=np.nonzero(keep);box=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)];a[~keep,3]=0;crop=Image.fromarray(a).crop(box)
        v=normalize(crop,bb[3]-bb[1],rgb);ey,ex=np.nonzero(base==14);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<v.shape[0]//2))
        if not len(vx):
            col=np.array(crop).astype(np.int32);r,g,b=col[:,:,:3].transpose(2,0,1);eye=(g>r+10)&(g>b+10)&(g>60)&(col[:,:,3]>=192);eye[crop.height//2:]=False
            gy,gx=np.nonzero(eye);vx=gx*v.shape[1]/crop.width;vy=gy*v.shape[0]/crop.height
        require(len(vx)>0,'Generated eye missing');dx=round(float(ex.mean()-vx.mean()));dy=round(float(ey.mean()-vy.mean()));cx,cy=round(float(ex.mean())),round(float(ey.mean()))
        face=[int(ex.min())-2,int(ey.min())-2,int(ex.max())+7,int(ey.max())+7]
        target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        lower=hip+4
        for y in range(lower,bb[3]):
            target[y]=0
            for left,right in intervals(base[y]>0):
                target[y,left:right+1]=1
                if right-left>=2:
                    target[y,left+1:right]=5 if y>=bb[3]-3 else 12
                    if right-left>=4 and y<bb[3]-3:target[y,right-1]=11
                elif right>left:target[y,left]=5 if y>=bb[3]-3 else 12
        target[:bb[1]]=0;target[bb[3]:]=0;target[(target==14)&(base!=14)]=2
        # Preserve the accepted face and the exact native pistol/hand contacts.
        for x,y,x2,y2 in [face]+CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        dist,idx=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        require(float(dist[missing].max(initial=0))<=6,f'Costume too far from native body: {n}')
        target[missing]=target[tuple(idx[:,missing])]
        for x,y,x2,y2 in [face]+CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        # Frame205 has only three leg quads. Retain its accepted shoe/toe
        # pixels so the white hem and rear veil stay in the leg-owned layer.
        if n==205:target[100:]=base[100:]
        head=(xx>=cx-7)&(xx<cx+9)&(yy>=cy-8)&(yy<cy+8)
        leg=(yy>=hip)|((xx>=cx+8)&(yy>=cy+8))|((yy>=hip-2)&(target==13))
        arm=np.zeros_like(base,bool)
        for ax,ay in ARM_BOXES[n]:arm|=(xx>=ax)&(xx<ax+16)&(yy>=ay)&(yy<ay+16)
        arm&=~head
        remaining=np.where(target!=base,target,0).astype(np.uint8);layers[n]={b:np.zeros_like(base) for b in LAYERS.values()}
        for b,mask in ((5,head),(8,leg),(7,arm)):
            layers[n][b][mask]=remaining[mask];remaining[mask]=0
        layers[n][6]=remaining;targets[n]=target
        records.append({'frame':n,'source_cell':i,'source_box':box,'native_size':list(v.shape[::-1]),'placement':[dx,dy],'face_box':face,'contacts':CONTACTS[n],'hip':hip,'lower_y':lower,'boundary_pixels':int(missing.sum()),'max_boundary_distance':float(dist[missing].max(initial=0))})
    for n,source in ((139,138),(157,156)):
        layers[n]={b:shift(v,-1) for b,v in layers[source].items()};targets[n]=render(arc,n)[1].copy()
        for b in (8,5,7,6):targets[n]=np.where(layers[n][b],layers[n][b],targets[n])
        records.append({'frame':n,'shared_costume':source,'translation':[0,-1]})
    _,base0,f,raw=render(arc,0)
    idle={b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,0)) for b in LAYERS.values()}
    for n in (141,142):
        layers[n]={b:v.copy() for b,v in idle.items()};targets[n]=render(arc,n)[1].copy()
        for b in (8,5,7,6):targets[n]=np.where(layers[n][b],layers[n][b],targets[n])
        records.append({'frame':n,'shared_costume':0,'exact_accepted_idle_layers':True})
    board=Image.new('RGB',(4*256,3*280),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+FRAMES):
        if n==0:im=render(arc,n,True)[0]
        else:
            merged=render(arc,n)[1].copy()
            for b in (8,5,7,6):merged=np.where(layers[n][b],layers[n][b],merged)
            require(np.array_equal(merged,targets[n]),'Layer split cannot cover base')
            for name,b in LAYERS.items():save_image(layers[n][b].tobytes(),(160,160),words,out/f'{name}_{n:03}.png')
            im=save_image(targets[n].tobytes(),(160,160),words,out/f'full_{n:03}.png').convert('RGBA')
        tile=im.crop((48,40,112,104)).resize((256,256),Image.Resampling.NEAREST);board.paste(tile,(i%4*256,i//4*280+24),tile);draw.text((i%4*256+4,i//4*280+4),str(n),fill='white')
    board.save(out/'family_4x.png')
    write(out/'layers.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'preserved_common_frames':PRESERVED,'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':records,'native_body_unchanged':True,'runtime_verified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'frames':len(FRAMES),'registration':records})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
