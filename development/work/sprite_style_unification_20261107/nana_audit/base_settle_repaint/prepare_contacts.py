"""새138의 정본 권총·공통손과 같은행 다리 정합을 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def main():
 meta=json.loads((D/'body_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['art_parent_arc']).read_bytes());out=D/'contacts_probe_v1';out.mkdir(exist_ok=False)
 donor=N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC';u=Archive(donor.read_bytes());need(digest(donor)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9','정본부모');z=u.layer(85)[0];mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));coords=[(int(x-160),int(y-160),int(z[y,x]))for y,x in np.argwhere(mask)];need(len(coords)==20,'총20texel');need(np.array_equal(a.words[:15],u.words[:15]),'권총팔레트')
 case=np.zeros_like(z)
 for sx,sy,v in coords:case[sx-9+160,sy+2+160]=v
 bodies={};records=[];rows=[]
 for form,start in(('base',0),('fourth',16)):
  p=D/'body_registered_v1'/f'{form}_138_indices.png';src=np.array(Image.open(p));target=src.copy();skin=(X>=-11)&(X<-4)&(Y>=-27)&(Y<-23)&np.isin(src,(10,11,12,13));rm=(X>=-11)&(X<-4)&(Y>=-32)&(Y<-23)&np.isin(src,range(1,10));target[rm]=0;visible=(case>0)&~skin;target[visible]=case[visible];target[skin]=src[skin]
  need(np.array_equal(target[~(rm|(case>0))],src[~(rm|(case>0))]),'신규몸보존');need(np.array_equal(target[skin],src[skin]),'신규손보존')
  Image.fromarray(target).save(out/f'{form}_138_weapon.png');Image.fromarray(skin.astype(np.uint8)*255).save(out/f'{form}_138_hand.png');Image.fromarray(rm.astype(np.uint8)*255).save(out/f'{form}_138_removed.png');bodies[form]=target
  records.append({'form':form,'source_path':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'generated_weapon_removed':[[int(x-160),int(y-160),int(src[y,x])]for y,x in np.argwhere(rm)],'preserved_skin_pixels':int(skin.sum()),'visible_canonical_pixels':int(visible.sum()),'gun_hand_adjacent8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum()),'components8':int(label(target>0,np.ones((3,3)))[1])})
  rows.append((form+' gun',[('idle',a.composite(0,15 if start else 0)[0]),('new art',a.rgba(src,start)),('20texel case',a.rgba(target,start))]))
 helper.grid(rows,out/'weapon_comparison.png',7);Image.fromarray(case).save(out/'canonical_case.png')
 b,f=bodies['base'],bodies['fourth'];oldf=f.copy();shared=(X>=-11)&(X<-4)&(Y>=-32)&(Y<-23);f[shared]=b[shared]
 # Only missing coverage of this same authored leg/scanline is registered.
 # The basic boot remains intact; no old bitmap or constant-color fill enters.
 source=f.copy();region=(Y>=8)&(Y<=22)&(X>=-16)&(X<=13);links=[];rejected=[]
 for y in range(168,183):
  gaps=spans((b[y]>0)&(f[y]==0)&region[y]);runs=spans((source[y]>0)&region[y]);groups={}
  for gap in gaps:
   need(bool(runs),'동일행 다리표본');sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));groups.setdefault((int(sr[0]),int(sr[-1])),[]).append(gap)
  for(l,r),gs in groups.items():
   lo=min(l,*(int(q[0])for q in gs));hi=max(r,*(int(q[-1])for q in gs));dest=np.arange(lo,hi+1)
   if max(l-lo,hi-r)>2 or len(dest)>max(3,2*(r-l+1)):
    rejected.append({'world_y':y-160,'source':[l-160,r-160],'requested':[lo-160,hi-160]});continue
   sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];f[y,dest]=source[y,sx]
   links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
 full=np.where(f,f,b).astype(np.uint8)
 for name,z in(('base',b),('fourth',f),('full',full)):Image.fromarray(z).save(out/f'{name}_138_indices.png')
 helper.grid([('138 common lower',[('source base',a.rgba(b)),('source Fourth',a.rgba(oldf,16)),('same source contact',a.rgba(f,16)),('actual overlay union',a.rgba(full,16))])],out/'legs_comparison.png',8)
 write(out/'manifest.json',{'art_parent_sha256':sha(a.data),'canonical_donor_path':donor.relative_to(ROOT).as_posix(),'canonical_donor_sha256':digest(donor),'canonical_ref':85,'canonical20':coords,'canonical_transform':{'matrix':[[0,1],[1,0]],'translation':[2,-9]},'frames':records,'common_hand_box':[-11,-32,-4,-23],'fourth_same_leg_source_links':links,'registration_rejected_rows':rejected,'lower_uncovered':int(((b>0)&(f==0)&region).sum()),'total_base_outside_fourth':int(((b>0)&(f==0)).sum()),'scope':'정본권총/새공통손과 같은행 다리표본 정합 비교.미술검토/부분파츠/패킹 전.','native_packed':False,'runtime_verified':False});print(json.dumps({'weapon':records,'links':len(links),'rejected':rejected,'lower_uncovered':int(((b>0)&(f==0)&region).sum())}))
if __name__=='__main__':main()
