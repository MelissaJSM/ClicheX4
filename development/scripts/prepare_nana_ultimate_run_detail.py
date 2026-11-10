"""대기 원화의 얼굴·크기 기준과 원화 명암을 보존하는 이동 등록."""
import json,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,require,render,write
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.extract_zero import save_image

DETAIL_SHA='fc5a1432f0e1e45bb67e47a8acacc96fa9aea788fa5d0beb493f9e3bdf0f7665'

def runs(row):
    xs=np.flatnonzero(row)
    return [] if not len(xs) else [v for v in np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)]

def register_shaded_legs(target,base,eye_x,eye_y,accepted_skin,lower_mask=None):
    """Retarget source color clusters, never synthesize a solid skin interior."""
    yy,xx=np.indices(target.shape);hip=eye_y+17;lower=(yy>=hip)|((xx>=eye_x+14)&(yy>=eye_y+12)) if lower_mask is None else lower_mask;source=target.copy();target[lower]=0
    limb=source.copy();limb[np.isin(limb,(5,6,7,8,9))]=0
    # A band near each destination row supplies the already drawn knee/calf
    # shading. Its two spans follow the native left/right leg silhouettes.
    for y in range(eye_y+12,160):
        dest=runs((base[y]>0)&lower[y])
        if not dest:continue
        candidates=[]
        for sy in range(max(eye_y+12,y-4),min(160,y+5)):
            parts=runs((limb[sy]>0)&lower[sy])
            if not parts:continue
            centers=[float(q.mean()) for q in parts];cost=abs(sy-y)*2+abs(len(parts)-len(dest))*3+sum(min(abs(float(q.mean())-z) for z in centers) for q in dest)*.1
            candidates.append((cost,sy,parts))
        require(bool(candidates),f'Generated leg source missing at row {y}')
        _,sy,parts=min(candidates,key=lambda q:q[0])
        for di,dr in enumerate(dest):
            sr=parts[di] if len(dest)==len(parts) else min(parts,key=lambda p:abs(float(p.mean())-float(dr.mean())))
            colors=source[sy,sr];width=len(dr)
            if width>=3 and len(colors)>=3:
                interior=np.array(Image.fromarray(colors[None,1:-1]).resize((width-2,1),Image.Resampling.NEAREST))[0];values=np.r_[colors[0],interior,colors[-1]]
            else:values=np.array(Image.fromarray(colors[None,:]).resize((width,1),Image.Resampling.NEAREST))[0]
            target[y,dr]=values
    # Raised/crossed legs can put a source shoe on the same horizontal row
    # as the other calf. Use the accepted bare-leg material mask to prevent
    # stretching that dark shoe over an entire leg. Copy nearby drawn skin
    # shades rather than filling the calf with a constant palette index.
    skin_source=np.isin(source,(10,11,12,13))&lower
    require(np.any(skin_source),'Generated skin shades missing')
    _,nearest=distance_transform_edt(~skin_source,return_indices=True)
    wrong_material=accepted_skin&lower&np.isin(target,(1,2,3,4,14,15))
    target[wrong_material]=source[nearest[0][wrong_material],nearest[1][wrong_material]]
    target[np.nonzero(base)[0].max()+1:]=0
    return lower

def artwork(out):
    from scripts.prepare_nana_ultimate_run import ROOT,D,PARENT,ARC_SHA
    require(digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Unsupported source')
    path=D/'run_detail_v1/generated_margin.png';require(digest(path)==DETAIL_SHA,'Detailed source changed');source=Image.open(path).convert('RGBA');alpha=np.array(source.getchannel('A'));require(not any(np.any(v>=128) for v in (alpha[0],alpha[-1],alpha[:,0],alpha[:,-1])),'Artwork clipped at canvas edge')
    arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
    master=np.array(Image.open(D/'start_v2/ultimate_000.png'));order=json.loads((ROOT/'work/ver_rin_nana/nana_art/run_v1/plan.json').read_text('utf8'))['order'];yy,xx=np.indices((160,160));results={};proof=[]
    for i,n in enumerate(order):
        base=render(arc,n)[1];shot=render(arc,n+1)[1];ey,ex=np.nonzero((base==14)&(yy<80));eye_x=int(round(float(np.median(ex))));eye_y=int(round(float(np.median(ey))));bottom=int(np.nonzero(base)[0].max())
        cell=source.crop((i%4*source.width//4,i//4*source.height//4,(i%4+1)*source.width//4,(i//4+1)*source.height//4));a=np.array(cell);ls,count=label(a[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(ls.flat);sizes[0]=0;keep=ls==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1))
        variants=[]
        for h in range(42,58):
            v=normalize(crop,h,rgb);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<h//2))
            if not len(vx):continue
            cy,cx=float(np.median(vy)),float(np.median(vx));variants.append((abs(h-1-cy-(bottom-eye_y)),abs(h-51),v,cx,cy))
        require(bool(variants),'Missing generated eye');_,_,v,cx,cy=min(variants,key=lambda q:q[:2]);dx=eye_x-round(cx);dy=eye_y-round(cy);target=np.zeros_like(base)
        target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # Register the top of the head independently: bent legs must never
        # inflate the ears, skull or face. Retain source pixel clusters.
        upper=target.copy();target[:eye_y+5]=0;ratio=min(1.0,16/max(cy,1))
        for y in range(eye_y-16,eye_y+5):
            source_y=round(cy+(y-eye_y)*(cy/16 if y<=eye_y else 1));source_y=max(0,min(v.shape[0]-1,source_y));row=v[source_y];width=max(1,round(len(row)*ratio));r=np.array(Image.fromarray(row[None,:]).resize((width,1),Image.Resampling.NEAREST))[0];x=eye_x-round(cx*ratio);target[y,x:x+width]=r
        # The concept has compact twin tails. The source sheet exaggerated
        # their trailing length; register rear-hair extent to the accepted
        # native pose while retaining its highlight/shadow clusters.
        tail_y=eye_y+15;tail_x=eye_x+9;old_right=int(np.nonzero(target[:tail_y])[1].max())+1;new_right=int(np.nonzero(base[:tail_y])[1].max())+1
        if old_right>new_right:
            patch=target[:tail_y,tail_x:old_right].copy();target[:tail_y,tail_x:]=0;target[:tail_y,tail_x:new_right]=np.array(Image.fromarray(patch).resize((new_right-tail_x,tail_y),Image.Resampling.NEAREST))
        # Use the actual accepted facial pixels, not the unrelated base face.
        fx,fy=eye_x-76,eye_y-68;target[65+fy:74+fy,73+fx:83+fx]=master[65:74,73:83]
        from scripts.prepare_shibuki_capsule_nova import raster
        fourth_arc=(PARENT/'modified.arc').read_bytes();fg,fc=entry(fourth_arc,2),entry(fourth_arc,3);fourth=raster(fg,fc,0,0,n)
        for cb in (8,5,7,6):
            layer=raster(fg,fc,0,cb,n);fourth=np.where(layer,layer,fourth)
        legmask=register_shaded_legs(target,base,eye_x,eye_y,np.isin(fourth,(10,11,12,13)))
        dist,nearest=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(dist[missing].max(initial=0)<=7,f'Registration requires redraw for {n}')
        target[missing]=target[nearest[0][missing],nearest[1][missing]]
        diff=base!=shot;gy,gx=np.nonzero(diff);gun_end=int(gx.min())+6;gun=(xx>=gx.min())&(xx<eye_x+1)&(yy>=eye_y+2)&(yy<eye_y+10);firing=target.copy();firing[gun]=shot[gun];lowered=(xx<eye_x+1)&(yy>=eye_y+10)&(yy<eye_y+18);firing[lowered]=shot[lowered]
        sleeve=gun&(xx>=gun_end)&(xx<eye_x)&np.isin(firing,(2,3,4));firing[sleeve]=np.choose(firing[sleeve]-2,[7,8,9]);stray=(shot>0)&(firing==0);firing[stray]=shot[stray]
        for y in range(eye_y+3,eye_y+8):
            row=firing[y];l=np.flatnonzero(row[eye_x-10:eye_x-2])+eye_x-10;r=np.flatnonzero(row[eye_x:eye_x+6])+eye_x
            if len(l) and len(r) and 0<int(r.min()-l.max()-1)<=5:
                for x in range(int(l.max()+1),int(r.min())):
                    if not row[x]:row[x]=7
        require(np.array_equal(firing[gy.min():gy.max()+1,gx.min():gun_end],shot[gy.min():gy.max()+1,gx.min():gun_end]),'Pistol changed')
        for f,b,t in ((n,base,target),(n+1,shot,firing)):
            require(not np.any((b>0)&(t==0)),'Base escapes overlay');require(int(np.nonzero(t)[0].max())==bottom,'Sole shifted');results[f]=t;save_image(t.tobytes(),(160,160),words,out/f'ultimate_{f:03}.png')
        proof.append({'frames':[n,n+1],'eye':[eye_x,eye_y],'sole':bottom,'generated_size':list(v.shape[::-1]),'eye_to_ear_top':int(eye_y-np.nonzero(target)[0].min()),'idle_eye_to_ear_top':16,'detail_fix':True,'face_source':'accepted Ultimate idle pixels','leg_registration':'source-shaded row registration, no solid-skin painting','leg_skin_counts':{str(c):int(np.count_nonzero((target==c)&legmask)) for c in (10,11,12,13)},'native_silhouette_extension_pixels':int(missing.sum()),'max_registration_distance':float(dist[missing].max(initial=0)),'pistol_exact':True,'pistol_mask_bbox':[int(gx.min()),int(gy.min()),gun_end,int(gy.max()+1)]})
    for firing,name in ((False,'run_review_4x.png'),(True,'shoot_review.png')):
        board=Image.new('RGB',(1280,1280),'#252c3c');draw=ImageDraw.Draw(board)
        for i,n in enumerate(order):
            f=n+int(firing);pic=Image.open(out/f'ultimate_{f:03}.png').convert('RGBA').crop((40,40,120,112)).resize((320,288),Image.Resampling.NEAREST);x=i%4*320;y=i//4*320;board.paste(pic,(x,y+24),pic);draw.text((x+4,y+4),str(f),fill='white')
        board.save(out/name)
    return results,proof
