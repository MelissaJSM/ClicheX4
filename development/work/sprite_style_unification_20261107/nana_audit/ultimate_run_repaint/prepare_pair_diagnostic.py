"""새 이동32 전후 공통층의 경계만 진단한다. 아직 패킹하지 않는다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
VERS={'a':'v2','b':'v2','c':'v3','d':'v1'}
def main():
 out=D/'firing_pair_diagnostic_v1';out.mkdir(exist_ok=False);a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());meta=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));Y,X=np.indices((384,384));X-=160;Y-=160;rows=[];recs=[]
 for page,ver in VERS.items():
  reg=json.loads((D/f'firing_{page}_before_registered_v1/registration.json').read_text('utf8'))
  for rr in reg['frames']:
   n=rr['ref'];q=next(q for q in meta['frames']if q['ref']==n);bp=D/f'firing_{page}_before_joint_probe_{ver}/before_{n:03}.png';ap=D/f'firing_after_cleanup_v1/after_{n:03}.png';b=np.array(Image.open(bp));f=np.array(Image.open(ap));orig=f.copy();body=np.array(Image.open(ROOT/q['sources']['before']['body_path']));ex,ey=rr['eye_world']
   head=((X>=ex-12)&(Y<=ey+4)&(body>0))|((X>=ex-10)&(Y<=ey+1));hc=[{'xy':[int(x-160),int(y-160)],'candidate':int(b[y,x]),'canonical_new_body':int(body[y,x])}for y,x in np.argwhere(head&(b!=body))];b[head]=body[head]
   outside=(f>0)&(b==0);pts=[{'xy':[int(x-160),int(y-160)],'after_index':int(f[y,x])}for y,x in np.argwhere(outside)];f[outside]=0
   labs,num=label(f>0,np.ones((3,3)));sz=np.bincount(labs.ravel());small=[{'size':int(sz[k]),'coords':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,num+1)if sz[k]<10]
   win=q['window_world'];x0,y0,x1,y1=win;sl=np.s_[y0+160:y1+160,x0+160:x1+160];case=np.array(Image.open(D/f'firing_inputs_v1/after_case_{n:03}.png'));need(np.array_equal(f[sl],case[sl])and np.array_equal(b[sl],case[sl]),'Original gun window')
   for name,v in(('before',b),('after',f),('after_source',orig)):Image.fromarray(v).save(out/f'{name}_{n:03}.png')
   recs.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_sha256':digest(bp),'after_source':ap.relative_to(ROOT).as_posix(),'after_sha256':digest(ap),'head_corrections_from_same_new_body':hc,'boundary_clipped_diagnostic':pts,'components':int(num),'small_components':small,'original_case_exact':True,'before_index_sha256':sha(b.tobytes()),'after_index_sha256':sha(f.tobytes())})
   rows.append((f'pair {n}: head{len(hc)} edge{len(pts)}',[('new jacket',a.rgba(b,16)),('new bare source',a.rgba(orig,0)),('common edge DIAGNOSTIC',a.rgba(f,0))]))
 for i in range(0,16,4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',5)
 write(out/'report.json',{'scope':'새 재킷 머리와 팔의 경계 진단. 새 몸체 머리에서 복구한 좌표는 별도 기록. 맨팔 밖경계를 재킷에 제한한 열은 아직 미술 검토 전이며 최종 채택/동결이 아니다.','frames':recs,'total_source_head_corrections':sum(len(q['head_corrections_from_same_new_body'])for q in recs),'total_boundary_clipped_diagnostic':sum(len(q['boundary_clipped_diagnostic'])for q in recs),'native_packed':False,'runtime_verified':False});print(json.dumps({q['ref']:{'head':len(q['head_corrections_from_same_new_body']),'boundary':len(q['boundary_clipped_diagnostic']),'components':q['components'],'small':q['small_components']}for q in recs}))
if __name__=='__main__':main()
