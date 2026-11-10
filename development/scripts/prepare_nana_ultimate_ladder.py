"""승인 체형의 사다리 원화를 등록하고 네 반전쌍과 두 사랑이를 공유한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_ultimate_ladder_reference import D,PARENT,PARENT_SHA,ARC_SHA,FRAMES,ORDER
from scripts.prepare_nana_fourth_ladder_art import MIRRORS,CONTACTS,mirror
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import full,pack_resources
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
SOURCE_SHA='f384b37fc1309fd47df7192ad90ab0f62ad1d1c2d29eb4fdc2edba8b91780bc5'
GUNS={150:[56,69,64,76],155:[59,65,67,72]}

def correct_base(arc):
 require(sha256(arc)==ARC_SHA,'Wrong parent');g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));replacements={};proof=[]
 for n,box in GUNS.items():
  x0,y0,x1,y1=box;f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(ns==([148,149,150]if n==150 else[155]),'Unknown gun aliases');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;data=bytearray(raw);_,loc,_=indexed_atlas(raw,f['tile_count']);parts=composition_frame(c,0,n)['parts'];protected={p['tile']for v in ns for cb in(0,6,7,8)if v!=n or cb!=0 for p in composition_frame(c,cb,v)['parts']};old=raster(g,c,0,0,n);wanted=old.copy();wanted[y0:y1,x0:x1]=module
  for y in range(y0,y1):
   for x in range(x0,x1):
    if old[y,x]==wanted[y,x]:continue
    hits=[p for p in parts if p['x']+80<=x<p['x']+96 and p['y']+80<=y<p['y']+96];editable=[p for p in hits if p['tile']not in protected];require(bool(editable),'Pistol outside editable base');paint=editable[-1]
    for p in hits:
     tx=x-80-p['x'];ty=y-80-p['y'];tx=15-tx if p['flip_x']else tx;ty=15-ty if p['flip_y']else ty;pos,shift=loc[(p['tile']//16*16+ty)*256+p['tile']%16*16+tx];value=int(wanted[y,x])if p is paint else 0
     if (data[pos]>>shift)&15==value:continue
     require(p['tile']not in protected,'Protected base tile');data[pos]=(data[pos]&~(15<<shift))|(value<<shift)
  for v in ns:
   for cb in(0,6,7,8):require(np.array_equal(canvas_from_parts(bytes(data),f['tile_count'],local_composition(composition_frame(c,cb,v))),wanted if v==n and cb==0 else raster(g,c,0,cb,v)),'Pistol changes another layer')
   replacements[v]=encode_stream(bytes(data))
  proof.append(dict(frame=n,gun_module_box=box,changed_base_pixels=int(np.count_nonzero(old!=wanted)),all_other_base_pixels_preserved=True))
 ng,rep=repack_graphics_bank(g,0,replacements);return replace_entry(arc,2,ng),proof

def artwork(out):
 src=D/'ladder_v1/generated.png';require(digest(src)==SOURCE_SHA,'Source changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();corrected,baseproof=correct_base(arc);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));master=full(arc,0);targets={};meta={};module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'))
 for i,n in enumerate(ORDER):
  base=render(corrected,n)[1];by,bx=np.nonzero(base);top,bottom=int(by.min()),int(by.max());cell=source.crop((i%3*source.width//3,i//3*source.height//3,(i%3+1)*source.width//3,(i//3+1)*source.height//3));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);cyy,cxx=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+8)&(ca[:,:,1]>ca[:,:,2]+8)&(ca[:,:,3]>=192)&(cyy<crop.height*.55);gy,gx=np.nonzero(green);ey,ex=np.nonzero((base==14)&(yy<90));face=None
  if n in(143,149,154,155):
   require(len(gx)and len(ex),'Missing face');ex=int(round(float(np.median(ex))));ey=int(round(float(np.median(ey))));choices=[]
   for h in range(30,66):
    w=round(h*crop.width/crop.height);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);choices.append((abs(h-1-cy-(bottom-ey)),abs(h-(bottom-top+3)),h,w,cx,cy))
   _,_,h,w,cx,cy=min(choices);dx,dy=ex-cx,ey-cy;face=[ex-3,ey-3,ex+7,ey+6]
  else:
   h=bottom-top+3;w=round(h*crop.width/crop.height);dx=round((bx.min()+bx.max()+1-w)/2);dy=bottom+1-h
  v=normalize(crop,h,rgb,width=w);target=np.zeros_like(base);target[dy:dy+h,dx:dx+w]=v
  if face:
   x,y,x2,y2=face;target[y:y2,x:x2]=master[65:74,73:83]
  # Preserve the actual rung-contact pixels, with pink cuffs instead of dark cloth.
  for x,y,x2,y2 in CONTACTS[n]:
   patch=base[y:y2,x:x2].copy()
   for old,new in((2,5),(3,7),(4,8)):patch[base[y:y2,x:x2]==old]=new
   target[y:y2,x:x2]=patch
  dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);save_image(target.tobytes(),(160,160),words,out/f'registered_{n:03}.png');print(json.dumps(dict(frame=n,size=[w,h],position=[dx,dy],face=face,missing_pixels=int(missing.sum()),max_distance=float(dist[missing].max(initial=0)),far=np.argwhere(missing&(dist>6)).tolist())),flush=True)
  require(dist[missing].max(initial=0)<=6,f'Pose {n} needs local registration');target[missing]=target[near[0][missing],near[1][missing]];target[bottom+1:]=0
  clusters,count=label(target>0,np.ones((3,3)));removed=[]
  for k in range(1,count+1):
   mask=clusters==k
   if np.count_nonzero(mask)<=2 and not np.any(base[mask]):removed.extend([[int(x),int(y)]for y,x in np.argwhere(mask)]);target[mask]=0
  targets[n]=target;meta[n]=dict(frames=[n,n],source_cell=i,source_size=[w,h],source_crop_size=list(crop.size),placement=[dx,dy],face_box=face,sole=bottom,contacts=CONTACTS[n],pistol_present=False,pistol_mask_bbox=None,max_registration_distance=float(dist[missing].max(initial=0)),new_leg_width_retained=True,removed_detached_pixels=removed)
 # The two firing bodies share the hanging pose; the front arm changes to
 # the authored shooting sleeve and uses the approved 8x7 pistol unchanged.
 authored_shot=targets[155].copy()
 for n,box in GUNS.items():
  base=render(corrected,n)[1];target=targets[149].copy();x,y,x2,y2=box;arm=(xx<77)&(yy>=64)&(yy<84);delta=x-59;vertical=y-65;shifted=np.zeros_like(base)
  for row in range(160):
   for col in range(max(0,-delta),min(160,160-delta)):
    if 0<=row+vertical<160:shifted[row+vertical,col+delta]=authored_shot[row,col]
  # Register sleeve colors to the existing firing arm; never stretch the pistol.
  native_arm=arm&(base>0);source_arm=arm&np.isin(shifted,(5,6,7,8,9,10,11,12,13));require(source_arm.any(),'Missing authored firing sleeve');_,near=distance_transform_edt(~source_arm,return_indices=True);target[arm]=0;target[native_arm]=shifted[near[0][native_arm],near[1][native_arm]];target[y:y2,x:x2]=module
  missing=(base>0)&(target==0);dist,near=distance_transform_edt(target==0,return_indices=True);require(dist[missing].max(initial=0)<=3,'Firing body registration differs');target[missing]=target[near[0][missing],near[1][missing]]
  accepted_arm=full(arc,85)[72:77,66:74];strip=np.concatenate((accepted_arm[:,:3],np.array(Image.fromarray(accepted_arm[:,3:]).resize((77-x2-3,5),Image.Resampling.NEAREST))),axis=1)
  for col in range(x2,77):
   rows=np.flatnonzero(native_arm[:,col]&(np.arange(160)>=y+2)&(np.arange(160)<y+8))
   for row in rows:target[row,col]=strip[min(4,int(row-rows[0])),col-x2]
  target[y:y2,x:x2]=module;fx,fy,fx2,fy2=meta[149]['face_box'];target[fy:fy2,fx:fx2]=targets[149][fy:fy2,fx:fx2];targets[n]=target;meta[n]={**meta[149], 'frames':[n,n],'pistol_present':True,'pistol_mask_bbox':box,'gun_module_box':box,'shared_body_frame':149,'authored_arm_source_frame':155,'accepted_sleeve_source_frame':85,'contacts':CONTACTS[149]}
 for n,(alias,total)in MIRRORS.items():
  require(np.array_equal(mirror(render(corrected,n)[1],total),render(corrected,alias)[1]),'Native mirror differs');targets[alias]=mirror(targets[n],total);q=meta[n];face=q['face_box'];meta[alias]={**q,'frames':[alias,alias],'mirror_source':n,'mirror_sum':total,'contacts':[[total-x2+1,y,total-x+1,y2]for x,y,x2,y2 in q['contacts']],'face_box':None if face is None else[total-face[2]+1,face[1],total-face[0]+1,face[3]]}
 board=Image.new('RGB',(1280,960),'#252c3c');draw=ImageDraw.Draw(board)
 for i,n in enumerate([0]+FRAMES):
  v=targets[n]if n else master
  if n:require(not np.any((render(corrected,n)[1]>0)&(v==0)),'Base escapes target');save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
  rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((40,36,120,116)).resize((256,256),Image.Resampling.NEAREST);x,y=i%5*256,i//5*320;board.paste(im,(x,y+24),im);draw.text((x+4,y+4),str(n)if n else'ACCEPTED IDLE',fill='white')
 board.save(out/'ladder_review_4x.png');return targets,[meta[n]for n in FRAMES],corrected,baseproof

def pack(arc,targets):
 g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);changes={};replacements={};reports=[];seen=set()
 reverse={alias:(src,total)for src,(alias,total)in MIRRORS.items()}
 for n in FRAMES:
  f=bank['frames'][n];off=f['offset']
  if off in seen:continue
  seen.add(off);ns=[q['index']for q in bank['frames']if q['offset']==off];require(set(ns)<=set(FRAMES),'Unselected alias');raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data;keep={q['tile']for v in ns for cb in(0,6,7,8)for q in composition_frame(c,cb,v)['parts']};pool=set(range(f['tile_count']))-keep;selected=[v for v in ns if v not in reverse]
  if any(v in reverse for v in ns):pool={t for t in pool if t%16!=0}
  overlays=[np.where((targets[v]==raster(g,c,0,0,v))&(targets[v]!=15),0,targets[v]).astype(np.uint8)for v in selected];new,rr=pack_shared(raw,f['tile_count'],overlays,pool,[len(pool)]*len(selected));rows=dict(zip(selected,rr))
  for v in ns:
   if v in reverse:
    src,total=reverse[v];rows[v]=[(t,total-x-15,y,fl^64)for t,x,y,fl in rows[src]]
   changes[v]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rows[v]);replacements[v]=encode_stream(new)
  reports.append(dict(frames=ns,source_frames=selected,free_tiles=len(pool),parts=[len(rows[v])for v in ns]));print(json.dumps(reports[-1]),flush=True)
 nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{})
 return result,dict(packing=reports,graphics_repack=rep,parts_bank5_remaining=slack,verification=check)

def prepare(out,art_only=False):
 out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof,base,baseproof=artwork(out);write(out/'registration.json',proof)
 if art_only:return
 result,packed=pack(base,targets);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_ladder',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,registration=proof,base_correction=baseproof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
