"""수용된 사랑이의 총열/그립20texel만 90도 강체 등록하는 비교 후보."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
REFS=(100,101,102,103,104,231)
TOP={100:-19,101:-38,102:-32,103:-27,104:-36,231:-28}
MUZZLE_X={100:-12,101:-9,102:-9,103:9,104:7,231:-9}
HAND_BOX={100:(-14,-14,-7,-9),101:(-14,-34,-6,-29),102:(-14,-28,-6,-23),103:(5,-21,13,-16),104:(4,-31,12,-24),231:(-14,-25,-6,-20)}
def source(form,n):
 if form=='fourth'and n in(101,102,231):return D/f'leg_edges_registered_v1/fourth_{n:03}_indices.png'
 page='charge'if n in(100,101)else'air'if n in(103,104)else'recovery_ground'
 return D/f'{page}_registered_v1/{form}_{n:03}_indices.png'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='canonical_weapon_probe_v1');ap.add_argument('--air104-down-one',action='store_true');args=ap.parse_args()
 p=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC';u=Archive(p.read_bytes());need(digest(p)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9','Frozen donor');a=Archive((N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes());out=D/args.out;out.mkdir(exist_ok=False)
 z=u.layer(85)[0];mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));coords=[(int(x-160),int(y-160),int(z[y,x]))for y,x in np.argwhere(mask)];need(len(coords)==20,'Proven source case');need(np.array_equal(u.words[:15],a.words[:15]),'Canonical palette')
 Image.fromarray(np.where(mask,z,0).astype(np.uint8)).save(out/'canonical85_only.png');records=[];rows=[]
 for n in REFS:
  panels=[]
  for form in('base','fourth'):
   p=source(form,n);old=np.array(Image.open(p));start=16 if form=='fourth'else 0;x0,y0,x1,y1=HAND_BOX[n]
   skin=np.isin(old,(10,11,12,13))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);yy,xx=np.nonzero(skin);need(len(xx)>0,'New source fingers');hand_top=int(yy.min()-160)
   # At these isolated upper pistol positions the window excludes the head;
   # only generated gun-colored texels before the first finger row are used.
   gx,top=MUZZLE_X[n],TOP[n]+int(n==104 and args.air104_down_one);remove=(X>=gx-4)&(X<=gx+3)&(Y>=top-2)&(Y<=hand_top)&np.isin(old,range(1,10))
   # Base104 has a one-row dark grip below its new long barrel. It remains
   # source-authored behind the new canonical gun, not imported old clothing.
   target=old.copy();target[remove]=0;case=np.zeros_like(old)
   for sx,sy,v in coords:
    tx=-sy+(gx-9);ty=sx+(top+22);case[ty+160,tx+160]=v
   visible=(case>0)&~skin;target[visible]=case[visible];target[skin]=old[skin]
   outside=~(remove|(case>0));need(np.array_equal(target[outside],old[outside]),'Other body');need(np.array_equal(target[skin],old[skin]),'Fingers');comps=int(label(target>0,np.ones((3,3)))[1])
   Image.fromarray(target).save(out/f'{form}_{n:03}_indices.png');Image.fromarray(case).save(out/f'{form}_{n:03}_case.png');Image.fromarray(remove.astype(np.uint8)*255).save(out/f'{form}_{n:03}_removed_mask.png')
   panels.extend([('new '+form,a.rgba(old,start)),('same 8px case '+form,a.rgba(target,start))]);records.append({'ref':n,'form':form,'source_body':p.relative_to(ROOT).as_posix(),'source_body_sha256':digest(p),'old_muzzle_world':[gx,top],'rotation':'(x,y) -> (-y,x)','translation':[gx-9,top+22],'case_source_pixels':20,'case_vertical_extent':8,'hand_pixels_preserved':int(skin.sum()),'generated_weapon_removed':[(int(x-160),int(y-160),int(old[y,x]))for y,x in np.argwhere(remove)],'source_case_visible_pixels':int(visible.sum()),'body_components_8':comps,'new_sha256':sha(target.tobytes()),'candidate_only':True})
  rows.append((f'Rising {n}',panels))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'donor_arc_sha256':sha(u.data),'parent_arc_sha256':sha(a.data),'donor_ref':85,'canonical_source_texels':coords,'canonical_sha256':sha(z[mask].tobytes()),'frames':records,'air104_one_pixel_down':args.air104_down_one,'scope':'기존 수용85의 실제 총열/그립20texel만 90도 회전, 크기 변경 없이 8px 길이로 등록. 새 손/팔/몸체/머리 보존을 비교하는 미채택 후보. 일반공중은 새 오른손 쪽, 차지/지상은 원래 왼손 쪽이다.','native_packed':False,'runtime_verified':False,'art_accepted':False});print(json.dumps({f'{r["form"]}/{r["ref"]}':r['body_components_8']for r in records}))
if __name__=='__main__':main()
