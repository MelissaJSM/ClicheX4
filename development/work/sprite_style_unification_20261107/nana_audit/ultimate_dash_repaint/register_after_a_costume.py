"""후폼4의 새 의상만 의미영역에 등록; 전폼의 새머리/다리/권총은 보호."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED
from collect_before_bodies import SOURCES
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={67:[(-5,-3),(-1,-4),(3,-3),(6,0),(9,2),(12,4),(13,8),(8,8),(5,7),(1,7),(-2,8),(-4,5),(-5,2)],71:[(-16,10),(-11,9),(-8,8),(1,8),(6,11),(7,13),(6,16),(1,17),(-4,16),(-10,16),(-13,17),(-16,15)],79:[(-4,-4),(2,-5),(6,-3),(10,-1),(14,3),(15,6),(10,7),(5,6),(1,6),(-3,6),(-4,3)],93:[(-3,-9),(3,-9),(5,-8),(9,-4),(11,-1),(10,2),(6,4),(0,3),(-3,2),(-3,-4)]}
HAND={67:(-9,0,-4,7),71:(-14,13,-9,16),79:(-7,-1,-2,5),93:(-8,-5,-2,2)}
FAR={67:(8,4,14,9),71:(1,13,6,16),79:(10,3,16,7),93:(7,-2,12,3)}
LEGY={67:8,71:16,79:6,93:3}
def box(b,q):
 x0,y0,x1,y1=q;return np.isin(b,(10,11,12))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def main(page='a',polys=POLYS,hands=HAND,fars=FAR,legys=LEGY,version='v3'):
 need(page in('a','b','c')and version.isalnum(),'Page');need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/f'after_{page}_costume_probe_{version}';out.mkdir(exist_ok=False);pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words]);mapped=int(np.argmin(((pal[:16].astype(float)-pal[31])**2).sum(axis=1)));need(mapped==13,'31 meaning');rows=[];recs=[]
 for n,poly in polys.items():
  bp=D/SOURCES[n]/f'before_{n:03}.png';ap=D/f'after_{page}_registered_v2'/f'after_{n:03}.png';b=np.array(Image.open(bp));donor=np.array(Image.open(ap));cp=D/('first_cases_probe_v2'if n in(67,71,79,93)else'more_cases_probe_v2')/f'case_{n:03}.png';case=np.array(Image.open(cp));mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=255);mask=np.array(mi)>0;protected=(case>0)|box(b,hands[n])|box(b,fars[n])|((Y>=legys[n])&np.isin(b,(10,11,12,14)))
  t=b.copy();t[b==15]=mapped;t[mask]=donor[mask];t[protected]=b[protected];t[protected&(b==15)]=mapped;added=(t>0)&(b==0)&mask;t[added]=0
  # 의미영역 외에는 새 전폼을 그대로 사용한다. 팔레트31 밝은 회색만 후폼의13으로 재표현한다.
  expected=b.copy();expected[b==15]=mapped;need(np.array_equal(t[~mask],expected[~mask]),'Outside costume');need(np.array_equal(t[case>0],b[case>0]),'Weapon');need(not ((t>0)&(b==0)).any(),'Outside silhouette');components=label(t>0,np.ones((3,3)))[1];need(components==label(b>0,np.ones((3,3)))[1],'Detached costume')
  Image.fromarray(t).save(out/f'after_{n:03}.png');Image.fromarray(b).save(out/f'before_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'mask_{n:03}.png');Image.fromarray(protected.astype(np.uint8)*255).save(out/f'protected_{n:03}.png');recs.append({'ref':n,'before_path':bp.relative_to(ROOT).as_posix(),'before_sha256':digest(bp),'donor_path':ap.relative_to(ROOT).as_posix(),'donor_sha256':digest(ap),'polygon':poly,'near_hand_box':hands[n],'far_hand_box':fars[n],'leg_skin_protected_y_min':legys[n],'mapped_palette15':mapped,'outside_mask_exact_except_palette15':True,'weapon_exact':True,'removed_outside_envelope':int(added.sum()),'changed':int((t!=b).sum()),'components8':components,'indexed_sha256':sha(t.tobytes())});rows.append((f'costume {n}',[('after idle',a.composite(0,0)[0]),('new before body',a.rgba(b,16)),('after donor',a.rgba(donor)),('local costume / common body',a.rgba(t))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'frames':recs,'source_policy':'새후폼 의상 의미다각형만 채택. 원형/팔레트색 자동생성 없음. 새전폼 머리·사지·권총 유지.','native_packed':False,'runtime_verified':False,'art_review_pending':True});print(out)
if __name__=='__main__':main(version='v4')
