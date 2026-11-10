"""Keep the accepted Sarang module and native muzzle while registering new clothing."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
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
 parent=W/'root_nana_vehicle/packed_vehicle03/PL00_U.ARC';a=Archive(parent.read_bytes());assert sha(a.data)=='29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db'
 donor=W/'nana_audit/ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC';u=Archive(donor.read_bytes());assert sha(u.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
 z=u.layer(85)[0];mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));gun=np.where(mask,z,0).astype(np.uint8);assert np.count_nonzero(gun)==20
 out=D/'joint_targets03';out.mkdir(exist_ok=False);frames=[];proof=[]
 for n in (85,86):
  b=np.array(Image.open(D/'registered01'/f'base_{n:03}_indices.png'));f=np.array(Image.open(D/'registered01'/f'fourth_{n:03}_indices.png'));case=np.roll(gun,n-85,1);registrations=[]
  for form,z in (('base',b),('fourth',f)):
   old=z.copy();skin=(X>=-20)&(X<=-13)&(Y>=-10)&(Y<=-6)&np.isin(z,(10,11,12,13))
   rm=(X>=-24)&(X<=-15)&(Y>=-13)&(Y<=-8)&np.isin(z,range(1,10));z[rm]=0;visible=(case>0)&~skin;z[visible]=case[visible];z[skin]=old[skin]
   registrations.append({'form':form,'removed_new_gun_cells':[[int(x-160),int(y-160),int(old[y,x])]for y,x in np.argwhere(rm)],'visible_canonical_cells':int(visible.sum()),'skin_cells':int(skin.sum()),'gun_skin_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())})
  hand=(case>0)|((X>=-20)&(X<=-13)&(Y>=-10)&(Y<=-6)&np.isin(b,(10,11,12,13)));f[hand]=b[hand]
  face=(X>=-7)&(X<=1)&(Y>=-16)&(Y<=-8);f[face]=b[face]
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
  own[(X<=-5)&(Y>=-12)&(Y<=-1)]=7
  own[(X>=5)&(X<=14)&(Y>=-5)&(Y<=4)]=7
  own[(X>=13)&(Y>=-6)&(Y<=-3)]=5
  own[face]=5;own[hand]=7
  diff=((full!=b)|np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full])&(full>0)
  ls={0:b,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
  expected=a.rgba(b);expected.alpha_composite(a.rgba(full,16));assert composite(a,ls,15,1).tobytes()==expected.tobytes()
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(own).save(out/f'owner_{n:03}.png')
  components=[{'mask':m,'arm':arm,'count':int(label(np.array(composite(a,ls,m,arm))[:,:,3]>0,np.ones((3,3)))[1])}for m in range(16)for arm in(1,2)]
  frames.append({'ref':n,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'components':components})
  proof.append({'ref':n,'canonical_gun_sha256':sha(gun.tobytes()),'gun_translation':[n-85,0],'gun_registration':registrations,'shared_new_hand_cells':int(hand.sum()),'shared_face_bbox':[-7,-16,2,-7],'leg_registration':links})
  helper.grid([(f'shot {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))])],out/f'comparison_{n}.png',6)
  helper.grid([(f'parts {n}',[(name,composite(a,ls,m))for name,m in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))])],out/f'partial_{n}.png',5)
 report={'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'refs':[85,86],'frames':frames,'source_registration':proof,'gun_donor':donor.relative_to(ROOT).as_posix(),'gun_donor_sha256':sha(u.data),'native_packed':False,'runtime_verified':False}
 (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'components':{q['ref']:sorted({c['count']for c in q['components']})for q in frames},'contacts':[[r['gun_skin_contact8']for r in p['gun_registration']]for p in proof]}))
if __name__=='__main__':main()
