"""Register authored poses and costume ownership without replacing pose detail."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();Y,X=np.indices((384,384));Y-=160;X-=160
def poly(pts):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in pts],fill=1);return np.array(im)>0
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 parent=W/'root_nana_arrival/packed_arrival01/PL00_U.ARC';a=Archive(parent.read_bytes());assert sha(a.data)=='9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91'
 out=D/'joint_targets01';out.mkdir(exist_ok=False);frames=[];rows=[];partial=[]
 for n in(204,205,206,207):
  reg=D/('registered_a01'if n in(204,205)else 'registered_206_03'if n==206 else 'registered_b01')
  b=np.array(Image.open(reg/f'base_{n:03}_indices.png'));f=np.array(Image.open(reg/f'fourth_{n:03}_indices.png'))
  shift=[0,0]
  if n==207:
   assert not b[:5].any()and not f[:5].any();b=np.roll(b,-5,axis=0);f=np.roll(f,-5,axis=0);shift=[0,-5]
  shared={204:[[-14,-6],[-3,-6],[-3,2],[-14,2]],205:[[-15,-18],[-5,-18],[-5,-8],[-15,-8]],206:[[-14,-21],[-8,-21],[-8,-8],[-14,-8]],207:[[-15,-39],[-7,-39],[-7,-23],[-15,-23]]}[n]
  grip=poly(shared);f[grip]=b[grip]
  face_pts=([[-8,-23],[-1,-23],[-1,-13],[-8,-13]]if n==207 else [[-7,-17],[1,-17],[1,-9],[-7,-9]])
  face=poly(face_pts);f[face]=b[face]
  source=f.copy();links=[]
  for y in range(164 if n==207 else 165,183):
   gaps=spans((b[y]>0)&(f[y]==0));runs=spans(source[y]>0)
   for gap in gaps:
    assert runs,('No new costume leg source',n,y)
    sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]))
    assert max(int(sr[0])-lo,hi-int(sr[-1]))<=3,('Leg correction exceeds3px',n,y,lo,hi,sr.tolist())
    dest=np.arange(lo,hi+1);assert len(dest)<=max(3,2*len(sr)),('Leg stretch exceeds2x',n,y)
    sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dest))).astype(int)];f[y,dest]=source[y,sx]
    links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
  inherited=np.argwhere((b>0)&(f==0));own=np.full(b.shape,6,np.uint8)
  own[(Y>=5)|((X>=7)&(Y>=-10))]=8
  own[(Y<=(-12 if n==207 else -7))&(X>=-9)]=5
  own[(X>=7)&(Y<=4)]=5
  own[poly([[1,-13 if n==207 else -9],[9,-9 if n==207 else -6],[11,3],[6,6],[1,0]])]=7
  own[grip]=7;own[face]=5
  full=np.where(f,f,b).astype(np.uint8)
  diff=((full!=b)|(np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]&(f>0)))&(full>0)
  ls={0:b,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  expected=a.rgba(b);expected.alpha_composite(a.rgba(f,16));assert composite(a,ls,15,1).tobytes()==expected.tobytes()
  checks=[{'mask':mask,'arm':arm,'components8':int(label(np.array(composite(a,ls,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(own).save(out/f'owner_{n:03}.png');Image.fromarray(f).save(out/f'fourth_body_{n:03}.png')
  frames.append({'ref':n,'source_registration':reg.relative_to(ROOT).as_posix(),'rigid_translation':shift,'bbox_rescale':False,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'shared_grip_polygon':shared,'shared_face_polygon':face_pts,'same_row_new_leg_registration':links,'new_base_shared_outer_pixels':[[int(x-160),int(y-160),int(b[y,x])]for y,x in inherited],'partial_components':checks})
  rows.append((f'victory {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))]))
  partial.append((f'parts {n}',[(name,composite(a,ls,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6);helper.grid(partial[i:i+2],out/f'partial_{i//2+1}.png',5)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'refs':[204,205,206,207],'frames':frames,'native_packed':False,'runtime_verified':False},indent=2)+'\n','utf8')
 print(json.dumps({'frames':len(frames),'components':{str(q['ref']):sorted(set(t['components8']for t in q['partial_components']))for q in frames}}))
if __name__=='__main__':main()
