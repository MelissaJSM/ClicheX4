"""수용된 85번의 사랑이 총열/그립만 새 비사격 손에 등록하는 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from check_first_geometry import full
from make_body_cycle import source
from review_held_cases import hand
Y,X=np.indices((384,384));Y=Y-160;X=X-160
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'canonical_cases_probe_v1';out.mkdir(exist_ok=False)
 accepted=full(a,85);mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(accepted,range(1,10))
 coords=[(int(x-160),int(y-160),int(accepted[y,x]))for y,x in zip(*np.nonzero(mask))]
 need(len(coords)==20,'Canonical case changed')
 Image.fromarray(np.where(mask,accepted,0).astype(np.uint8)).save(out/'accepted85_weapon_only.png');records=[];rows=[]
 for n in range(33,55,2):
  b=np.array(Image.open(source(n)));old=full(a,n);yy,xx=np.nonzero((old==14)&(Y<0));ex,ey=int(np.median(xx))-160,int(np.median(yy))-160;hm,hb=hand(b,ex,ey)
  # The anchor is the first original fingertip at (-16,-9). No gun scaling,
  # and no arm/skin/sleeve pixels are imported from the old accepted frame.
  dx,dy=hb[0]+16,hb[1]+9;target=b.copy();remove=(X>=hb[0]-7)&(X<hb[0]+1)&(Y>=hb[1]-3)&(Y<hb[3]+2)&np.isin(b,(1,2,3,4))
  target[remove]=0;case=np.zeros_like(b)
  for x,y,v in coords:case[y+dy+160,x+dx+160]=v
  protected=np.isin(b,(10,11,12))|((b>=5)&(case==0));use=(case>0)&~np.isin(b,(10,11,12));target[use]=case[use]
  need(np.array_equal(target[hm],b[hm]),'Authored fingers changed');need(np.array_equal(target[protected],b[protected]),'Authored material changed')
  need(label(target>0,np.ones((3,3)))[1]==1,'Detached case/body')
  Image.fromarray(target).save(out/f'before_{n:03}.png');Image.fromarray(case).save(out/f'case_{n:03}.png');Image.fromarray(remove.astype(np.uint8)*255).save(out/f'removal_{n:03}.png')
  records.append({'ref':n,'body_source':source(n).relative_to(ROOT).as_posix(),'body_sha256':digest(source(n)),'new_hand_bbox':hb,'case_translation':[dx,dy],'canonical_pixels':len(coords),'placed_pixels':int(use.sum()),'removed_generated_gray_case_pixels':int(remove.sum()),'changed_pixels':int(np.count_nonzero(target!=b)),'indexed_sha256':sha(target.tobytes()),'hand_skin_exact':True,'color_source':'accepted PL02 ref85 indices only','art_review_pending':True})
  rows.append((f'held {n}',[('accepted standing case',a.composite(85,15)[0]),('new authored body',a.rgba(b,16)),('same body / consistent case',a.rgba(target,16))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'registration.json',{'parent_arc_sha256':sha(a.data),'canonical_ref':85,'canonical_source_texels':coords,'canonical_sha256':sha(accepted[mask].tobytes()),'frames':records,'native_packed':False,'runtime_verified':False,'previous_U_case_candidate_adopted':False});print(str(out))
if __name__=='__main__':main()
