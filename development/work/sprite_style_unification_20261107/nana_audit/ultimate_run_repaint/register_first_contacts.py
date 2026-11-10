"""새 이동 첫4의 신발 국소 강체 정합과 accepted 사랑이 모듈 등록 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
HAND={1:(-10,0,-4,4),7:(-15,-1,-9,3),15:(-14,-2,-8,2),25:(-13,0,-7,4)}
FEET={7:[([(-22,16),(-10,16),(-10,24),(-22,24)],(1,-1)), ([(15,8),(25,8),(25,17),(16,17),(16,12),(14,10)],(-1,-1))],25:[([(-3,18),(6,18),(6,25),(-3,25)],(0,-1))]}
def poly(v):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in v],fill=1);return np.array(im,dtype=bool)
def main():
 src=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';need(digest(src)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Parent');a=Archive(src.read_bytes());out=D/'first_contacts_probe_v1';out.mkdir(exist_ok=False);canon=json.loads((N/'ultimate_dash_repaint/first_cases_probe_v2/registration.json').read_text('utf8'))['canonical_source_texels'];need(len(canon)==20,'Canonical weapon');rows=[];recs=[]
 for n in(1,7,15,25):
  p=D/f'before_first_registered_v1/before_{n:03}.png';b=np.array(Image.open(p));new=b.copy();changed=np.zeros_like(b,bool);foot_notes=[]
  for vertices,(dx,dy)in FEET.get(n,[]):
   m=poly(vertices);piece=np.where(m,b,0).astype(np.uint8);new[m]=0;shifted=np.roll(piece,(dy,dx),(0,1));use=shifted>0;new[use]=shifted[use];changed|=m|np.roll(m,(dy,dx),(0,1));foot_notes.append({'vertices':vertices,'translation':[dx,dy],'source_nonzero':int((piece>0).sum()),'source_sha256':sha(piece.tobytes()),'overlap_with_other_new_body':int((use&~m&(b>0)).sum())})
  afterfeet=new.copy();x0,y0,x1,y1=HAND[n];hand=np.isin(new,(10,11,12))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);yy,xx=np.nonzero(hand);need(len(xx)>=2,'Authored hand');hx,hy=int(xx.min()-160),int(yy.min()-160);case=np.zeros_like(new)
  for x,y,v in canon:case[y+hy+9+160,x+hx+16+160]=v
  remove=(X>=hx-7)&(X<=hx+3)&(Y>=hy-3)&(Y<=hy)&np.isin(new,range(1,10));remove|=(X>=hx-7)&(X<=hx)&(Y>hy)&(Y<=int(yy.max()-160)+2)&np.isin(new,(1,2,3,4));new[remove]=0;use=(case>0)&~np.isin(afterfeet,(10,11,12));new[use]=case[use];changed|=remove|use
  need(np.array_equal(new[~changed],b[~changed]),'Body outside authored modules');need(np.array_equal(new[np.isin(afterfeet,(10,11,12))],afterfeet[np.isin(afterfeet,(10,11,12))]),'New hand/skin preservation');need(label(new>0,np.ones((3,3)))[1]==1,f'Connected {n}');Image.fromarray(new).save(out/f'before_{n:03}.png');Image.fromarray(case).save(out/f'case_{n:03}.png');Image.fromarray(remove.astype(np.uint8)*255).save(out/f'gun_removal_{n:03}.png');yy2,xx2=np.nonzero(new);recs.append({'ref':n,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'foot_modules':foot_notes,'hand_box':HAND[n],'actual_grip_skin':[hx,hy],'canonical_case_texels':20,'case_visible':int(use.sum()),'generated_weapon_removed':int(remove.sum()),'sole_y':int(yy2.max()-160),'native_sha256':sha(new.tobytes()),'outside_modules_exact':True,'new_hand_skin_exact':True});rows.append((f'new run contact {n}',[('accepted idle',a.composite(0,15)[0]),('generated fixed cell',a.rgba(b,16)),('local shoes only',a.rgba(afterfeet,16)),('canonical gun / candidate',a.rgba(new,16))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'source_arc_sha256':digest(src),'canonical_ref85_texels':canon,'frames':recs,'method':'새 발목/신발만±1px 강체 등록. 나머지 새 몸/머리는 exact. 총열·그립20texel만 손에 정합하고 팔·피부 복사/늘림 없음.','art_review_pending':True,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
