"""새 벽12참조의 맨팔 기본층과 재킷 차분층을 source-bound로 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
PARENT='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18';PBS=(0,5,6,7,8)
def paths(n):
 if n%2:return D/'canonical_cases_probe_v2'/f'before_{n:03}.png',D/'costume_pair_probe_v2'/f'after_{n:03}.png'
 if n<61:return D/'firing_a_before_joint_probe_v2'/f'before_{n:03}.png',D/'firing_a_after_joint_probe_v5'/f'after_{n:03}.png'
 return D/'firing_b_before_joint_probe_v4'/f'before_{n:03}.png',D/'firing_b_after_joint_probe_v6'/f'after_{n:03}.png'
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());need(sha(a.data)==PARENT,'Parent');out=D/'joint_native_targets_v1';out.mkdir(exist_ok=False);frames=[];rows=[]
 allowed={56:{(-15,-6),(-8,-6),(-7,-6)},58:{(-15,-8)},60:{(-15,-8),(-1,-3)},62:set(),64:{(-3,-3),(-2,-3),(-8,-2),(-7,-2)},66:{(0,-2)}}
 for n in range(55,67):
  bp,ap=paths(n);before=np.array(Image.open(bp));after=np.array(Image.open(ap));local=[];need(before.shape==after.shape==(384,384)and before.dtype==after.dtype==np.uint8 and max(before.max(),after.max())<16,'Native format')
  outside=(after>0)&(before==0);points={(int(x-160),int(y-160))for y,x in np.argwhere(outside)};need(points==allowed.get(n,set()),f'Unexpected new-source silhouette mismatch {n}')
  for y,x in np.argwhere(outside):local.append({'world':[int(x-160),int(y-160)],'before_index':int(after[y,x]),'after_index':0,'reason':'맨팔 경계만 새 재킷 원화의 공통 외곽 안으로 제한. 옛 게임 몸체의 알파는 사용하지 않음.'})
  after[outside]=0;need(not((after>0)&(before==0)).any(),'After alpha')
  delta=(before!=after)|(before==15);layers={0:after,5:np.where(delta,before,0).astype(np.uint8),6:np.zeros_like(after),7:np.zeros_like(after),8:np.zeros_like(after)};need(np.array_equal(np.where(layers[5],layers[5],layers[0]),before),'Full composite')
  for pb in(6,7,8):need(not a.layer(n,pb)[0].any(),f'Unexpected armor layer {n}/{pb}')
  for pb,ar in layers.items():Image.fromarray(ar).save(out/f'layer{pb}_{n:03}.png')
  for form,ar in(('before',before),('after',after)):
   Image.fromarray(ar).save(out/f'{form}_{n:03}.png');need(label(ar>0,np.ones((3,3)))[1]==1,f'Disconnected {n}/{form}')
  if n%2==0:
   bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));y,x=np.nonzero(bar);gx=int(x.min());my=float(np.median(y[x==x.min()]));Y,X=np.indices(bar.shape);gate=(X>=gx)&(X<gx+8)&(Y>=my-3)&(Y<=my+5);need(np.array_equal(before[gate],bar[gate])and np.array_equal(after[gate],bar[gate]),f'Original muzzle {n}')
  frames.append({'ref':n,'before_source':bp.relative_to(D).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(D).as_posix(),'after_source_sha256':digest(ap),'local_source_corrections':local,'before_sha256':sha(before.tobytes()),'after_sha256':sha(after.tobytes()),'base_sha256':sha(after.tobytes()),'layers':{str(pb):sha(ar.tobytes())for pb,ar in layers.items()},'both_connected':True,'after_alpha_subset_before':True})
  if n%2==0:
   ob=np.array(Image.open(out/f'before_{n-1:03}.png'));oa=np.array(Image.open(out/f'after_{n-1:03}.png'));rows.append((f'Ultimate wall {n-1}/{n}',[('before idle',a.composite(0,15)[0]),('new before',a.rgba(ob,16)),('new before shot',a.rgba(before,16)),('after idle',a.composite(0,0)[0]),('new after',a.rgba(oa,0)),('new after shot',a.rgba(after,0))]))
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',5)
 write(out/'manifest.json',{'source_arc_sha256':PARENT,'frames':frames,'selected_refs':list(range(55,67)),'layer_semantics':{'0':'획득후 새 몸/맨팔','5':'획득전 새 재킷/소매 차분 및 팔레트15 보정','6/7/8':'기존 빈 층 보존'},'native_packed':False,'runtime_verified':False,'art_review_pending':True,'new_source_silhouette_clipped_pixels':sum(len(q['local_source_corrections'])for q in frames)});print(str(out))
if __name__=='__main__':main()
