"""원래 남아 있던 두 번째 피격 아머233..236을 수용 의상으로 등록한다."""
import argparse,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_hurt_extra_reference import PARENT,PARENT_SHA,FRAMES
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.extract_zero import save_image
from scripts.project import digest

SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/hurt_extra_v1/generated.png'
SOURCE_SHA='34a636aa36dbf9dbe1cac791c76f7bcb875f8516405a250e7c570fdf67a78e3f'

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh work path required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Input changed')
    arc=(PARENT/'modified.arc').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32)
    rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    source=Image.open(SOURCE).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparency differs');out.mkdir(parents=True)
    yy,xx=np.indices((160,160));masters={};rows=[];pictures={}
    for i,n in enumerate((233,234)):
        base=render(arc,n)[1];by,bx=np.nonzero(base);top,bottom=int(by.min()),int(by.max());ey,ex=np.nonzero((base==14)&(yy<80));require(len(ex)>0,'Native eye missing');eye_x,eye_y=int(round(ex.mean())),int(round(ey.mean()))
        cell=source.crop((i*source.width//2,0,(i+1)*source.width//2,source.height));a=np.array(cell);lab,count=label(a[:,:,3]>=128);sizes=np.bincount(lab.flat);sizes[0]=0;keep=lab==sizes.argmax();sy,sx=np.nonzero(keep);box=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)];a[~keep,3]=0;crop=Image.fromarray(a).crop(box)
        v=normalize(crop,bottom-top+1,rgb);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<v.shape[0]//2))
        if not len(vx):
            colors=np.array(crop).astype(np.int32);red,green,blue=colors[:,:,:3].transpose(2,0,1)
            mask=(green>red+10)&(green>blue+10)&(green>60)&(colors[:,:,3]>=128);mask[crop.height//2:]=False
            cy,cx=np.nonzero(mask);require(len(cx)>0,'Generated eye missing');vx=cx*v.shape[1]/crop.width;vy=cy*v.shape[0]/crop.height
        dx,dy=eye_x-int(round(vx.mean())),eye_y-int(round(vy.mean()));target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        face=(xx>=eye_x-2)&(xx<eye_x+7)&(yy>=eye_y-3)&(yy<eye_y+6);target[face]=base[face]
        hip=eye_y+(15 if n==233 else 14);lower=hip+4
        # The uppermost left skin pixels in 234 are the raised palm, not hat glitter.
        arm=(xx<eye_x-5)&(yy<hip);target[arm]=base[arm]
        specks=np.isin(target,(10,11,12,13,15))&(yy>=eye_y-12)&(yy<eye_y-3)&(xx>=eye_x+5)&(xx<eye_x+14);target[specks]=2
        for y in range(eye_y-2,hip+1):
            hair=np.flatnonzero(np.isin(target[y],(7,8,9))&(np.arange(160)>=eye_x+8))
            for x in hair[:-2]:target[y,x]={7:2,8:3,9:4}[int(target[y,x])]
        calves,count=label((base>0)&(yy>=lower));foot=np.zeros_like(base,bool)
        for k in range(1,count+1):
            cy,cx=np.nonzero(calves==k)
            if len(cx):foot|=(calves==k)&(yy>=int(cy.max())-2)
        for y in range(lower,bottom+1):
            target[y]=0
            for l,r in intervals(base[y]>0):
                target[y,l:r+1]=1
                if r-l>=2:
                    target[y,l+1:r]=12
                    if r-l>=4:target[y,r-1]=11
                    for x in range(l+1,r):
                        if foot[y,x]:target[y,x]=5
                elif r>l:target[y,l]=5 if foot[y,l] or foot[y,r] else 12
        target[bottom]=np.where(base[bottom],1,0);target[bottom+1:]=0
        sy,sx=np.nonzero(target);missing=np.argwhere((base>0)&(target==0));distances=[]
        for y,x in missing:
            dist=(sy-y)**2+(sx-x)**2;k=int(dist.argmin());require(dist[k]<=25,f'Excessive local registration {n} {x},{y}');target[y,x]=target[sy[k],sx[k]];distances.append(int(dist[k]))
        target[face]=base[face]
        islands,count=label(target>0,np.ones((3,3)))
        for k in range(1,count+1):
            mask=islands==k
            if np.count_nonzero(mask)<=2 and not np.any(base[mask]):target[mask]=0
        top=int(np.nonzero(target)[0].min());masks={5:(xx>=eye_x-1)&(xx<eye_x+15)&(yy>=top)&(yy<top+16),8:(yy>=hip)|((xx>=eye_x+13)&(yy>=eye_y+4)),7:(xx<eye_x-1)&(yy<hip)}
        remain=np.where(target!=base,target,0).astype(np.uint8);layers={k:np.zeros_like(base) for k in LAYERS.values()}
        for k in (5,8,7):layers[k][masks[k]]=remain[masks[k]];remain[masks[k]]=0
        layers[6]=remain;masters[n]=layers
        rows.append({'frame':n,'source_cell':i,'source_crop':box,'size':list(v.shape[::-1]),'placement':[dx,dy],'eye':[eye_x,eye_y],'face_box':[eye_x-2,eye_y-3,eye_x+7,eye_y+6],'native_lower_from_y':lower,'boundary_pixels':len(missing),'max_boundary_distance_squared':max(distances,default=0)})
    for n in FRAMES:
        layers=masters[233 if n==233 else 234];merged=render(arc,n)[1].copy()
        for k in (8,5,7,6):
            name=next(name for name,v in LAYERS.items() if v==k);save_image(layers[k].tobytes(),(160,160),words,out/f'{name}_{n:03}.png');merged=np.where(layers[k],layers[k],merged)
        pictures[n]=save_image(merged.tobytes(),(160,160),words,out/f'full_{n:03}.png').convert('RGBA')
    board=Image.new('RGB',(1280,560),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+FRAMES):
        for row in (0,1):
            im=(render(arc,n,True)[0] if n==0 or row==0 else pictures[n]).crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST)
            board.paste(im,(i*256,row*280+24),im);draw.text((i*256+4,row*280+4),f'{n} '+('before' if row==0 else 'fixed'),fill='white')
    board.save(out/'comparison_4x.png');write(out/'layers.json',{'task':'fourth_armor_nana','parent_sha256':PARENT_SHA,'frames':FRAMES,'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':rows,'runtime_verified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'frames':FRAMES})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
