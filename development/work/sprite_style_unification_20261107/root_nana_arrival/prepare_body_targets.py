"""Register new authored body pixels, shared grips and semantic armor layers."""
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
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def main():
 parent=W/'root_nana_recoil/packed_recoil03/PL00_U.ARC';a=Archive(parent.read_bytes());assert sha(a.data)=='ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4'
 out=D/'body_targets02';out.mkdir(exist_ok=False);frames=[];rows=[];partial=[]
 for n in(133,135,136,137):
  reg=D/('registered_a01'if n in(133,135)else'registered_b01');b=np.array(Image.open(reg/f'base_{n:03}_indices.png'));f=np.array(Image.open(reg/f'fourth_{n:03}_indices.png'))
  shared={133:[[-15,4],[-8,0],[-5,2],[-7,8],[-15,12]],135:[[-12,-17],[-5,-17],[-3,-9],[-8,-7],[-12,-11]],136:[[-13,-17],[-6,-17],[-4,-9],[-8,-6],[-13,-11]],137:[[-14,-27],[-5,-27],[-5,-21],[-9,-18],[-6,-13],[-9,-12],[-14,-17]]}[n]
  grip=poly(shared);f[grip]=b[grip]
  face=poly([[-7,-19],[-4,-19],[-1,-15],[-1,-10],[-6,-10],[-7,-14]])if n==137 else np.zeros(b.shape,bool)
  f[face]=b[face]
  source=f.copy();links=[]
  for y in range(165,183):
   gaps=spans((b[y]>0)&(f[y]==0));runs=spans(source[y]>0)
   for gap in gaps:
    sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]));assert max(int(sr[0])-lo,hi-int(sr[-1]))<=2
    dest=np.arange(lo,hi+1);assert len(dest)<=max(3,2*len(sr));sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dest))).astype(int)];f[y,dest]=source[y,sx];links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
  inherited=np.argwhere((b>0)&(f==0));own=np.full(b.shape,6,np.uint8)
  if n==133:
   own[Y>=8]=8;own[(X>=4)&(Y>=0)]=8;own[(X>=-8)&(X<=5)&(Y<=1)]=5;own[(X>=5)&(Y<=2)]=5
   own[poly([[2,0],[9,0],[12,11],[5,11],[2,7]])]=7
  else:
   own[(Y>=5)|((X>=7)&(Y>=-11))]=8;own[(X>=-9)&(X<=8)&(Y<=-7)]=5;own[(X>=8)&(Y<=-10)]=5
   own[poly([[1,-9],[9,-6],[11,4],[6,7],[2,2]])]=7
  # The rear hood/veil belongs to head armor; otherwise legs-only
  # equipment exposes an isolated black wedge behind the bare beret.
  if n!=133:own[(X>=7)&(Y<=4)]=5
  own[grip]=7;own[face]=5
  full=np.where(f,f,b).astype(np.uint8);diff=((full!=b)|(np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]&(f>0)))&(full>0)
  ls={0:b,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  expected=a.rgba(b);expected.alpha_composite(a.rgba(f,16));assert composite(a,ls,15,1).tobytes()==expected.tobytes()
  checks=[{'mask':mask,'arm':arm,'components8':int(label(np.array(composite(a,ls,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(own).save(out/f'owner_{n:03}.png');Image.fromarray(f).save(out/f'fourth_body_{n:03}.png')
  frames.append({'ref':n,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'shared_grip_polygon':shared,'shared_face_polygon':n==137,'same_row_new_leg_registration':links,'new_base_shared_outer_pixels':[[int(x-160),int(y-160),int(b[y,x])]for y,x in inherited],'partial_components':checks})
  rows.append((f'arrival {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))]));partial.append((f'parts {n}',[(name,composite(a,ls,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6);helper.grid(partial[i:i+2],out/f'partial_{i//2+1}.png',5)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'refs':[133,135,136,137],'frames':frames,'effects_restored':False,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'frames':len(frames),'components':{str(q['ref']):sorted(set(t['components8']for t in q['partial_components']))for q in frames}}))
if __name__=='__main__':main()
