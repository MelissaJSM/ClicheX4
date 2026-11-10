"""원발사점 새팔 donor를 기존 새몸에 국소 등록하고 정본총을 연결한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def box(b):return(X>=b[0])&(Y>=b[1])&(X<b[2])&(Y<b[3])
def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,dtype=bool)
SPECS={
 222:{'translation':[0,0],'barrel':[-26,-10],'poly':[(-23,-8),(-18,-8),(-17,-7),(-15,-7),(-15,-9),(-4,-9),(1,-7),(1,-4),(-4,-4),(-4,-6),(-14,-6),(-14,-5),(-21,-5),(-23,-7)]},
 224:{'translation':[0,1],'barrel':[-28,-10],'poly':[(-25,-8),(-20,-8),(-19,-7),(-17,-7),(-17,-9),(-4,-9),(1,-7),(1,-4),(-4,-4),(-4,-6),(-16,-6),(-16,-5),(-23,-5),(-25,-7)]},
 226:{'translation':[0,0],'barrel':[-19,-11],'poly':[(-16,-9),(-12,-9),(-11,-8),(-11,-7),(-8,-7),(-6,-8),(-4,-9),(1,-7),(1,-4),(-4,-4),(-6,-3),(-9,-3),(-10,-4),(-11,-5),(-15,-5),(-16,-7)]},
 228:{'translation':[3,0],'barrel':[-19,-11],'poly':[(-16,-9),(-12,-9),(-11,-8),(-11,-7),(-8,-7),(-6,-8),(-4,-9),(1,-7),(1,-4),(-4,-4),(-6,-3),(-9,-3),(-10,-4),(-11,-5),(-15,-5),(-16,-7)]},
 230:{'translation':[0,0],'barrel':[-23,-12],'poly':[(-20,-10),(-16,-10),(-15,-9),(-14,-9),(-14,-8),(-11,-8),(-8,-7),(-5,-8),(-4,-9),(1,-7),(1,-3),(-3,-3),(-3,-2),(-10,-2),(-11,-4),(-15,-4),(-15,-6),(-19,-6),(-20,-8)]}}
def main():
 out=D/'muzzle_joint_probe_v1';out.mkdir(exist_ok=False);a=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());rows=[];frames=[]
 for n,s in SPECS.items():
  page='a'if n<230 else'b';meta=json.loads((D/f'muzzle_arm_{page}_inputs_v1/manifest.json').read_text('utf8'));q=next(v for v in meta['frames']if v['ref']==n);src=D/f'muzzle_arm_{page}_registered_v1/body_{n:03}_indices.png';donor=np.array(Image.open(src));bp=D/f'canonical_cases_probe_v4/body_{n-1:03}_indices.png';base=np.array(Image.open(bp));m=poly(s['poly']);piece=np.where(m,donor,0);gx,gy=s['barrel'];generated_grip=box([gx,gy-1,gx+8,gy+6])&np.isin(piece,[5,6,7,8,9]);piece[generated_grip]=0;dx,dy=s['translation'];moved=np.roll(np.roll(piece,dy,0),dx,1);z=base.copy();remove=box([-16,-7,-4,2]);z[remove]=0;protected=((X>=-8)&(Y<=-10))|((X>=1)&(Y<=-7));use=(moved>0)&~protected;z[use]=moved[use];gun=np.array(Image.open(D/f'muzzle_arm_{page}_inputs_v1/target_gun_{n}.png'));mx,my=q['muzzle_left_x'],q['engine_projectile_origin'][1];skin=box([mx+3,my,mx+10,my+6])&np.isin(moved,[10,11,12,13]);guse=(gun>0)&~skin;z[guse]=gun[guse];labs,ct=label(z>0,np.ones((3,3)));components=[{'size':int((labs==i).sum()),'cells':[[int(x-160),int(y-160),int(z[y,x])]for y,x in np.argwhere(labs==i)]if (labs==i).sum()<25 else None}for i in range(1,ct+1)];need(np.array_equal(z[Y>=3],base[Y>=3]),'하체 보호');need(np.array_equal(z[(X>=-8)&(Y<=-10)],base[(X>=-8)&(Y<=-10)]),'새머리 보호')
  for tag,v in [('body',z),('source_arm',piece),('placed_arm',moved),('canonical',gun)]:Image.fromarray(v).save(out/f'{tag}_{n:03}_indices.png')
  Image.fromarray(m.astype(np.uint8)*255).save(out/f'source_mask_{n}.png');old=np.array(Image.open(D/f'shot_joint_probe_v2/body_{n:03}_indices.png'));frames.append({'ref':n,'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'body_source':bp.relative_to(ROOT).as_posix(),'body_source_sha256':digest(bp),'source_polygon':s['poly'],'source_translation':[dx,dy],'source_generated_grip_removed_cells':[[int(x-160),int(y-160),int(donor[y,x])]for y,x in np.argwhere(generated_grip)],'removed_held_window':[-16,-7,-4,2],'canonical_translation':q['canonical_translation'],'engine_projectile_origin':q['engine_projectile_origin'],'canonical_visible':int(guse.sum()),'canonical_skin_occluded':int(((gun>0)&skin).sum()),'components8':components,'target_sha256':sha(z.tobytes()),'old_firing_8column_window_preserved':False,'runtime_verified':False});rows.append((str(n),[('prior gun-position candidate',a.rgba(old)),('new local source',a.rgba(donor)),('actual muzzle joint candidate',a.rgba(z))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'parent_arc_sha256':sha(a.data),'frames':frames,'scope':'원발사표/원US 총입구에 맞춘 정본총20과 새 팔 donor 국소정합 후보. 현재8열 총창 고정정책은 폐기. 228의 새팔은+3x 강체정합 후보로 어깨/팔꿈치 재열람 필요. 몸체/하체/원코드·효과 불변.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'components':q['components8'],'visible':q['canonical_visible'],'occluded':q['canonical_skin_occluded']}for q in frames]))
if __name__=='__main__':main()
