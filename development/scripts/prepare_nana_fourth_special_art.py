"""차지/사이클론 새 의상을 수용 몸·권총 기준점에 등록한다."""
import argparse,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,distance_transform_edt
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_special_reference import PARENT,PARENT_SHA,FRAMES,ORDER
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.extract_zero import save_image

SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/special_v1/generated.png'
SOURCE_SHA='6ee7f4bc8e6e5f88334bd44ef349cc6493f24df9932cd606bf83b7a135626539'
HIPS={89:85,90:86,91:86,97:86,98:88}
CONTACTS={89:[(58,45,74,63)],90:[(54,56,73,71)],91:[(50,64,68,79)],97:[(64,65,77,78)],98:[(50,66,67,81),(94,66,105,81)]}
ARM_BOXES={89:[(61,60)],90:[(60,66),(80,75)],91:[(62,66),(81,75)],97:[(65,74)],98:[(61,73),(82,73),(91,68)]}
TRANSLATIONS={88:(89,-1),99:(98,1)}

def shift(v,dx):
    result=np.zeros_like(v)
    if dx<0:result[:,:dx]=v[:,-dx:]
    else:result[:,dx:]=v[:,:-dx]
    return result

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor art directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Source changed')
    arc=(PARENT/'modified.arc').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
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
        target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v;lower=hip+4
        for y in range(lower,bb[3]):
            target[y]=0
            for left,right in intervals(base[y]>0):
                target[y,left:right+1]=1
                if right-left>=2:
                    target[y,left+1:right]=5 if y>=bb[3]-3 else 12
                    if right-left>=4 and y<bb[3]-3:target[y,right-1]=11
                elif right>left:target[y,left]=5 if y>=bb[3]-3 else 12
        target[:bb[1]]=0;target[bb[3]:]=0;target[(target==14)&(base!=14)]=2
        for x,y,x2,y2 in [face]+CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        dist,idx=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        require(float(dist[missing].max(initial=0))<=6,f'Costume too far from native body: {n}')
        target[missing]=target[tuple(idx[:,missing])]
        for x,y,x2,y2 in [face]+CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        if n==97:target[100:]=base[100:]
        head=(xx>=cx-7)&(xx<cx+9)&(yy>=cy-8)&(yy<cy+8)
        if n==91:head=(xx>=71)&(xx<87)&(yy>=61)&(yy<77)
        leg=(yy>=hip)|((xx>=cx+8)&(yy>=cy+4))|((yy>=hip-2)&(target==13))
        arm=np.zeros_like(base,bool)
        for ax,ay in ARM_BOXES[n]:arm|=(xx>=ax)&(xx<ax+16)&(yy>=ay)&(yy<ay+16)
        arm&=~head
        remaining=np.where(target!=base,target,0).astype(np.uint8);layers[n]={b:np.zeros_like(base) for b in LAYERS.values()}
        for b,mask in ((5,head),(8,leg),(7,arm)):
            layers[n][b][mask]=remaining[mask];remaining[mask]=0
        layers[n][6]=remaining;targets[n]=target
        records.append({'frame':n,'source_cell':i,'source_box':box,'native_size':list(v.shape[::-1]),'placement':[dx,dy],'face_box':face,'contacts':CONTACTS[n],'hip':hip,'lower_y':lower,'boundary_pixels':int(missing.sum()),'max_boundary_distance':float(dist[missing].max(initial=0))})
    for n,(source,dx) in TRANSLATIONS.items():
        layers[n]={b:shift(v,dx) for b,v in layers[source].items()};targets[n]=render(arc,n)[1].copy()
        for b in (8,5,7,6):targets[n]=np.where(layers[n][b],layers[n][b],targets[n])
        records.append({'frame':n,'shared_costume':source,'translation':[dx,0]})
    board=Image.new('RGB',(3*320,3*280),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0,85]+FRAMES):
        if n in (0,85):im=render(arc,n,True)[0]
        else:
            merged=render(arc,n)[1].copy()
            for b in (8,5,7,6):merged=np.where(layers[n][b],layers[n][b],merged)
            require(np.array_equal(merged,targets[n]),'Layer split cannot cover base')
            for name,b in LAYERS.items():save_image(layers[n][b].tobytes(),(160,160),words,out/f'{name}_{n:03}.png')
            im=save_image(targets[n].tobytes(),(160,160),words,out/f'full_{n:03}.png').convert('RGBA')
        tile=im.crop((40,40,120,104)).resize((320,256),Image.Resampling.NEAREST);board.paste(tile,(i%3*320,i//3*280+24),tile);draw.text((i%3*320+4,i//3*280+4),str(n),fill='white')
    board.save(out/'family_4x.png')
    write(out/'layers.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':records,'native_body_unchanged':True,'runtime_verified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'frames':len(FRAMES),'registration':records})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
