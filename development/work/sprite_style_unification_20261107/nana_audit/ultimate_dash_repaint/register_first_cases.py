"""accepted85의 총열/그립20texel만 새 대시 손에 정합하는 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED,merged
Y,X=np.indices((384,384));Y-=160;X-=160
HAND_BOXES={67:(-9,0,-4,7),71:(-14,13,-9,16),79:(-7,-1,-2,5),93:(-8,-5,-2,2)}
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'first_cases_probe_v2';out.mkdir(exist_ok=False);accepted=merged(a,85,15)
 mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(accepted,range(1,10));coords=[(int(x-160),int(y-160),int(accepted[y,x]))for y,x in zip(*np.nonzero(mask))];need(len(coords)==20,'Case20');records=[];rows=[]
 for n in(67,71,79,93):
  src=D/f'first_contacts_probe_v1/before_{n:03}.png';b=np.array(Image.open(src));x0,y0,x1,y1=HAND_BOXES[n];hm=np.isin(b,(10,11,12))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);yy,xx=np.nonzero(hm);need(len(xx)>=2,'Grip skin');hb=[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)];dx,dy=hb[0]+16,hb[1]+9;target=b.copy()
  remove=(X>=hb[0]-7)&(X<hb[0]+1)&(Y>=hb[1]-3)&(Y<hb[3]+2)&np.isin(b,(1,2,3,4));target[remove]=0;case=np.zeros_like(b)
  for x,y,v in coords:case[y+dy+160,x+dx+160]=v
  use=(case>0)&~np.isin(b,(10,11,12));target[use]=case[use]
  protected=np.isin(b,(10,11,12))|((b>=5)&(case==0));need(np.array_equal(target[protected],b[protected]),'Authored material changed')
  need(label(target>0,np.ones((3,3)))[1]==label(b>0,np.ones((3,3)))[1],f'Detached {n}')
  Image.fromarray(target).save(out/f'before_{n:03}.png');Image.fromarray(case).save(out/f'case_{n:03}.png');Image.fromarray(remove.astype(np.uint8)*255).save(out/f'removal_{n:03}.png')
  records.append({'ref':n,'body_source':str(src.relative_to(ROOT)),'body_sha256':digest(src),'hand_box_world':HAND_BOXES[n],'actual_grip_skin_bbox':hb,'case_translation':[dx,dy],'case20_texels_placed':int(use.sum()),'gray_generated_case_texels_removed':int(remove.sum()),'indexed_sha256':sha(target.tobytes()),'new_skin_exact':True})
  rows.append((f'held case {n}',[('accepted 85',a.composite(85,15)[0]),('new body/case',a.rgba(b,16)),('new body/canonical weapon only',a.rgba(target,16))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'canonical_ref':85,'canonical_source_texels':coords,'frames':records,'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
