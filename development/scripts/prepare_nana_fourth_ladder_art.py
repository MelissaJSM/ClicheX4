"""같은 사다리 몸·손발 기준에 생성 의상만 등록하고 반전·사격을 공유한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,distance_transform_edt
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_ladder_reference import PARENT,PARENT_SHA,FRAMES,ORDER
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.extract_zero import save_image

SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/ladder_v1/generated.png'
SOURCE_SHA='fd94d7760e97fa596a1f75d58cf721531026800f25178dd62c35f71daf97a0f6'
MIRRORS={144:(145,159),146:(147,160),149:(148,160),151:(152,160)}
ANCHORS={143:(81,64,80),144:(80,62,82),146:(80,64,84),149:(78,63,78),151:(80,61,78),153:(80,67,76),154:(74,77,86),183:(80,83,94),155:(78,63,78)}
CONTACTS={143:[[66,54,71,60]],144:[[70,50,74,56],[83,66,89,73]],146:[[70,48,76,54],[81,67,88,74]],149:[[83,49,88,54]],151:[[69,55,75,60],[84,61,89,65]],153:[[66,84,71,87],[89,84,94,87]],154:[],183:[[68,82,73,86],[90,82,95,86]],155:[[83,49,88,54]]}
ARM_BOXES={143:[(64,55),(76,72)],144:[(68,54),(81,68)],146:[(68,52),(81,68)],149:[(81,51),(63,68)],150:[(81,51),(63,68)],155:[(81,51),(63,68)],151:[(67,54),(80,58)],153:[(64,73),(80,73)],154:[(64,80)],183:[(64,80),(80,80)]}

def mirror(v,total):
    result=np.zeros_like(v);y,x=np.nonzero(v);require(np.all((total-x>=0)&(total-x<160)),'Mirror outside canvas');result[y,total-x]=v[y,x];return result

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor art directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Source changed')
    arc=(PARENT/'modified.arc').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    src=Image.open(SOURCE).convert('RGBA');require(src.getchannel('A').getextrema()==(0,255),'Transparent source required');out.mkdir(parents=True)
    yy,xx=np.indices((160,160));targets={};all_layers={};records=[]
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];by,bx=np.nonzero(base);bb=[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)];cx,cy,hip=ANCHORS[n]
        a=np.array(src.crop((i%3*src.width//3,i//3*src.height//3,(i%3+1)*src.width//3,(i//3+1)*src.height//3)))
        lab,count=label(a[:,:,3]>=128);sizes=np.bincount(lab.flat);sizes[0]=0;keep=lab==sizes.argmax();sy,sx=np.nonzero(keep);box=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)];a[~keep,3]=0;crop=Image.fromarray(a).crop(box)
        v=normalize(crop,bb[3]-bb[1],rgb);dx=round((bb[0]+bb[2]-v.shape[1])/2);dy=bb[1];ey,ex=np.nonzero(base==14);face=None
        if len(ex):
            vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<v.shape[0]//2))
            if not len(vx):
                colors=np.array(crop).astype(np.int32);red,green,blue=colors[:,:,:3].transpose(2,0,1)
                eye=(green>red+10)&(green>blue+10)&(green>60)&(colors[:,:,3]>=128);eye[crop.height//2:]=False
                ey0,ex0=np.nonzero(eye);vx=ex0*v.shape[1]/crop.width;vy=ey0*v.shape[0]/crop.height
            require(len(vx)>0,'Generated eye missing');dx=round(float(ex.mean()-vx.mean()));dy=round(float(ey.mean()-vy.mean()));face=[int(ex.min())-2,int(ey.min())-2,int(ex.max())+7,int(ey.max())+7]
        require(min(dx,dy)>=0 and dx+v.shape[1]<=160 and dy+v.shape[0]<=160,'Canvas overflow')
        target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # The existing leg articulation, sole and rung contacts remain the geometry source.
        lower=hip+4;regions,num=label((base>0)&(yy>=lower));shoe=np.zeros_like(base,bool)
        for k in range(1,num+1):
            ly,lx=np.nonzero(regions==k)
            if len(lx):shoe|=(regions==k)&(yy>=int(ly.max())-2)
        for y in range(lower,bb[3]):
            target[y]=0
            for left,right in intervals(base[y]>0):
                target[y,left:right+1]=1
                if right-left>=2:
                    target[y,left+1:right]=12
                    if right-left>=4:target[y,right-1]=11
                    target[y,left+1:right][shoe[y,left+1:right]]=5
                elif right>left:target[y,left]=5 if np.any(shoe[y,left:right+1]) else 12
        target[bb[3]:]=0
        target[:bb[1]]=0
        if n==143:
            raised=(xx<cx-6)&(yy<cy+2)
            target[raised]=base[raised]
        # Remove generated stray green dots outside the existing eye.
        target[(target==14)&(base!=14)]=2
        if face:
            x,y,x2,y2=face;target[y:y2,x:x2]=base[y:y2,x:x2]
        for x,y,x2,y2 in CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        # All overlays must cover existing opaque pixels; transparent pixels cannot erase the base.
        dist,idx=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        require(float(dist[missing].max(initial=0))<=6,f'Costume registration differs too far: {n}')
        target[missing]=target[tuple(idx[:,missing])]
        if face:
            x,y,x2,y2=face;target[y:y2,x:x2]=base[y:y2,x:x2]
        for x,y,x2,y2 in CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        targets[n]=target
        records.append({'frame':n,'source_cell':i,'source_box':box,'native_size':list(v.shape[::-1]),'placement':[dx,dy],'head_anchor':[cx,cy],'hip':hip,'lower_y':lower,'face_box':face,'contacts':CONTACTS[n],'boundary_pixels':int(missing.sum()),'max_boundary_distance':float(dist[missing].max(initial=0))})
    # Both shooting poses use the accepted native pistol at its original muzzle.
    for n in (150,155):
        shot=render(arc,n)[1];regular=render(arc,149)[1];target=targets[149].copy();diff=shot!=regular;gy,gx=np.nonzero(diff);gun=[int(gx.min()),int(gy.min()),int(gx.max()+1),int(gy.max()+1)]
        x,y,x2,y2=gun;target[y:y2,x:x2]=shot[y:y2,x:x2];targets[n]=target
        record=next(q for q in records if q['frame']==149).copy();record.update(frame=n,shared_costume=149,gun_box=gun)
        if n==155:records=[q for q in records if q['frame']!=155]
        records.append(record)
    for n in ORDER+[150]:
        base=render(arc,n)[1];t=targets[n];q=next(q for q in records if q['frame']==n);cx,cy=q['head_anchor'];hip=q['hip']
        # One 16x16 head slot; rear veil belongs to the leg costume, as approved.
        head=(xx>=cx-7)&(xx<cx+9)&(yy>=cy-8)&(yy<cy+8)
        leg=(yy>=hip)|((xx>=cx+8)&(yy>=cy+8))
        arm=np.zeros_like(base,bool)
        for ax,ay in ARM_BOXES[n]:arm|=(xx>=ax)&(xx<ax+16)&(yy>=ay)&(yy<ay+16)
        arm&=~head
        if n==143:arm=((xx<cx-5)|(xx>=cx+7))&(yy<hip)&~head
        remaining=np.where(t!=base,t,0).astype(np.uint8);layers={k:np.zeros_like(base) for k in LAYERS.values()}
        for b,mask in ((5,head),(8,leg),(7,arm)):
            layers[b][mask]=remaining[mask];remaining[mask]=0
        layers[6]=remaining;all_layers[n]=layers
    for n,(alias,total) in MIRRORS.items():
        targets[alias]=mirror(targets[n],total);all_layers[alias]={k:mirror(v,total) for k,v in all_layers[n].items()}
        require(np.array_equal(mirror(render(arc,n)[1],total),render(arc,alias)[1]),'Native mirror relationship differs')
    board=Image.new('RGB',(5*256,3*280),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+FRAMES):
        if n==0:im=render(arc,n,True)[0]
        else:
            base=render(arc,n)[1];merged=base.copy()
            for b in (8,5,7,6):merged=np.where(all_layers[n][b],all_layers[n][b],merged)
            require(np.array_equal(merged,targets[n]),'Layer split cannot cover base')
            for name,b in LAYERS.items():save_image(all_layers[n][b].tobytes(),(160,160),words,out/f'{name}_{n:03}.png')
            im=save_image(targets[n].tobytes(),(160,160),words,out/f'full_{n:03}.png').convert('RGBA')
        tile=im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.paste(tile,(i%5*256,i//5*280+24),tile);draw.text((i%5*256+4,i//5*280+4),str(n),fill='white')
    board.save(out/'family_4x.png')
    write(out/'layers.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':records,'mirror_sums':MIRRORS,'native_body_unchanged':True,'runtime_verified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'frames':len(FRAMES),'registration':records})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
