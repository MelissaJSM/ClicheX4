"""Register authored recoil art and native equipment ownership, with provenance."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
Y,X=np.indices((384,384));Y-=160;X-=160
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def spans(row):
 xs=np.flatnonzero(row);return [] if not len(xs) else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 m=read(D/'inputs01/manifest.json');old=Archive((ROOT/m['parent_arc']).read_bytes());parent=N/'base_settle_repaint/packed_settle_candidate_v1/PL00_U.ARC';a=Archive(parent.read_bytes());assert sha(a.data)=='15d01f06aee14e3264d7ce41d1358a530147e4a3464d3ac949b64cde5085a775'
 for n in (90,91):
  for pb in (0,5,6,7,8):assert np.array_equal(old.layer(n,pb)[0],a.layer(n,pb)[0])
 out=D/'joint_layers02';out.mkdir(exist_ok=False);rows=[];partials=[];frames=[];proof=[]
 donor=N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC';u=Archive(donor.read_bytes());assert sha(u.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
 z=u.layer(85)[0];gunmask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));gun=np.where(gunmask,z,0).astype(np.uint8);assert np.count_nonzero(gun)==20
 for n in (90,91):
  b=np.array(Image.open(D/'registered01'/f'base_{n:03}_indices.png'));f=np.array(Image.open(D/'registered01'/f'fourth_{n:03}_indices.png'));weapon={}
  if n==90:
   shared=poly([[-22,-20],[-14,-20],[-11,-13],[-14,-9],[-18,-11]])
   f[shared]=b[shared];weapon={'method':'new angled base gun and hand shared identically into Fourth','polygon':[[-22,-20],[-14,-20],[-11,-13],[-14,-9],[-18,-11]]}
  else:
   # Original ref91's horizontal muzzle is two pixels left of accepted85.
   case=np.roll(gun,-2,1);records=[]
   for form,z in (('base',b),('fourth',f)):
    original=z.copy();skin=(X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(z,(10,11,12,13));rm=(X>=-25)&(X<=-17)&(Y>=-13)&(Y<=-7)&((Y<=-10)|(X<=-20))&np.isin(z,range(1,10));z[rm]=0;vis=(case>0)&~skin;z[vis]=case[vis];z[skin]=original[skin]
    records.append({'form':form,'removed':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(rm)],'skin_preserved':int(skin.sum()),'gun_hand_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())})
   shared=(X>=-25)&(X<=-16)&(Y>=-13)&(Y<=-5);f[shared]=b[shared]
   weapon={'method':'accepted85 canonical20-texel pistol translated x-2, same hand across outfits','donor_arc':donor.relative_to(ROOT).as_posix(),'donor_sha256':sha(u.data),'ref':85,'translation':[-2,0],'registrations':records}
  source=f.copy();region=(Y>=8)&(Y<=22)&(X>=-18)&(X<=16);links=[]
  for y in range(168,183):
   gaps=spans((b[y]>0)&(f[y]==0)&region[y]);runs=spans((source[y]>0)&region[y]);groups={}
   for gap in gaps:
    assert runs,('no new leg',n,y-160);sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));groups.setdefault((int(sr[0]),int(sr[-1])),[]).append(gap)
   for (l,r),gs in groups.items():
    lo=min(l,*(int(q[0])for q in gs));hi=max(r,*(int(q[-1])for q in gs));dest=np.arange(lo,hi+1);assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1)),('leg bound',n,y-160,l-160,r-160,lo-160,hi-160)
    sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];f[y,dest]=source[y,sx];links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
  own=np.full(b.shape,6,np.uint8);own[(Y>=5)|((X>=7)&(Y>=-15))]=8
  own[poly([[-24,-21],[-13,-21],[-9,-12],[-3,-7],[-4,-2],[-17,-7]]) if n==90 else poly([[-26,-14],[-15,-14],[-11,-9],[-3,-8],[-3,-2],[-16,-4],[-22,-6]])]=7
  own[poly([[3,-8],[12,-7],[14,6],[7,8],[3,2]])]=7
  own[(X>=-9)&(X<=6)&(Y>=-21)&(Y<=-6)]=5
  # The source veil behind the head belongs to the head upper edge and legs below.
  own[(X>=7)&(Y<=-16)]=5
  own[(X>=7)&(X<=13)&(Y>=-15)&(Y<=-9)]=5
  own[shared]=7
  full=np.where(f,f,b).astype(np.uint8);pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];different=((full!=b)|((f>0)&pc))&(full>0)
  ls={0:b,**{pb:np.where(different&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}};expect=a.rgba(b);expect.alpha_composite(a.rgba(f,16));assert composite(a,ls,15,1).tobytes()==expect.tobytes()
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(own).save(out/f'owner_{n:03}.png')
  frames.append({'ref':n,'source_ref':n,'body_translation':[0,0],'bbox_rescaled':False,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'components':[{'mask':mask,'arm':arm,'count':int(label(np.array(composite(a,ls,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]})
  proof.append({'ref':n,'weapon':weapon,'leg_registration':links})
  rows.append((f'recoil {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))]));partials.append((f'partial {n}',[(name,composite(a,ls,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
 helper.grid(rows,out/'comparison.png',6);helper.grid(partials,out/'partial.png',5)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'source_parent_sha256':m['parent_sha256'],'selected_source_layers_unchanged_after_rebase':True,'refs':[90,91],'frames':frames,'source_registration':proof,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'refs':[90,91],'components':[sorted(set(c['count']for c in q['components']))for q in frames]}))
if __name__=='__main__':main()
