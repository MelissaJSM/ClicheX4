"""Same native pattern packer, reserving a safe unflipped padded edge first."""
import numpy as np
from scripts.prepare_shibuki_armor_motion import fit
from src.psx_player import indexed_atlas
from native_pose_pack import shared_components

def fit_two(mask):
 ys,xs=np.nonzero(mask)
 if not len(xs):return []
 if xs.max()-xs.min()<16 and ys.max()-ys.min()<16:return [(int(xs.min()),int(ys.min()))]
 # The first rectangle must contain the topmost nonzero point. Exhaust
 # all such rectangles, then the residual must fit one native tile.
 px,py=int(xs[0]),int(ys[0]);best=None
 for y in range(max(0,py-15),min(py,mask.shape[0]-16)+1):
  for x in range(max(0,px-15),min(px,mask.shape[1]-16)+1):
   keep=~((xs>=x)&(xs<x+16)&(ys>=y)&(ys<y+16));rx,ry=xs[keep],ys[keep]
   if not len(rx):return [(x,y)]
   if rx.max()-rx.min()<16 and ry.max()-ry.min()<16:
    candidate=[(x,y),(int(rx.min()),int(ry.min()))];score=int((~keep).sum())
    if best is None or score>best[0]:best=score,candidate
 return None if best is None else best[1]

def pack_reserved(images):
 patterns=[];records=[]
 for im in images:
  rects=fit(im>0,24)
  if rects is not None and len(rects)>2:
   short=fit_two(im>0)
   if short is not None:rects=short
  if rects is None:raise ValueError('Layer exceeds 24 parts')
  remaining=im.copy();rr=[]
  for left,top in rects:
   patch=remaining[top:top+16,left:left+16].copy();remaining[top:top+16,left:left+16]=0;ys,xs=np.nonzero(patch)
   if not len(xs):continue
   x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1);v=patch[y0:y1,x0:x1];key=(v.shape,v.tobytes());flipped=(v.shape,v[:,::-1].tobytes())
   if key in patterns:k=patterns.index(key);flag=0
   elif flipped in patterns:k=patterns.index(flipped);flag=64
   else:k=len(patterns);patterns.append(key);flag=0
   rr.append([k,left+x0,top+y0,flag])
  records.append(rr)
 if len(patterns)>31:raise ValueError(f'{len(patterns)} patterns exceed31')
 eligible=[k for k,(shape,data)in enumerate(patterns)if shape[1]<16 and not any(r[0]==k and r[3]for rr in records for r in rr)]
 if len(patterns)==31 and not eligible:raise ValueError('No unflipped narrow edge pattern')
 chosen={};used=set()
 if len(patterns)==31:
  k=min(eligible,key=lambda k:patterns[k][0][0]*patterns[k][0][1]);chosen[k]=(16,1);used.add(16)
 for k,(shape,data)in sorted(enumerate(patterns),key=lambda v:v[1][0][1],reverse=True):
  if k in chosen:continue
  t=next(t for t in range(1,32)if t!=16 and t not in used);chosen[k]=(t,0);used.add(t)
 raw=bytes(4096);_,locations,_=indexed_atlas(raw,32);out=bytearray(raw)
 for k,(shape,data)in enumerate(patterns):
  t,pad=chosen[k];v=np.frombuffer(data,np.uint8).reshape(shape)
  for y,x in np.argwhere(v):
   pos,shift=locations[(t//16*16+int(y))*256+t%16*16+int(x)+pad];out[pos]|=int(v[y,x])<<shift
 result=[[(chosen[k][0],x-(16-patterns[k][0][1]if flag else chosen[k][1]),y,flag)for k,x,y,flag in rr]for rr in records]
 return bytes(out),result

def shared_reserved(images):
 parts,which=shared_components(images);nr,rr=pack_reserved(parts);out=[[r for k in ks for r in rr[k]]for ks in which]
 if any(len(q)>24 for q in out):raise ValueError('Component parts exceed24')
 return nr,out,'shared components, eligible narrow unflipped tile16 reserved first'
