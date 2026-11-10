"""새 손/소매를 유지하며 기존 사랑이 총몸의 크기를 접점에 맞춰 대조."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from check_first_geometry import full
from make_body_cycle import source
Y,X=np.indices((384,384));Y=Y-160;X=X-160
def hand(v,ex,ey):
 m=np.isin(v,(10,11,12))&(X<ex)&(Y>=ey+7)&(Y<ey+17);ls,count=label(m,np.ones((3,3)));options=[]
 for k in range(1,count+1):
  yy,xx=np.nonzero(ls==k)
  if len(xx)>=2:options.append((int(xx.min()),int(yy.min()),-len(xx),k))
 need(bool(options),'No hand');k=min(options)[-1];yy,xx=np.nonzero(ls==k)
 return ls==k,[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'held_cases_probe_v1';out.mkdir(exist_ok=False);rows=[];reports=[]
 for n in range(33,55,2):
  old=full(a,n);body=np.array(Image.open(source(n)));yy,xx=np.nonzero((old==14)&(Y<0));ex,ey=int(np.median(xx))-160,int(np.median(yy))-160;oh,ob=hand(old,ex,ey);nh,nb=hand(body,ex,ey)
  dx=nb[0]-ob[0];dy=nb[1]-ob[1]
  original=(X>=ob[0]-5)&(X<ob[2]+1)&(Y>=ob[1]-3)&(Y<ob[3]+1)&np.isin(old,(1,2,3,4));selected=np.zeros_like(body);oy,ox=np.nonzero(original);selected[oy+dy,ox+dx]=old[original]
  remove=(X>=nb[0]-6)&(X<nb[2]+1)&(Y>=nb[1]-3)&(Y<nb[3]+1)&np.isin(body,(1,2,3,4));target=body.copy();target[remove]=0;selected[nh]=0;target[selected>0]=selected[selected>0]
  # Do not let a casing replace skin in the authored hand or forearm.
  protected_skin=np.isin(body,(10,11,12));target[protected_skin]=body[protected_skin]
  comps=label(target>0,np.ones((3,3)))[1];Image.fromarray(target).save(out/f'before_{n:03}.png');Image.fromarray(selected).save(out/f'original_case_module_{n:03}.png')
  reports.append({'ref':n,'old_hand_box':ob,'new_hand_box':nb,'original_case_translation':[dx,dy],'original_case_pixels':int(original.sum()),'source_body_sha256':digest(source(n)),'changed_pixels':int(np.count_nonzero(target!=body)),'alpha_components_8':comps,'hand_skin_exact':True,'source_case_sha256':sha(selected.tobytes()),'indexed_sha256':sha(target.tobytes()),'scope':'Original gun dark case only; new hand skin and all colored sleeve texels preserved. Static candidate; semantic mask and grip review pending.'});rows.append((f'held {n}',[('original native case',a.rgba(old,16)),('new source body',a.rgba(body,16)),('case registration candidate',a.rgba(target,16))]))
 for start in range(0,len(rows),4):helper.grid(rows[start:start+4],out/f'comparison_{start//4+1}.png',5)
 write(out/'registration.json',{'frames':reports,'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
