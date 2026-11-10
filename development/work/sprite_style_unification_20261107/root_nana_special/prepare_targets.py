"""Register new special-pose contacts and retain native equipment ownership."""
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
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 m=read(D/'inputs01/manifest.json');a=Archive((ROOT/m['parent_arc']).read_bytes());assert sha(a.data)==m['parent_sha256']
 out=D/'joint_layers04';out.mkdir(exist_ok=False);rows=[];partials=[];frames=[];proof=[]
 donor=N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC';u=Archive(donor.read_bytes());assert sha(u.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
 z=u.layer(85)[0];gunmask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));gun=np.where(gunmask,z,0).astype(np.uint8);assert np.count_nonzero(gun)==20
 assert np.array_equal(u.words[:15],a.words[:15])
 for n in(95,98):
  bodies={};records=[]
  for form in('base','fourth'):
   p=D/'registered01'/f'{form}_{n:03}_indices.png';z=np.array(Image.open(p));src=z.copy();start,end=(177,181)if n==95 else(179,184)
   z[start-1:end]=0;z[start-1:end-1]=src[start:end]
   assert np.nonzero(z)[0].max()==(179 if n==95 else 182)
   records.append({'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p.read_bytes()),'shoe_source_rows':[start,end],'shoe_destination_rows':[start-1,end-1]})
   bodies[form]=z
  b,f=bodies['base'],bodies['fourth']
  # 95 holds the source-authored pistol diagonally without firing. Use the
  # exact same new gun/hand module for both costumes; do not synthesize a
  # 45-degree weapon by stretching its horizontal pixels.
  if n==95:
   shared=poly([[-20,-2],[-12,-10],[-7,-7],[-15,1]])
   f[shared]=b[shared];weapon={'policy':'95 비발사 사선총은 새 기본 원화의 총·손을 두 의상에 그대로 등록','shared_module_polygon':[[-20,-2],[-12,-10],[-7,-7],[-15,1]],'new_source_only':True}
  else:
   case=np.roll(np.roll(gun,-3,1),1,0) # Same historical muzzle (-25,-9).
   weapon={'policy':'98 수평발사 총열·그립은 수용85의20texel/8px를 강체이동','donor_arc':donor.relative_to(ROOT).as_posix(),'donor_arc_sha256':sha(u.data),'donor_ref':85,'translation':[-3,1],'canonical_texels':20}
   for form,z in bodies.items():
    original=z.copy();skin=(X>=-23)&(X<=-18)&(Y>=-8)&(Y<=-3)&np.isin(z,(10,11,12,13));rm=(X>=-27)&(X<=-18)&(Y>=-11)&(Y<=-3)&((Y<=-7)|(X<=-22))&np.isin(z,range(1,10));z[rm]=0;visible=(case>0)&~skin;z[visible]=case[visible];z[skin]=original[skin]
    assert np.array_equal(z[~(rm|(case>0))],original[~(rm|(case>0))])
    records.append({'form':form,'gun_removed':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(rm)],'preserved_skin':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(skin)],'visible_case_texels':int(visible.sum()),'case_hand_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())})
   # Hands and sleeve cuffs have the same source shape in both costumes.
   shared=(X>=-27)&(X<=-16)&(Y>=-11)&(Y<=-2);f[shared]=b[shared]
  # Match boot/bare-leg coverage only in the lower limbs. Each added texel
  # is sampled from the same new-art row; no old body or flat fill is used.
  links=[];source=f.copy();low=3 if n==95 else 10
  region=(Y>=low)&(Y<=22)&(X>=-18)&(X<=16)
  for y in range(160+low,183):
   gaps=spans((b[y]>0)&(f[y]==0)&region[y]);runs=spans((source[y]>0)&region[y]);groups={}
   for gap in gaps:
    assert runs,('no authored leg',n,y-160)
    sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));groups.setdefault((int(sr[0]),int(sr[-1])),[]).append(gap)
   for(l,r),gs in groups.items():
    lo=min(l,*(int(q[0])for q in gs));hi=max(r,*(int(q[-1])for q in gs));dest=np.arange(lo,hi+1)
    assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1)),('registration bound',n,y-160,l-160,r-160,lo-160,hi-160)
    sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];f[y,dest]=source[y,sx]
    links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
  assert not np.any((b>0)&(f==0)&region)
  own=np.full(b.shape,6,np.uint8)
  if n==95:
   own[(Y>=-1)|((X>=7)&(Y>=-15))]=8
   own[poly([[-20,1],[-7,-13],[-3,-10],[-9,-1]])]=7
   own[poly([[7,-10],[18,-9],[19,-1],[8,-1]])]=7
   # The lower neck row belongs to the torso. This preserves every authored
   # texel and places the actual 16x16 head in one native part record.
   own[(Y<-14)&(X>=-9)&(X<7)]=5
   own[poly([[6,-25],[10,-22],[14,-17],[17,-10],[18,2],[7,2],[7,-13]])]=8
  else:
   own[(Y>=6)|((X>=9)&(Y>=1))]=8
   own[poly([[-28,-12],[-15,-12],[-3,-5],[-3,1],[-16,-2],[-27,-2]])]=7
   own[poly([[4,-5],[16,-10],[22,-10],[22,0],[7,2]])]=7
   own[poly([[-9,-20],[7,-20],[12,-9],[8,-5],[-9,-4]])]=5
   own[poly([[8,-6],[12,-4],[16,-3],[20,-2],[20,9],[8,10],[5,-1]])]=8
  full=np.where(f,f,b).astype(np.uint8);pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[full];different=((full!=b)|((f>0)&pc))&(full>0)
  ls={0:b,**{pb:np.where(different&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  expect=a.rgba(b);expect.alpha_composite(a.rgba(f,16));assert composite(a,ls,15,1).tobytes()==expect.tobytes()
  for n2,dx in((n,0),(n+1,1)):
   layers={pb:np.roll(z,dx,1)for pb,z in ls.items()}
   for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{n2:03}.png')
   Image.fromarray(np.roll(own,dx,1)).save(out/f'owner_{n2:03}.png')
   frames.append({'ref':n2,'source_ref':n,'translation':[dx,0],'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in layers.items()},'components':[{'mask':mask,'arm':arm,'count':int(label(np.array(composite(a,layers,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]})
   rows.append((f'special {n2}',[('base idle',a.composite(0)[0]),('new base',composite(a,layers,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,layers,15))]))
   partials.append((f'partial {n2}',[(name,composite(a,layers,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
  proof.append({'ref':n,'contact_registration':records,'weapon':weapon,'leg_registration':links,'new_base_visible_outside_fourth':int(((b>0)&(f==0)).sum())})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6);helper.grid(partials[i:i+2],out/f'partial_{i//2+1}.png',5)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':m['parent_arc'],'parent_sha256':m['parent_sha256'],'refs':[95,96,98,99],'frames':frames,'source_registration':proof,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'refs':[95,96,98,99],'component_issues':[{'ref':q['ref'],'issues':[c for c in q['components']if c['count']>1]}for q in frames if any(c['count']>1 for c in q['components'])]}))
if __name__=='__main__':main()
