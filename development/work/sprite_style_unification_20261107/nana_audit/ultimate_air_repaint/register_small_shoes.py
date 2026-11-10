"""새 원화의 구두 모듈만 대기 크기 규칙에 맞춰 국소 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
SPANS={37:{9:(6,9),10:(6,10),11:(5,10),12:(4,11),13:(2,11),14:(2,11),15:(4,11),16:(5,11),17:(6,7)},41:{10:(4,7),11:(3,8),12:(4,9),13:(4,9),14:(2,9),15:(2,9),16:(4,9),17:(4,9),18:(5,6)}}
PLACEMENT={37:((7,7),(3,11)),41:((6,7),(1,12))}
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'small_shoes_probe_v2';out.mkdir(exist_ok=False);rows=[];reports=[]
 for n in(37,41):
  path=D/f'before_second_registered_v1/before_{n:03}.png';old=np.array(Image.open(path));mask=np.zeros(old.shape,bool)
  for y,(lo,hi)in SPANS[n].items():mask[y+160,lo+160:hi+160]=old[y+160,lo+160:hi+160]>0
  yy,xx=np.nonzero(mask);x0,x1,y0,y1=int(xx.min()),int(xx.max()+1),int(yy.min()),int(yy.max()+1);module=np.where(mask,old,0)[y0:y1,x0:x1];size,(dx,dy)=PLACEMENT[n]
  votes=np.stack([np.array(Image.fromarray((module==v).astype(np.float32),'F').resize(size,Image.Resampling.BOX))for v in range(1,16)]);coverage=votes.sum(0);resized=1+votes.argmax(0).astype(np.uint8);resized[coverage<.5]=0
  new=old.copy();new[mask]=0;field=np.zeros_like(old);field[dy+160:dy+160+size[1],dx+160:dx+160+size[0]]=resized
  overlap=(field>0)&(new>0);need(np.count_nonzero(overlap)<8,'Excess body overlap');new[field>0]=field[field>0]
  changed=(new!=old);region=mask|(field>0);need(np.array_equal(new[~region],old[~region]),'Outside module changed');components=label(new>0,np.ones((3,3)))[1];need(components==1,'Foot detached');need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Sole height changed')
  Image.fromarray(new).save(out/f'before_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'source_shoe_mask_{n:03}.png')
  rows.append((f'shoe {n}',[('accepted idle',a.composite(0,15)[0]),('new body previous',a.rgba(old,16)),('source shoes locally registered',a.rgba(new,16))]))
  reports.append({'ref':n,'input_sha256':digest(path),'source_spans_world':SPANS[n],'source_box_world':[x0-160,y0-160,x1-160,y1-160],'target_size':size,'target_position_world':[dx,dy],'changed_pixels':int(changed.sum()),'overlap_pixels':int(overlap.sum()),'outside_shoe_module_exact':True,'alpha_components_8':components,'sole_y_exact':True,'method':'Area-vote source-index resampling of explicitly isolated new shoe/ankle module only. No original game body pixels, invented colors or leg enlargement.','indexed_sha256':sha(new.tobytes())})
 helper.grid(rows,out/'comparison.png',8);write(out/'registration.json',{'frames':reports,'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
