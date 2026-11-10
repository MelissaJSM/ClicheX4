"""새 승리 머리·다리와 새 맨팔 의상 영역을 의미 경계로 공유한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from semantic_grids import source
POLYS={
 204:[(-6,-9),(-3,-9),(-1,-9),(2,-9),(4,-7),(6,-4),(8,-2),(9,0),(9,2),(6,4),(2,5),(1,5),(-1,4),(-4,5),(-7,6),(-9,5),(-11,3),(-13,1),(-14,-2),(-13,-4),(-10,-6),(-7,-7)],
 205:[(-16,-16),(-12,-16),(-11,-13),(-9,-11),(-7,-9),(-5,-8),(-2,-9),(2,-9),(4,-7),(6,-3),(8,-1),(9,1),(8,3),(5,4),(2,5),(0,5),(-3,4),(-6,5),(-9,5),(-10,3),(-9,0),(-8,-5),(-10,-7),(-12,-8),(-14,-10),(-15,-12),(-16,-14)],
 206:[(-16,-9),(-12,-9),(-11,-7),(-9,-7),(-7,-8),(-5,-8),(-2,-9),(2,-9),(4,-6),(6,-3),(8,-1),(8,2),(5,3),(2,5),(0,5),(-3,4),(-6,5),(-9,5),(-10,2),(-10,0),(-13,-1),(-15,-3),(-16,-5)],
 207:[(-14,-27),(-11,-27),(-9,-24),(-8,-20),(-7,-16),(-7,-12),(-6,-10),(-4,-9),(-1,-9),(2,-9),(4,-6),(6,-3),(8,-1),(8,2),(5,3),(2,5),(0,5),(-3,4),(-6,5),(-9,5),(-11,2),(-11,0),(-10,-4),(-9,-8),(-11,-10),(-12,-14),(-13,-17),(-14,-21)]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['v1','v2'],default='v2');args=ap.parse_args()
 a=Archive((N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC').read_bytes());out=D/f'costume_pair_probe_{args.version}';out.mkdir(exist_ok=False);records=[];rows=[]
 for n,points in POLYS.items():
  bp,ap=source('before',n),source('after',n);b=np.array(Image.open(bp));donor=np.array(Image.open(ap));common=b.copy();common[b==15]=13
  im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);m=np.array(im)>0
  hair_excluded=[]
  if args.version=='v2'and n in(204,207):
   x,y=(-13,-4)if n==204 else(-10,-4);need(donor[y+160,x+160]==5 and b[y+160,x+160]==0,'후폼 옆머리 의미표본');m[y+160,x+160]=False;hair_excluded=[[x,y,5]]
  after=common.copy();after[m]=donor[m];outside=(after>0)&(b==0)
  need(np.array_equal(after[~m],common[~m]),'새 머리/다리 공통부 보존')
  for tag,z in(('before',b),('after',after),('donor',donor),('costume_mask',m.astype(np.uint8)*255),('outside_mask',outside.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{tag}_{n:03}.png')
  records.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(ROOT).as_posix(),'after_source_sha256':digest(ap),'costume_polygon':points,'common_gray15_to_after13_count':int((b==15).sum()),'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes()),'new_outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in np.argwhere(outside)],'components_before':int(label(b>0,np.ones((3,3)))[1]),'components_after':int(label(after>0,np.ones((3,3)))[1]),'alpha_clipped':False,'old_pixels_copied':0})
  records[-1]['after_hair_excluded_from_costume']=hair_excluded
  rows.append((f'costume {n}',[('new jacket',a.rgba(b,16)),('new after donor',a.rgba(donor)),('semantic candidate',a.rgba(after)),('after idle',a.composite(0)[0])]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'manifest.json',{'parent_arc_sha256':sha(a.data),'frames':records,'scope':'새 머리/다리는 before,의상/맨팔은 after 실제원화 의미영역. 후보이며 총/손·원순서·패킹 전.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'outside':q['new_outside_before'],'components':[q['components_before'],q['components_after']]}for q in records]))
if __name__=='__main__':main()
