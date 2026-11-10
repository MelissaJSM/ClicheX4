"""새 등장 손에 수용된 85의20texel 권총만 강체 등록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
# (barrel column x, muzzle-extreme y). Matrices do not rescale any texel.
POSE={133:('down',-20,18),135:('up',-14,-13),136:('up',-15,-16),137:('up',-16,-27),138:('up',-14,-33)}
REMOVE={133:(-23,12,-14,20),135:(-15,-12,-8,-6),136:(-16,-14,-8,-8),137:(-17,-27,-9,-19),138:(-15,-34,-7,-27)}
HAND={133:(-18,9,-13,14),135:(-13,-6,-8,-2),136:(-14,-8,-9,-4),137:(-15,-19,-10,-14),138:(-14,-27,-8,-23)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='canonical_cases_probe_v1');ap.add_argument('--geometry',choices=['v1','v2'],default='v1');args=ap.parse_args();poses=POSE if args.geometry=='v1'else{133:('down',-18,17),135:('up',-13,-11),136:('up',-14,-14),137:('up',-14,-25),138:('up',-12,-32)};out=D/args.out;out.mkdir(exist_ok=False);a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());z=a.layer(85)[0];mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));coords=[(int(x-160),int(y-160),int(z[y,x]))for y,x in np.argwhere(mask)];need(len(coords)==20,'정본20texel');records=[];rows=[]
 Image.fromarray(np.where(mask,z,0).astype(np.uint8)).save(out/'canonical85_indices.png')
 for n,(direction,gx,tip)in poses.items():
  panels=[];pair=[]
  for form,pal in(('before',16),('after',0)):
   p=D/(f'pistol_hands_registered_v1/{form}_{n:03}_local.png'if n!=138 else f'settle_pair_probe_v1/{form}_{n:03}.png');old=np.array(Image.open(p));rx0,ry0,rx1,ry1=REMOVE[n];rm=(X>=rx0)&(X<rx1)&(Y>=ry0)&(Y<ry1)&np.isin(old,range(1,10));hx0,hy0,hx1,hy1=HAND[n];skin=(X>=hx0)&(X<hx1)&(Y>=hy0)&(Y<hy1)&np.isin(old,(10,11,12,13));case=np.zeros_like(old)
   for sx,sy,v in coords:
    tx=sy+(gx+10);ty=(sx+(tip+22))if direction=='up'else(-sx+(tip-22));case[ty+160,tx+160]=v
   target=old.copy();target[rm]=0;visible=(case>0)&~skin;target[visible]=case[visible];target[skin]=old[skin];need(np.array_equal(target[~(rm|(case>0))],old[~(rm|(case>0))]),'신규몸 보존');need(np.array_equal(target[skin],old[skin]),'손가락 보존')
   for tag,v in(('indices',target),('case',case),('removed_mask',rm.astype(np.uint8)*255),('skin_mask',skin.astype(np.uint8)*255)):Image.fromarray(v).save(out/f'{form}_{n:03}_{tag}.png')
   comps=int(label(target>0,np.ones((3,3)))[1]);touch=int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum());records.append({'ref':n,'form':form,'body_source':p.relative_to(ROOT).as_posix(),'body_sha256':digest(p),'direction':direction,'matrix':[[0,1],[1 if direction=='up'else-1,0]],'translation':[gx+10,tip+22 if direction=='up'else tip-22],'canonical_texels':20,'visible_texels':int(visible.sum()),'length_native_pixels':8,'skin_pixels_preserved':int(skin.sum()),'gun_adjacent_to_hand_pixels8':touch,'source_weapon_removed':[[int(x-160),int(y-160),int(old[y,x])]for y,x in np.argwhere(rm)],'components8':comps,'target_sha256':sha(target.tobytes())});panels.extend([('new '+form,a.rgba(old,pal)),('8px module '+form,a.rgba(target,pal))]);pair.append(target)
  rows.append((f'case {n}',panels));records[-1]['after_outside_before']=int(((pair[1]>0)&(pair[0]==0)).sum())
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'donor_arc_sha256':sha(a.data),'donor_ref':85,'canonical_source_texels':coords,'frames':records,'scope':'최초권총 방향을새손에서정본85의20texel·8px모듈로정합하는후보.신규몸/손피부보존,공통손/부분층/패킹검증전.','native_packed':False,'runtime_verified':False});print(json.dumps([{k:r.get(k)for k in('ref','form','components8','gun_adjacent_to_hand_pixels8','after_outside_before')}for r in records]))
if __name__=='__main__':main()
