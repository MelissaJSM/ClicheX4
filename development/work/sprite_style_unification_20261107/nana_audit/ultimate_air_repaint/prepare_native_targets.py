"""새 얼티밋 공중 22참조의 후폼 기본층/전폼 재킷층 제작 후보를 모은다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
PARENT='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45';PBS=(0,5,6,7,8)
def paths(n):
 if n%2:
  return(D/'canonical_cases_probe_v1'/f'before_{n:03}.png',D/('costume43_boundary_v3'if n==43 else'costume_pair_probe_v2')/f'after_{n:03}.png')
 if n>=50:return tuple(D/'firing_reach_pair_probe_v2'/f'{form}_{n:03}.png'for form in('before','after'))
 return(D/'firing_joint_probe_v3'/f'before_{n:03}.png',D/'firing_costume_pair_probe_v1'/f'after_{n:03}.png')
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());need(sha(a.data)==PARENT,'Parent');out=D/'joint_native_targets_v2';out.mkdir(exist_ok=False);frames=[];rows=[]
 for n in range(33,55):
  bp,ap=paths(n);before=np.array(Image.open(bp));after=np.array(Image.open(ap));local=[]
  if n==38:
   need(after[163,155]==3,'Folded hand remnant changed');after[163,155]=0;local.append({'xy':[-5,3],'before':3,'after':0,'reason':'New nonfiring folded-hand outline is hidden by firing posture; detached after removing sleeve'})
  if n==44:
   corrected=np.array(Image.open(D/'costume43_boundary_v3/after_043.png'));old=np.array(Image.open(D/'costume_pair_probe_v2/after_043.png'));mask=corrected!=old
   need(np.array_equal(after[mask],old[mask]),'Far shoulder conflict');after[mask]=corrected[mask];local.append({'source':'costume43_boundary_v3/after_043.png','coordinates':json.loads((D/'costume43_boundary_v3/verification.json').read_text('utf8'))['coordinates_xy'],'reason':'Same far arm as new43; same source six-texel boundary restoration'})
  need(before.shape==after.shape==(384,384)and before.dtype==after.dtype==np.uint8 and max(before.max(),after.max())<16,'Native format')
  need(not((after>0)&(before==0)).any(),f'After alpha outside jacket {n}')
  layers={0:after,5:np.where(before!=after,before,0).astype(np.uint8),6:np.zeros_like(after),7:np.zeros_like(after),8:np.zeros_like(after)}
  need(np.array_equal(np.where(layers[5],layers[5],layers[0]),before),'Full composite')
  for pb in(6,7,8):need(not a.layer(n,pb)[0].any(),f'Unexpected existing armor layer {n}/{pb}')
  for pb,ar in layers.items():Image.fromarray(ar).save(out/f'layer{pb}_{n:03}.png')
  for form,ar in(('before',before),('after',after)):
   Image.fromarray(ar).save(out/f'{form}_{n:03}.png');need(label(ar>0,np.ones((3,3)))[1]==1,f'Disconnected {n}/{form}')
  if n%2==0:
   bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));y,x=np.nonzero(bar);gx=int(x.min());my=float(np.median(y[x==x.min()]));Y,X=np.indices(bar.shape);gate=(X>=gx)&(X<gx+8)&(Y>=my-3)&(Y<=my+5)
   need(np.array_equal(before[gate],bar[gate])and np.array_equal(after[gate],bar[gate]),f'Original muzzle {n}')
  frames.append({'ref':n,'before_source':bp.relative_to(D).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(D).as_posix(),'after_source_sha256':digest(ap),'local_source_corrections':local,'before_sha256':sha(before.tobytes()),'after_sha256':sha(after.tobytes()),'base_sha256':sha(layers[0].tobytes()),'layers':{str(pb):sha(ar.tobytes())for pb,ar in layers.items()},'both_connected':True,'after_alpha_subset_before':True})
  if n%2==0:
   oddbefore=np.array(Image.open(out/f'before_{n-1:03}.png'));oddafter=np.array(Image.open(out/f'after_{n-1:03}.png'))
   rows.append((f'Ultimate {n-1}/{n}',[('before idle',a.composite(0,15)[0]),('new before',a.rgba(oddbefore,16)),('new before shot',a.rgba(before,16)),('after idle',a.composite(0,0)[0]),('new after',a.rgba(oddafter,0)),('new after shot',a.rgba(after,0))]))
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',5)
 write(out/'manifest.json',{'source_arc_sha256':PARENT,'frames':frames,'selected_refs':list(range(33,55)),'layer_semantics':{'0':'acquired alternate costume','5':'pre-capsule jacket delta including palette15 remap','6/7/8':'originally blank; kept transparent'},'native_packed':False,'runtime_verified':False,'art_review_pending':True});print(str(out))
if __name__=='__main__':main()
