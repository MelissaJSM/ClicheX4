"""217 고정 셀의 실제 홍채/팔레트15 표본과 피부색 후보를 읽는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write
def main():
 out=D/'dash217_samples_v1';out.mkdir(exist_ok=False);m=json.loads((D/'dash217_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);im=Image.open(D/'dash217_v1/generated.png').convert('RGBA');ar=np.array(im);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255;res=lambda q:np.array(Image.fromarray(q.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX));mass=res(alpha);mean=np.stack([res(rgb[:,:,k]*alpha)/np.maximum(mass,.001)for k in range(3)],2);labs=np.zeros(ar.shape[:2],np.uint8)
 for y in range(im.height):labs[y]=1+((rgb[y,:,None]-pal[None,1:])**2).sum(2).argmin(1)
 votes=np.stack([res(np.where(labs==v,alpha,0))for v in range(1,16)]);z=np.array(Image.open(D/'dash217_registered_v1/body_217_indices.png'));eyes=[];skin=[];p15=[]
 for y in range(-3,6):
  for x in range(-19,-9):
   v=votes[13,y+48,x+48]
   if v>.02:eyes.append({'world':[x,y],'old_index':int(z[y+160,x+160]),'green_fraction':float(v),'source_mean_rgb':mean[y+48,x+48].tolist(),'votes':{str(i+1):float(t)for i,t in enumerate(votes[:,y+48,x+48])if t>.01}})
 for yy,xx in np.argwhere(z==15):
  x,y=int(xx-160),int(yy-160);allowed=np.arange(1,15);value=int(allowed[((pal[allowed]-mean[y+48,x+48])**2).sum(1).argmin()]);p15.append({'world':[x,y],'old_index':15,'source_mean_rgb':mean[y+48,x+48].tolist(),'nearest_non15':value})
 for yy,xx in np.argwhere(np.isin(z,[5,6,7,8,9])):
  x,y=int(xx-160),int(yy-160)
  if y<9:continue
  allowed=np.array([1,2,3,4,10,11,12,13]);value=int(allowed[((pal[allowed]-mean[y+48,x+48])**2).sum(1).argmin()]);skin.append({'world':[x,y],'old_index':int(z[yy,xx]),'source_mean_rgb':mean[y+48,x+48].tolist(),'nearest_skin':value})
 write(out/'report.json',{'source_sha256':digest(D/'dash217_v1/generated.png'),'iris_candidates':eyes,'palette15_candidates':p15,'lower_candidates':skin,'scope':'실제 source 투표/평균RGB만 읽은 의미 표본 후보. 몸체/색/알파 수정 없음.'});print(json.dumps({'iris':eyes,'p15':p15,'skin':skin}))
if __name__=='__main__':main()
