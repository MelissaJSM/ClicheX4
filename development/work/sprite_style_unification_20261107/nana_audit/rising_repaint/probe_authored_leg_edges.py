"""원화의 실제 어두운 경계 표본과 area vote의 손실을 분리하는 미술 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,binary_erosion
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';a=Archive(src.read_bytes());need(digest(src)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Parent')
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
 out=D/'authored_leg_edge_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for n,page in [(101,'charge'),(102,'recovery_ground'),(231,'recovery_ground')]:
  rd=D/f'{page}_registered_v1';meta=json.loads((rd/'registration.json').read_text('utf8'));q=next(r for r in meta['frames']if r['form']=='fourth'and r['ref']==n)
  p=D/f'{page}_v1/generated.png';art=Image.open(p).convert('RGBA');need(digest(p)==meta['source_art_sha256'],'Art');crop=art.crop(q['cell_crop']);arr=np.array(crop);rgb=arr[:,:,:3].astype(np.float32);alpha=arr[:,:,3].astype(np.float32)/255
  labels=np.zeros(arr.shape[:2],np.uint8)
  for yy in range(crop.height):labels[yy]=1+((rgb[yy,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
  # Native alpha and all nonedge colors are immutable in this probe.
  votes=np.stack([np.array(Image.fromarray(np.where((labels==i)&(arr[:,:,3]>=192),alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
  coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));native=register(crop,(96,96),pal,'area_vote');base=np.zeros((384,384),np.uint8);base[112:208,112:208]=native
  dx,dy=q['whole_translation'];base=np.roll(base,(dy,dx),(0,1));current=np.array(Image.open(rd/f'fourth_{n:03}_indices.png'));need(np.array_equal(base,current),'Exact source registration')
  outer=(base>0)&~binary_erosion(base>0,np.array([[0,1,0],[1,1,1],[0,1,0]],bool))
  near_skin=binary_dilation(np.isin(base,(10,11,12)),np.ones((3,3)))
  region=(Y>=0)&(Y<=20)&(X<16)&np.isin(base,(3,4))&near_skin&outer
  candidate=base.copy();samples=[];eligible=[]
  for y,x in np.argwhere(region):
   lx,ly=x-112-dx,y-112-dy;need(0<=lx<96 and 0<=ly<96,'Source index');v=votes[:,ly,lx];dark=float(v[0]+v[1]);cov=float(coverage[ly,lx]);choice=int(np.argmax(v[:2])+1)
   x0,x1=int(np.floor(lx*crop.width/96)),int(np.ceil((lx+1)*crop.width/96));y0,y1=int(np.floor(ly*crop.height/96)),int(np.ceil((ly+1)*crop.height/96))
   allowed=(labels[y0:y1,x0:x1]==choice)&(arr[y0:y1,x0:x1,3]>=192);points=np.argwhere(allowed)
   change=dark>=.12 and dark/max(cov,1e-6)>=.18 and len(points)>0
   rec={'world':[int(x-160),int(y-160)],'before':int(base[y,x]),'dark_coverage':dark,'alpha_coverage':cov,'dark_share_of_covered':dark/max(cov,1e-6),'source_cell_box':[x0,y0,x1,y1],'registered_dark_choice':choice,'changed':bool(change)}
   if change:
    center=np.array([(ly+.5)*crop.height/96-y0,(lx+.5)*crop.width/96-x0]);sy,sx=points[np.square(points-center).sum(1).argmin()];sy,sx=int(sy+y0),int(sx+x0)
    rec.update({'after':choice,'source_page_pixel':[sx+q['cell_crop'][0],sy+q['cell_crop'][1]],'source_RGBA':[int(v)for v in arr[sy,sx]],'source_nearest_palette_index':int(labels[sy,sx])});candidate[y,x]=choice;samples.append(rec)
   eligible.append(rec)
  need(np.array_equal(candidate>0,base>0),'Alpha');need(np.array_equal(candidate[~region],base[~region]),'Outside edge');Image.fromarray(candidate).save(out/f'fourth_{n:03}_indices.png');Image.fromarray(region.astype(np.uint8)*255).save(out/f'eligible_{n:03}.png')
  rows.append((f'fourth {n}',[('accepted idle',a.composite(0,15)[0]),('current area vote',a.rgba(base,16)),('authored dark sample probe',a.rgba(candidate,16))]));records.append({'ref':n,'source_art_path':p.relative_to(ROOT).as_posix(),'source_art_sha256':digest(p),'source_registration':q,'native_before':sha(base.tobytes()),'native_after':sha(candidate.tobytes()),'eligible_samples':eligible,'changes':samples,'alpha_exact':True,'all_nonedge_pixels_exact':True})
 helper.grid(rows,out/'comparison.png',7)
 write(out/'manifest.json',{'source_arc_sha256':digest(src),'frames':records,'method':'원화의 같은 셀/고정배율에서 alpha192 이상 실제 RGB의 팔레트1/2 면적을 재확인했다. 회색3/4이면서 피부 인접한 외곽 중 어두운표본 면적>=0.12/피복비>=0.18만 그 실제 색인으로 후보 등록. 알파·두께·다리 길이·그 외 그림 불변.','source_dark_thresholds':[.12,.18],'candidate_only':True,'art_accepted':False,'native_packed':False,'runtime_verified':False})
 print(json.dumps({r['ref']:{'eligible':len(r['eligible_samples']),'changed':len(r['changes'])}for r in records}))
if __name__=='__main__':main()
