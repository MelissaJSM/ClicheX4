"""등장·승리·귀환10참조를 승인된 체형과 공통 효과에 맞춰 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt,binary_dilation
from scripts.prepare_nana_ultimate_ceremony_reference import D,PARENT,PARENT_SHA,ARC_SHA,FRAMES,ORDER,PRESERVED
from scripts.prepare_nana_fourth_ceremony_art import CONTACTS,shift
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import full,pack_resources
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
SOURCE_SHA='410981306cb2867fcf8ebeb7eb8eabfcaa948cfa7a85dc2ad90749743364891e'
GUNS={138:[65,45,80,57],206:[65,68,72,77],207:[58,40,74,54]}

def artwork(out):
 src=D/'ceremony_v1/generated_first.png';require(digest(src)==SOURCE_SHA,'Source changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));master=full(arc,0);targets={};meta={}
 for i,n in enumerate(ORDER):
  base=render(arc,n)[1];by,bx=np.nonzero(base);bottom=int(by.max());cell=source.crop((i%3*source.width//3,i//3*source.height//2,(i%3+1)*source.width//3,(i//3+1)*source.height//2));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);cyy,cxx=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+8)&(ca[:,:,1]>ca[:,:,2]+8)&(ca[:,:,3]>=192)&(cyy<crop.height*.55);gy,gx=np.nonzero(green);require(len(gx)>0,'Source eye missing');ex=76;ey=65 if n==138 else 67;choices=[]
  for h in range(32,72):
   w=round(h*crop.width/crop.height);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);choices.append((abs(h-1-cy-(bottom-ey)),abs(cy-16),h,w,cx,cy))
  _,_,h,w,cx,cy=min(choices);v=normalize(crop,h,rgb,width=w);dx,dy=ex-cx,ey-cy;target=np.zeros_like(base);target[dy:dy+h,dx:dx+w]=v;face=[ex-3,ey-3,ex+7,ey+6];x,y,x2,y2=face;target[y:y2,x:x2]=master[65:74,73:83]
  if n==138:target[:int(by.min())]=0
  for j,(x,y,x2,y2)in enumerate(CONTACTS[n]):
   patch=base[y:y2,x:x2].copy()
   if n not in GUNS or list((x,y,x2,y2))!=GUNS[n]:
    for old,new in((2,5),(3,7),(4,8)):patch[base[y:y2,x:x2]==old]=new
   target[y:y2,x:x2]=patch
  dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);save_image(target.tobytes(),(160,160),words,out/f'registered_{n:03}.png');print(json.dumps(dict(frame=n,source_size=[w,h],position=[dx,dy],eye=[ex,ey],max_distance=float(dist[missing].max(initial=0)),far=np.argwhere(missing&(dist>6)).tolist())),flush=True);require(dist[missing].max(initial=0)<=6,f'Pose {n} needs registration correction');target[missing]=target[near[0][missing],near[1][missing]];target[bottom+1:]=0
  labs,count=label(target>0,np.ones((3,3)));removed=[]
  for k in range(1,count+1):
   mask=labs==k
   if np.count_nonzero(mask)<=2 and not np.any(base[mask]):removed.extend([[int(x),int(y)]for y,x in np.argwhere(mask)]);target[mask]=0
  # Contacts above the face do not replace the approved eye/chin cluster.
  x,y,x2,y2=face;mask=master[65:74,73:83]>0;target[y:y2,x:x2][mask]=master[65:74,73:83][mask]
  targets[n]=target;meta[n]=dict(frames=[n,n],source_cell=i,source_size=[w,h],source_crop_size=list(crop.size),placement=[dx,dy],face_box=face,eye=[ex,ey],sole=bottom,contacts=CONTACTS[n],pistol_present=n in GUNS,pistol_mask_bbox=GUNS.get(n),max_registration_distance=float(dist[missing].max(initial=0)),removed_detached_pixels=removed)
 # Arrival settle shares the exact accepted idle, plus the native12 dust pixels.
 for n in(141,142):
  native=render(arc,n)[1];base0=render(arc,0)[1];fx=np.where(native!=base0,native,0).astype(np.uint8);require(not np.any((base0>0)&(native!=base0)),'Ready body differs from idle');targets[n]=np.where(fx,fx,master).astype(np.uint8);save_image(fx.tobytes(),(160,160),words,out/f'effect_{n:03}.png');meta[n]=dict(frames=[n,n],shared_body_frame=0,exact_accepted_idle=True,native_effect_pixels=int(np.count_nonzero(fx)),pistol_present=False,pistol_mask_bbox=None)
 require(np.array_equal(shift(render(arc,138)[1],-1),render(arc,139)[1]),'Arrival shift differs');targets[139]=shift(targets[138],-1);q=meta[138];x,y,x2,y2=q['pistol_mask_bbox'];meta[139]=dict(frames=[139,139],shared_body_frame=138,translation=[0,-1],pistol_present=True,pistol_mask_bbox=[x,y-1,x2,y2-1])
 # Retain the two original aura colors and adapt the outline to the new body.
 body=shift(targets[156],-1);native=render(arc,157)[1];oldbody=shift(render(arc,156)[1],-1);fx=np.where(native!=oldbody,native,0).astype(np.uint8);require(not np.any((oldbody>0)&(native!=oldbody))and set(np.unique(fx))=={0,7,13},'Unexpected return aura');mask=body>0;outer=binary_dilation(mask,np.ones((3,3)),iterations=2);inner=binary_dilation(mask,np.ones((3,3)),iterations=1);aura=np.where(inner,7,np.where(outer,13,0)).astype(np.uint8);aura[mask]=0;dist=distance_transform_edt(~mask);require(dist[fx>0].max(initial=0)<=4,'Native aura far from new silhouette');aura=np.where((fx>0)&(aura==0)&~mask,fx,aura).astype(np.uint8);targets[157]=np.where(body,body,aura).astype(np.uint8);save_image(aura.tobytes(),(160,160),words,out/'effect_157.png');meta[157]=dict(frames=[157,157],shared_body_frame=156,translation=[0,-1],pistol_present=False,pistol_mask_bbox=None,aura_colors=[7,13],native_aura_pixels=int(np.count_nonzero(fx)),new_aura_pixels=int(np.count_nonzero(aura)),new_body_in_aura_unmodified=True)
 board=Image.new('RGB',(1280,900),'#252c3c');draw=ImageDraw.Draw(board)
 for i,n in enumerate([0]+FRAMES):
  v=targets[n]if n else master
  if n:require(not np.any((render(arc,n)[1]>0)&(v==0)),'Base escapes new ceremony');save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
  rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((40,32,120,112)).resize((256,256),Image.Resampling.NEAREST);x,y=i%5*256,i//5*300;board.paste(im,(x,y+24),im);draw.text((x+4,y+4),str(n)if n else'ACCEPTED IDLE',fill='white')
 board.save(out/'ceremony_review_4x.png');return targets,[meta[n]for n in FRAMES]

def prepare(out,art_only=False):
 out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
 if art_only:return
 result,packed=pack_resources((PARENT/'PL02_U.ARC').read_bytes(),targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_ceremony',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,preserved_common_frames=PRESERVED,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
