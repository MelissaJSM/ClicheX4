"""승리206/207 새 손에 정본85의 사랑이20texel을 강체 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
POSE={206:(-13,-16),207:(-13,-35)}
REMOVE={206:(-14,-19,-9,-10),207:(-15,-38,-9,-28)}
HAND={206:(-14,-12,-10,-8),207:(-16,-31,-10,-27)}
def main():
 a=Archive((N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC').read_bytes());z=a.layer(85)[0];m=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));coords=[(int(x-160),int(y-160),int(z[y,x]))for y,x in np.argwhere(m)];need(len(coords)==20,'정본20texel')
 src=D/'costume_pair_probe_v2';out=D/'canonical_weapon_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for n in(204,205,206,207):
  pair=[];panels=[]
  for form,pal in(('before',16),('after',0)):
   p=src/f'{form}_{n:03}.png';old=np.array(Image.open(p));target=old.copy();case=np.zeros_like(old);rm=np.zeros_like(old,bool);skin=rm.copy()
   if n in POSE:
    gx,tip=POSE[n];x0,y0,x1,y1=REMOVE[n];rm=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)&np.isin(old,range(1,10));x0,y0,x1,y1=HAND[n];skin=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)&np.isin(old,(10,11,12,13))
    for sx,sy,v in coords:case[sx+tip+22+160,sy+gx+10+160]=v
    target[rm]=0;visible=(case>0)&~skin;target[visible]=case[visible];target[skin]=old[skin]
   need(np.array_equal(target[~(rm|(case>0))],old[~(rm|(case>0))]),'새 몸체 보호')
   for tag,v in(('indices',target),('case',case),('removed_mask',rm.astype(np.uint8)*255),('skin_mask',skin.astype(np.uint8)*255)):Image.fromarray(v).save(out/f'{form}_{n:03}_{tag}.png')
   record={'ref':n,'form':form,'body_source':p.relative_to(ROOT).as_posix(),'body_source_sha256':digest(p),'target_sha256':sha(target.tobytes()),'components8':int(label(target>0,np.ones((3,3)))[1]),'new_weapon':n in POSE}
   if n in POSE:record.update(matrix=[[0,1],[1,0]],translation=[gx+10,tip+22],canonical_texels=20,length_native_pixels=8,visible_texels=int(visible.sum()),skin_pixels_preserved=int(skin.sum()),gun_adjacent_to_hand_pixels8=int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum()),source_weapon_removed=[[int(x-160),int(y-160),int(old[y,x])]for y,x in np.argwhere(rm)])
   records.append(record);panels.extend([('new '+form,a.rgba(old,pal)),('canonical '+form,a.rgba(target,pal))]);pair.append(target)
  records[-1]['after_outside_before']=int(((pair[1]>0)&(pair[0]==0)).sum());rows.append((f'weapon {n}',panels))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'canonical_donor_arc_sha256':sha(a.data),'canonical_donor_ref':85,'canonical_texels':coords,'frames':records,'scope':'204/205 빈손 유지,206/207 새 손에8px 정본사랑이 강체정합. 원점·전신·손피부 보존. 최종 미술/패킹 전.','native_packed':False,'runtime_verified':False});print(json.dumps([{k:r.get(k)for k in('ref','form','components8','gun_adjacent_to_hand_pixels8','after_outside_before')}for r in records]))
if __name__=='__main__':main()
