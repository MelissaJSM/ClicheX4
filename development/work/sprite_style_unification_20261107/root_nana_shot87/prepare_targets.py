"""Register shared new face/hands and fit the existing layered-armor coverage."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();Y,X=np.indices((384,384));Y-=160;X-=160;PBS=(0,5,6,7,8)
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,m,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
  if m&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 parent=W/'root_nana_shot85/packed_shot01/PL00_U.ARC';a=Archive(parent.read_bytes());assert sha(a.data)=='d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61'
 out=D/'joint_targets02';out.mkdir(exist_ok=False);frames=[];proof=[]
 for n in (87,92):
  b=np.array(Image.open(D/'registered01'/f'base_{n:03}_indices.png'));f=np.array(Image.open(D/'registered01'/f'fourth_{n:03}_indices.png'))
  face=(X>=-7)&(X<=1)&(Y>=-16)&(Y<=-8);f[face]=b[face]
  hand=(X>=-18)&(X<=-8)&(Y>=0)&(Y<=7)if n==87 else (X>=6)&(X<=12)&(Y>=0)&(Y<=6)
  f[hand]=b[hand]
  source=f.copy();links=[]
  for y in range(168,183):
   for gap in spans((b[y]>0)&(f[y]==0)):
    runs=spans(source[y]>0);assert runs,('No leg source',n,y)
    sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]))
    assert max(int(sr[0])-lo,hi-int(sr[-1]))<=2,('Leg limit',n,y,lo,hi)
    dest=np.arange(lo,hi+1);assert len(dest)<=max(3,2*len(sr));sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dest))).astype(int)]
    f[y,dest]=source[y,sx];links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
  full=np.where(f,f,b).astype(np.uint8);own=np.full(b.shape,6,np.uint8)
  own[(Y>=5)|((X>=7)&(Y>=-8))]=8
  own[(Y<=-6)&(X>=-10)]=5
  own[(X<=-5)&(Y>=-5)&(Y<=5)]=7
  own[(X>=5)&(X<=12)&(Y>=-5)&(Y<=6)]=7
  own[(X>=12)&(Y>=-7)&(Y<=6)]=5
  own[face]=5;own[hand]=7
  diff=((full!=b)|np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full])&(full>0)
  ls={0:b,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
  expected=a.rgba(b);expected.alpha_composite(a.rgba(full,16));assert composite(a,ls,15,1).tobytes()==expected.tobytes()
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(own).save(out/f'owner_{n:03}.png')
  components=[{'mask':m,'arm':arm,'count':int(label(np.array(composite(a,ls,m,arm))[:,:,3]>0,np.ones((3,3)))[1])}for m in range(16)for arm in(1,2)]
  frames.append({'ref':n,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'components':components})
  proof.append({'ref':n,'shared_new_hand_bbox':[-18,0,-7,8]if n==87 else[6,0,13,7],'shared_face_bbox':[-7,-16,2,-7],'leg_registration':links,'body_translation':[0,0],'bbox_rescale':False,'all_source_art_new':True})
  helper.grid([(f'settle {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))])],out/f'comparison_{n}.png',6)
  helper.grid([(f'parts {n}',[(name,composite(a,ls,m))for name,m in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))])],out/f'partial_{n}.png',5)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'refs':[87,92],'frames':frames,'source_registration':proof,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'components':{q['ref']:sorted({c['count']for c in q['components']})for q in frames}}))
if __name__=='__main__':main()
