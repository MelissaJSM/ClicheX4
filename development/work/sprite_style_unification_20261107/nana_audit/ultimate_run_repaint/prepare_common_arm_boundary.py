"""새 맨팔을 자르지 않고 두 새 원화 경계를 합치는 별도 비교 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def main():
 out=D/'common_arm_boundary_probe_v2';out.mkdir(exist_ok=False)
 a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes())
 need(np.array_equal(np.array(a.words[1:15]),np.array(a.words[17:31])),'Both costume palette colors')
 meta=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));rows=[];records=[]
 for n in range(2,33,2):
  bp=D/f'firing_pair_diagnostic_v1/before_{n:03}.png';ap=D/f'arm_source_shading_probe_v1/after_{n:03}.png'
  b=np.array(Image.open(bp));f=np.array(Image.open(ap));outside=(f>0)&(b==0)
  need(not(outside&~binary_dilation(b>0,np.ones((3,3)))).any(),'More than one native cell away')
  need(not np.isin(f[outside],[5,6,7,8,9,14,15]).any(),'Unexpected colored costume/head boundary')
  # 실제 새 맨팔 원화의 공통 신체 외곽만 사용한다. 색 생성/최근접 채움 없음.
  common=b.copy();common[outside]=f[outside]
  need(np.array_equal(common[b>0],b[b>0]),'Existing jacket pixels changed')
  need(label(common>0,np.ones((3,3)))[1]==1 and label(f>0,np.ones((3,3)))[1]==1,'Disconnected body')
  q=next(z for z in meta['frames']if z['ref']==n);x0,y0,x1,y1=q['window_world'];sl=np.s_[y0+160:y1+160,x0+160:x1+160]
  case=np.array(Image.open(D/f'firing_inputs_v1/after_case_{n:03}.png'));need(np.array_equal(common[sl],case[sl])and np.array_equal(f[sl],case[sl]),'Gun')
  points=[{'xy':[int(x-160),int(y-160)],'source_after_index':int(f[y,x])}for y,x in np.argwhere(outside)]
  for name,z in(('before',common),('after',f)):Image.fromarray(z).save(out/f'{name}_{n:03}.png')
  records.append({'ref':n,'jacket_source':bp.relative_to(ROOT).as_posix(),'jacket_source_sha256':digest(bp),
   'bare_source':ap.relative_to(ROOT).as_posix(),'bare_source_sha256':digest(ap),'same_pose_body_boundary_from_after':points,
   'before_index_sha256':sha(common.tobytes()),'after_index_sha256':sha(f.tobytes()),'all_existing_jacket_texels_exact':True,
   'bare_arm_alpha_and_shading_exact':True,'case_exact':True,'both_connected':True})
  rows.append((f'common source edge {n}: {len(points)} cells',[('jacket source',a.rgba(b,16)),('jacket + bare edge candidate',a.rgba(common,16)),('bare arm exact source',a.rgba(f))]))
 for i in range(0,16,4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',5)
 write(out/'report.json',{'scope':'새 맨팔의 외곽을 자르지 않는 공통 경계 후보. 재킷의 기존 모든 불투명 셀은 보존하고 바로1셀 이웃인 같은 자세의 맨팔 원화 경계만 재킷 바깥에 추가. 옛 게임 몸체/임의 색 생성 없음. 재킷 알파가 늘어난 사실을 명시하며 최종 미술 검토 전이다.',
  'frames':records,'jacket_alpha_additions':sum(len(q['same_pose_body_boundary_from_after'])for q in records),
  'bare_alpha_clipped':0,'native_packed':False,'runtime_verified':False,'art_review_pending':True})
 print(json.dumps({'jacket_additions':sum(len(q['same_pose_body_boundary_from_after'])for q in records),'output':str(out)}))
if __name__=='__main__':main()
