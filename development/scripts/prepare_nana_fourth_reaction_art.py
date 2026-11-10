"""피격의 닫힌 눈·효과와 저체력 입/접지를 보존해 생성 의상을 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_reaction_reference import PARENT,PARENT_SHA,FRAMES
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.prepare_nana_fourth_run_art import intervals,LAYERS
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_shibuki_idle import breathe
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import composition_frame
from src.psx_sprite_batch import canvas_from_parts

SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/reaction_v1/generated.png'
SOURCE_SHA='0c2f8d289442572462787cf60f75cfb579b3dace6836f3e5bffe71503fc0d2b7'

def effect_parts(c,bank,n):
    comp=composition_frame(c,bank,n)
    # 107/108 append independent electricity/heat overlays to the 106 body.
    if n not in (107,108):return {**comp,'parts':[]}
    ordinary={p['tile'] for p in composition_frame(c,bank,106)['parts']}
    return {**comp,'parts':[p for p in comp['parts'] if p['tile'] not in ordinary]}

def face_anchor(v):
    yy,xx=np.indices(v.shape);top=int(np.nonzero(v)[0].min())
    lab,count=label(np.isin(v,(11,12,13))&(yy<top+13),np.ones((3,3)))
    require(count>0,'Face skin landmark missing')
    chosen=max(range(1,count+1),key=lambda k:np.count_nonzero(lab==k))
    y,x=np.nonzero(lab==chosen)
    return int(round(x.mean())),int(round(y.mean())),[int(x.min())-1,int(y.min())-2,int(x.max())+2,int(y.max())+2]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor path required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Input changed')
    arc=(PARENT/'modified.arc').read_bytes();c=entry(arc,3);words=struct.unpack_from('<16H',entry(arc,9),32)
    rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    source=Image.open(SOURCE).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparency differs')
    yy,xx=np.indices((160,160));masters={};metadata=[];out.mkdir(parents=True)
    for i,n in enumerate((106,110,122)):
        base=render(arc,n)[1];eyex,eyey,face=face_anchor(base);by,bx=np.nonzero(base);top,bottom=int(by.min()),int(by.max())
        cell=source.crop((i*source.width//3,0,(i+1)*source.width//3,source.height));a=np.array(cell)
        lab,num=label(a[:,:,3]>=128);sizes=np.bincount(lab.flat);sizes[0]=0;keep=lab==sizes.argmax();sy,sx=np.nonzero(keep)
        box=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)];a[~keep,3]=0
        v=normalize(Image.fromarray(a).crop(box),bottom-top+1,rgb);vx,vy,_=face_anchor(v);dx,dy=eyex-vx,eyey-vy
        target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        x,y,x2,y2=face;target[y:y2,x:x2]=base[y:y2,x:x2]
        hip=eyey+({106:14,110:11,122:17}[n])
        if n in (106,110):
            arm=(xx<eyex-5)&(yy<hip+4)
            target[arm]=base[arm]
        # Retain the existing leg articulation and skin cluster style.
        lower=hip+4;calves,count=label((base>0)&(yy>=lower));foot=np.zeros_like(base,bool)
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
        # Keep the small held pistol and palm intact in the tired pose.
        gun_box=[70,80,77,88] if n==122 else None
        if gun_box:
            x,y,x2,y2=gun_box;target[y:y2,x:x2]=base[y:y2,x:x2]
        specks=np.isin(target,(10,11,12,13,15))&(yy>=eyey-12)&(yy<eyey-4)&(xx>=eyex+3)&(xx<eyex+14);target[specks]=2
        for y in range(eyey-2,hip+1):
            hair=np.flatnonzero(np.isin(target[y],(7,8,9))&(np.arange(160)>=eyex+8))
            for x in hair[:-2]:target[y,x]={7:2,8:3,9:4}[int(target[y,x])]
        save_image(target.tobytes(),(160,160),words,out/f'registered_{n:03}.png')
        print({'frame':n,'face_anchor':[eyex,eyey],'source_anchor':[vx,vy],'position':[dx,dy],'size':list(v.shape[::-1])},flush=True)
        sy,sx=np.nonzero(target);missing=np.argwhere((base>0)&(target==0));distances=[]
        for y,x in missing:
            dist=(sy-y)**2+(sx-x)**2;k=int(dist.argmin());require(dist[k]<=36,f'Pose registration exceeds six pixels: {n} {x},{y}')
            target[y,x]=target[sy[k],sx[k]];distances.append(int(dist[k]))
        x,y,x2,y2=face;target[y:y2,x:x2]=base[y:y2,x:x2]
        masters[n]=target
        metadata.append({'frame':n,'source_cell':i,'crop':box,'size':list(v.shape[::-1]),'placement':[dx,dy],'face_anchor':[eyex,eyey],'face_box':face,'hip':hip,'native_lower_from_y':lower,'boundary_pixels':len(missing),'max_boundary_distance_squared':max(distances,default=0),'gun_box':gun_box})
    pictures={};masks={}
    for n in FRAMES:
        core=106 if n in (106,107,108) else 110 if n in (110,111) else 122
        base=render(arc,core)[1];target=masters[core].copy();q=next(q for q in metadata if q['frame']==core)
        delta={120:1,121:1,122:0,123:0,124:-1,125:-1}.get(n,0)
        if core==122:
            # Exactly the native lower-body taper, with the final five rows fixed.
            target[55:103,56:104]=breathe(target[55:103,56:104],delta)
            base=render(arc,n)[1]
            x,y,x2,y2=q['face_box'];y+=delta;y2+=delta;target[y:y2,x:x2]=base[y:y2,x:x2]
        require(not np.any((base>0)&(target==0)),f'Costume cannot erase base {n}')
        ex,ey=q['face_anchor'];ey+=delta;hip=q['hip']+delta;top=int(np.nonzero(target)[0].min())
        layer_masks={5:(xx>=ex-2)&(xx<ex+14)&(yy>=top)&(yy<top+16),
                     8:(yy>=hip)|((xx>=ex+12)&(yy>=ey+4)),
                     7:(xx<ex-1)&(yy>=ey+6)&(yy<hip)}
        layers={k:np.zeros_like(base) for k in LAYERS.values()};remaining=np.where(target!=base,target,0).astype(np.uint8)
        for k in (5,8,7):layers[k][layer_masks[k]]=remaining[layer_masks[k]];remaining[layer_masks[k]]=0
        layers[6]=remaining
        actual_base,_,desc,raw=render(arc,n);merged=render(arc,n)[1].copy()
        for k in (8,5,7,6):
            name=next(name for name,v in LAYERS.items() if v==k)
            save_image(layers[k].tobytes(),(160,160),words,out/f'{name}_costume_{n:03}.png')
            ep=effect_parts(c,k,n)
            fx=canvas_from_parts(raw,desc['tile_count'],ep) if ep['parts'] else np.zeros_like(base)
            layers[k]=np.where(fx,fx,layers[k])
            save_image(layers[k].tobytes(),(160,160),words,out/f'{name}_{n:03}.png');merged=np.where(layers[k],layers[k],merged)
        pictures[n]=save_image(merged.tobytes(),(160,160),words,out/f'full_{n:03}.png').convert('RGBA')
    board=Image.new('RGB',(1024,3*280),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+FRAMES):
        im=(render(arc,n,True)[0] if n==0 else pictures[n]).crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST)
        board.paste(im,(i%4*256,i//4*280+24),im);draw.text((i%4*256+4,i//4*280+4),str(n),fill='white')
    board.save(out/'family_4x.png')
    write(out/'layers.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'canvas_size':[160,160],'origin':[80,80],'palette_words':list(words),'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'registration':metadata,'effects_preserved':True,'runtime_verified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'frames':len(FRAMES)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
