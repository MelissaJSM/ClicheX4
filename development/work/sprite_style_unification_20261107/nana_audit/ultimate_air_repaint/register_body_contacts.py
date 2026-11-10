"""새 몸체의 손/신발 접점만 원점에 맞춘다. 새 원화 색인 이동만 사용."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from make_body_cycle import source
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'body_contacts_probe_v4';out.mkdir(exist_ok=False);records=[];rows=[];Y,X=np.indices((384,384));Y=Y-160;X=X-160
 for n in(33,35,39,47):
  path=source(n);old=np.array(Image.open(path));new=old.copy();moves=[]
  if n==33:mask=(Y>=15)&(old>0);dx=np.full(old.shape,-1)
  elif n==35:mask=(Y>=13)&(old>0);dx=-np.clip(Y-12,0,4)
  elif n==39:mask=(Y>=12)&(old>0);dx=np.full(old.shape,-2)
  else:mask=(Y>=13)&(old>0);dx=np.full(old.shape,-2)
  yy,xx=np.nonzero(mask);new[mask]=0;destx=xx+dx[mask];need(np.all(new[yy,destx]==0),'Foot module collision');new[yy,destx]=old[mask]
  moves.append({'scope':'new shoe/lower-calf module','native_source_pixels':int(mask.sum()),'row_shifts':{int(y):int(dx[y+160,xx[0]])for y in sorted(set((yy-160).tolist()))}})
  if n==39:moves.append({'scope':'raised fist/cuff','changed':False,'reason':'Rigid shift collided with authored ear/upper arm, so rejected; no overwrite applied.'})
  need(label(new>0,np.ones((3,3)))[1]==1,'Disconnected module');need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Sole y');need(np.array_equal(new[np.isin(old,[14])&(Y<0)],old[np.isin(old,[14])&(Y<0)]),'Pupil')
  Image.fromarray(new).save(out/f'before_{n:03}.png');records.append({'ref':n,'input':str(path.relative_to(ROOT)),'input_sha256':digest(path),'moves':moves,'output_indexed_sha256':sha(new.tobytes()),'flat_color_fill':0,'old_game_pixel_copy':0,'alpha_components_8':1,'sole_y_exact':True});rows.append((f'contact {n}',[('native prior',a.rgba(old,16)),('local source registration',a.rgba(new,16))]))
 helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'frames':records,'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
