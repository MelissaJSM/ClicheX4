"""보류 v2의 101 발끝/104 긴 부츠를 새 기본 원화 폭으로 되돌린 국소 비교."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from probe_common_legs import spans
Y,X=np.indices((384,384));Y-=160;X-=160

def main():
 out=D/'common_legs_probe_v3';out.mkdir(exist_ok=False);a=Archive((N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes());rows=[];reports=[]
 for n in(100,101,102,103,104,231):
  v2=D/'common_legs_probe_v2';source=D/'body_contacts_probe_v1';b=np.array(Image.open(v2/f'base_{n:03}_indices.png'));f=np.array(Image.open(v2/f'fourth_authored_contacts_{n:03}_indices.png'));authb=np.array(Image.open(source/f'base_{n:03}_indices.png'));authf=np.array(Image.open(source/f'fourth_{n:03}_indices.png'));before=b.copy();beforef=f.copy();links=[]
  region=np.zeros_like(b,bool)
  if n==101:region=(Y>=18)&(Y<=20)&(X>=-7)&(X<=-3)
  if n==104:region=(Y>=6)&(Y<=18)&(X>=-1)&(X<=11)
  if region.any():
   # Preserve the exact newly authored basic boot in the explicitly reviewed
   # region. Fourth samples stay on this pose's same leg and same scanline.
   b[region]=authb[region]
   for py in np.flatnonzero(region.any(1)):
    dst=np.flatnonzero(region[py]&(b[py]>0));src=np.flatnonzero(region[py]&(authf[py]>0))
    need(len(dst)>0 and len(src)>0,'Both same-leg source sections exist')
    need(len(spans(region[py]&(authf[py]>0)))==1,'No cross-leg sampling')
    need(abs(float(dst.mean()-src.mean()))<=1.5,'Local offset only')
    sample=np.rint(np.linspace(0,len(src)-1,len(dst))).astype(int)
    # The costume's outside contour in this region follows only the boot
    # section, not its former surplus pixels. All colors have exact provenance.
    f[py,region[py]]=0;f[py,dst]=authf[py,src[sample]]
    links.extend({'world':[int(dx-160),int(py-160)],'source_world':[int(sx-160),int(py-160)],'index':int(authf[py,sx])}for dx,sx in zip(dst,src[sample]))
   need(np.array_equal(b[region],authb[region]),'Basic original boot details')
  full=np.where(f,f,b).astype(np.uint8)
  for name,z in(('base',b),('fourth_authored_contacts',f),('fourth',full)):Image.fromarray(z).save(out/f'{name}_{n:03}_indices.png')
  if n in(101,104):rows.append((f'local boot {n}',[('source base',a.rgba(authb)),('held v2',a.rgba(before)),('source boot width restored',a.rgba(b)),('Fourth same-leg source',a.rgba(full,16))]))
  reports.append({'ref':n,'source_base_sha256':sha(authb.tobytes()),'source_fourth_sha256':sha(authf.tobytes()),'previous_base_sha256':sha(before.tobytes()),'previous_fourth_sha256':sha(beforef.tobytes()),'base_sha256':sha(b.tobytes()),'fourth_sha256':sha(f.tobytes()),'base_changed':int((b!=before).sum()),'fourth_changed':int((f!=beforef).sum()),'localized_same_leg_links':links,'uncovered_within_edit':int(((b>0)&(f==0)&region).sum()),'base_components':int(label(b>0,np.ones((3,3)))[1]),'full_components':int(label(full>0,np.ones((3,3)))[1])})
 helper.grid(rows,out/'comparison.png',8)
 write(out/'manifest.json',{'scope':'101 발끝3행과104 긴 부츠13행만 새 기본 원화 폭으로 보존. 포스는 같은 자세/같은 다리/같은 행의 실제 새 원화 표본을 국소 폭에 등록. 다리 전체 길이 및 다른 그림 불변. 비교 후보이며 미술 수용/패킹 전.','frames':reports,'new_image_generated':False,'native_packed':False,'runtime_verified':False})
 print(json.dumps([{k:r[k]for k in('ref','base_changed','fourth_changed','base_components','full_components')}for r in reports]))
if __name__=='__main__':main()
