"""얼티밋 체이서13자세와 조종석19머리를 원래 접점에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt,binary_erosion
from scripts import prepare_nana_ultimate_ride_heads as heads
from scripts.prepare_nana_ultimate_ride_heads import PARENT,PARENT_SHA,ARC_SHA,D,full,entry,render,require,write,translate
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_fourth_vehicle_art import CONTACTS,HIPS
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
ORDER=[162,166,170,174]
FRAMES=list(range(162,175))+heads.FRAMES
EDITED_FRAMES=[n for n in FRAMES if n!=198]

def artwork(out):
    targets,overlays,proof=heads.artwork(out)
    arc=(PARENT/'PL02_U.ARC').read_bytes();c,g=entry(arc,3),entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True)
    path=D/'chaser_v1/generated.png';provenance=json.loads((path.parent/'provenance.json').read_text('utf8'));require(digest(path)==provenance['sha256'],'Chaser source changed');src=Image.open(path).convert('RGBA');require(src.getchannel('A').getextrema()==(0,255),'Transparent source required')
    words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);master=full(arc,0);yy,xx=np.indices(master.shape)
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];by,bx=np.nonzero(base);bottom=int(by.max());gy,gx=np.nonzero((base==14)&(yy<80));ex,ey=round(float(np.median(gx))),round(float(np.median(gy)))
        a=np.array(src.crop((i*src.width//4,0,(i+1)*src.width//4,src.height)));labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));col=np.array(crop).astype(np.int32);cyy,_=np.indices(col.shape[:2]);gy,gx=np.nonzero((col[:,:,1]>col[:,:,0]+6)&(col[:,:,1]>col[:,:,2]+6)&(col[:,:,3]>=192)&(cyy<crop.height*.6));require(len(gx)>0,'Generated eye absent')
        choices=[]
        for h in range(32,65):
            w=round(h*crop.width/crop.height);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);choices.append((abs(h-1-cy-(bottom-ey)),abs(cy-16),h,w,cx,cy))
        _,_,h,w,cx,cy=min(choices);v=normalize(crop,h,rgb,width=w);target=np.zeros_like(base);dx,dy=ex-cx,ey-cy;target[dy:dy+h,dx:dx+w]=v
        # Reuse the native-resolution head; crouching must not shrink the skull.
        head=master[52:74,67:90];hx,hy=ex-9,ey-16
        target[:ey-16]=0;target[hy:ey+5,hx:ex+12]=0
        region=target[hy:hy+22,hx:hx+23];region[head>0]=head[head>0]
        # Approved face and ear clusters keep the idle design recognizable.
        face=master[65:74,73:83];fx,fy=ex-3,ey-3;mask=face>0;target[fy:fy+9,fx:fx+10][mask]=face[mask]
        # Retain the authored skin shading while mapping the pedal contacts.
        lower=(yy>=HIPS[n]+3);register_shaded_legs(target,base,ex,ey,np.isin(target,(10,11,12,13)),lower)
        for x,y,x2,y2 in CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(dist[missing].max(initial=0)<=6,'Chaser pose too far from native');target[missing]=target[tuple(near[:,missing])]
        for x,y,x2,y2 in CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        protected_head=np.zeros_like(target,dtype=bool);protected_head[hy:hy+22,hx:hx+23]=head>0
        rim=(target>0)&~binary_erosion(target>0,np.ones((3,3),bool))&(target==5)&~protected_head;target[rim]=1
        for x,y,x2,y2 in CONTACTS[n]:target[y:y2,x:x2]=base[y:y2,x:x2]
        require(not np.any((base>0)&(target==0)),'Base escapes chaser overlay');require(int(np.nonzero(target)[0].max())==bottom,'Pedal sole moved')
        overlay=np.where(target!=base,target,0).astype(np.uint8);f=bank['frames'][n];aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']];p0=composition_frame(c,0,n)['parts'][0]
        for k in aliases:
            native=render(arc,k)[1];p=composition_frame(c,0,k)['parts'][0];tx,ty=p['x']-p0['x'],p['y']-p0['y'];require(np.array_equal(native,translate(base,tx,ty)),'Chaser aliases differ');targets[k]=translate(target,tx,ty);overlays[k]=translate(overlay,tx,ty);proof.append(dict(frames=[k,k],basis=n,translation=[tx,ty],eye=[ex+tx,ey+ty],sole=bottom+ty,source_size=[w,h],source_crop_size=list(crop.size),face_box=[fx+tx,fy+ty,fx+tx+10,fy+ty+9],contacts=[[x+tx,y+ty,x2+tx,y2+ty]for x,y,x2,y2 in CONTACTS[n]],native_lower_from_y=HIPS[n]+3+ty,missing_pixels=int(missing.sum()),max_missing_distance=float(dist[missing].max(initial=0)),pistol_present=False,pistol_mask_bbox=None))
    for n in FRAMES:save_image(targets[n].tobytes(),(160,160),words,out/f'ultimate_{n:03}.png');save_image(overlays[n].tobytes(),(160,160),words,out/f'overlay_{n:03}.png')
    board=Image.new('RGB',(1600,360),'#46545c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+ORDER):
        v=full(arc,0) if n==0 else targets[n];im=Image.fromarray(np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),2));pic=im.crop((35,35,115,115)).resize((320,320),Image.Resampling.NEAREST);board.paste(pic,(i*320,30),pic);draw.text((i*320+4,5),str(n),fill='white')
    board.save(out/'chaser_review.png');return targets,overlays,sorted(proof,key=lambda q:q['frames'][0])

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,overlays,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};packing=[]
    for n in ORDER+list(heads.HEADS):
        f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={p['tile']for v in ns for b in(0,6,7,8)for p in composition_frame(c,b,v)['parts']};keep|={p['tile']for v in ns if v==198 for p in composition_frame(c,5,v)['parts']};pool={t for t in range(f['tile_count'])if t not in keep and t%16!=0};new,rr=pack_shared(raw,f['tile_count'],[overlays[n]],pool,[len(pool)])
        for v in ns:
            replacements[v]=encode_stream(new)
            if v==198:continue
            q=next(q for q in proof if q['frames'][0]==v);dx,dy=q['translation'];changes[v]=b''.join(struct.pack('<BBbb',fl,t,x+dx-80,y+dy-80)for t,x,y,fl in rr[0])
        packing.append(dict(frames=ns,free_tiles=len(pool),parts=len(rr[0])))
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{});require(not full(result,198).any(),'Blank198 changed');(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_vehicle',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,frames=FRAMES,edited_frames=EDITED_FRAMES,registration=proof,packing=packing,graphics_repack=rep,parts_bank5_remaining=slack,verification=check,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=check)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
