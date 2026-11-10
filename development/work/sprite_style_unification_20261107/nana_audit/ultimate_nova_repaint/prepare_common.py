"""노바 준비 두 자세의 새 의상 의미영역과 공통 몸체를 분리한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
# 실제 새 원화의 목, 맨팔, 상의와 허리 경계. 양 끝 좌표를 포함한다.
SPANS={
213:{-8:(0,3),-7:(-1,5),-6:(-1,6),-5:(-1,8),-4:(-10,10),-3:(-10,11),-2:(-10,12),-1:(-10,12),0:(-10,12),1:(-6,12),2:(-3,12),3:(-3,12),4:(-4,12)},
215:{-8:(4,8),-7:(3,10),-6:(3,12),-5:(0,13),-4:(0,14),-3:(-1,15),-2:(-1,16),-1:(-1,16),0:(-1,16),1:(0,16),2:(2,15),3:(3,13),4:(3,13),5:(1,13)}
}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1');args=ap.parse_args()
 out=D/f'common_probe_{args.version}';out.mkdir(exist_ok=False)
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_sha256'],'부모 해시');a=Archive(p.read_bytes());frames=[];rows=[]
 for n in(213,215):
  b=np.array(Image.open(D/f'semantic_samples_v1/before_{n:03}_indices.png'));donor=np.array(Image.open(D/f'semantic_samples_v1/after_{n:03}_indices.png'));m=np.zeros(b.shape,bool)
  before_source=f'semantic_samples_v1/before_{n:03}_indices.png';boundary=[]
  if args.version in('v4','v5') and n==215:
   b=np.array(Image.open(D/'raise215_local_probe_v2/before_215_indices.png'));donor=np.array(Image.open(D/'raise215_local_probe_v2/after_215_indices.png'))
   before_source='raise215_local_probe_v2/before_215_indices.png'
   if args.version=='v5':
    x,y=14,0;need(b[y+160,x+160]==0 and donor[y+160,x+160]==2,'실제 허리 경계 한셀');b[y+160,x+160]=donor[y+160,x+160];boundary.append({'world':[x,y],'source':'raise215_local_probe_v2/after_215_indices.png','source_index':2,'before_was':0,'meaning':'새 원화의 허리 바깥 짙은 경계 한 셀을 양폼에 공통 등록. 새 맨팔을 자르거나 새 색을 그리지 않음.'})
   SPANS[n]={-19:(14,17),-18:(13,18),-17:(13,19),-16:(12,19),-15:(12,19),-14:(11,19),-13:(9,19),-12:(7,19),-11:(5,18),-10:(4,17),-9:(3,16),-8:(2,15),-7:(1,14),-6:(0,15),-5:(0,15),-4:(0,16),-3:(0,17),-2:(0,18),-1:(0,18),0:(0,18),1:(0,17),2:(0,16),3:(2,15),4:(3,14)}
  for y,(x0,x1)in SPANS[n].items():m[y+160,x0+160:x1+161]=True
  donor_source=f'semantic_samples_v1/after_{n:03}_indices.png'
  if args.version in('v4','v5') and n==215:donor_source='raise215_local_probe_v2/after_215_indices.png'
  if args.version in('v2','v3') and n==215:
   shift=1 if args.version=='v2' else 2
   donor_source=f'contacts_probe_v1/after_215_shift_m1_p{shift}_indices.png';donor=np.array(Image.open(D/donor_source))
  v=b.copy();v[m]=donor[m];outside=(v>0)&(b==0)
  need(np.array_equal(v[~m],b[~m]),'새 공통 머리/다리 원본 보존')
  for name,z in(('before',b),('after',v),('donor',donor),('costume_mask',m.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)):
   Image.fromarray(z).save(out/f'{name}_{n:03}_indices.png')
  frames.append({'ref':n,'costume_rows':SPANS[n],'before_source':before_source,'donor_source':donor_source,'source_boundary_links':boundary,'before_sha256':sha(b.tobytes()),'after_sha256':sha(v.tobytes()),'donor_sha256':sha(donor.tobytes()),'outside_before':[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(outside)],'components':[int(label(z>0,np.ones((3,3)))[1])for z in(b,v)],'alpha_clipped':False,'full_body_translation':[0,0],'old_body_copied':False})
  rows.append((str(n),[('jacket',a.rgba(b,16)),('bare source',a.rgba(donor)),('common candidate',a.rgba(v)),('idle',a.composite(0)[0])]))
 helper.grid(rows,out/'comparison.png',7)
 write(out/'manifest.json',{'parent_sha256':digest(p),'semantic_samples_sha256':digest(D/'semantic_samples_v1/manifest.json'),'frames':frames,'scope':'새 213/215 두 준비 자세의 의상 의미영역 등록 후보. 손목/목 경계와 원접점은 후속 검토이며 파츠/패킹/실기 완료가 아니다. 몸체를 옛 그림으로 덮거나 알파를 재킷에 맞춰 자르지 않았다.','native_packed':False,'runtime_verified':False})
 print(json.dumps(frames))
if __name__=='__main__':main()
