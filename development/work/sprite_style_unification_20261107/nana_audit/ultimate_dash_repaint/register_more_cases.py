"""새 연결6자세에 사랑이의 동일20texel 권총모듈만 새 손 위치로 정합."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED,merged
SPECS={69:('before_second_registered_v1',(-16,6,-11,9)),75:('local_legs_registered_v4',(-18,14,-13,16)),77:('before_second_registered_v1',(-7,3,-3,5)),81:('local_legs_registered_v4',(1,-4,4,-1)),83:('before_last_registered_v1',(-8,2,-6,4)),94:('before_last_registered_v1',(-7,-5,-4,-2))}
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'more_cases_probe_v2';out.mkdir(exist_ok=False);ref=merged(a,85,15);Y,X=np.indices(ref.shape);Y-=160;X-=160;mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(ref,range(1,10));coords=[(int(x-160),int(y-160),int(ref[y,x]))for y,x in zip(*np.nonzero(mask))];need(len(coords)==20,'Canonical20');records=[];rows=[]
 for n,(folder,box)in SPECS.items():
  src=D/folder/f'before_{n:03}.png';old=np.array(Image.open(src));x0,y0,x1,y1=box;hm=np.isin(old,(10,11,12))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);yy,xx=np.nonzero(hm);need(len(xx)>=2,'Hand skin');hx,hy=int(xx.min()-160),int(yy.min()-160);new=old.copy();case=np.zeros_like(old)
  for x,y,v in coords:
   dx,dy=x+16,y+9
   if n==83:dx,dy=dy,-dx
   case[hy+dy+160,hx+dx+160]=v
  if n==83:remove=np.zeros_like(old,dtype=bool)
  else:remove=(X>=hx-7)&(X<hx+1)&(Y>=hy-3)&(Y<int(yy.max()-160)+3)&np.isin(old,(1,2,3,4))
  removed_colored=[]
  if n==94:
   # 새 원화의 별도 분홍 총열이 기존 회색만 제거하는 후보에서 남았다.
   # source gun x877..930/y295..315에 대응하는 실제3행만 등록한다.
   weapon=(X>=-9)&(X<=-3)&(Y>=-8)&(Y<=-6)&(old>0)
   need(not np.isin(old[weapon],(10,11,12,13,14,15)).any(),'94 authored barrel material')
   removed_colored=[{'xy':[int(x-160),int(y-160)],'before':int(old[y,x])}for y,x in zip(*np.nonzero(weapon))]
   remove|=weapon
  new[remove]=0;use=(case>0)&~np.isin(old,(10,11,12));new[use]=case[use];protected=np.isin(old,(10,11,12))|((old>=5)&(case==0)&~remove);need(np.array_equal(new[protected],old[protected]),'Skin or authored colors outside gun')
  need(label(new>0,np.ones((3,3)))[1]==label(old>0,np.ones((3,3)))[1],f'Detached {n}');Image.fromarray(new).save(out/f'before_{n:03}.png');Image.fromarray(case).save(out/f'case_{n:03}.png');Image.fromarray(remove.astype(np.uint8)*255).save(out/f'removal_{n:03}.png')
  records.append({'ref':n,'source_body':str(src.relative_to(ROOT)),'source_body_sha256':digest(src),'hand_box':box,'grip_world':[hx,hy],'rotation':'barrel_down_90deg'if n==83 else'horizontal_left','source_case_texels':20,'visible_case_texels':int(use.sum()),'removed_generated_case_texels':int(remove.sum()),'authored_barrel_semantic_texels':removed_colored,'all_new_skin_exact':True,'result_index_sha256':sha(new.tobytes())})
  rows.append((f'held Sarang-i {n}',[('accepted 85 module',a.composite(85,15)[0]),('new source body/case',a.rgba(old,16)),('new body/canonical case',a.rgba(new,16))]))
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
 write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'canonical_ref':85,'canonical_texels':coords,'frames':records,'no_arm_or_skin_copied':True,'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
