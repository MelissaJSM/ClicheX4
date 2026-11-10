"""새 이동/사격32의 전후 원화와 출처 경계를 네이티브5층 목표로 묶는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
PARENT='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
PBS=(0,5,6,7,8)
AFTER=('after_a_costume_probe_v3','after_b_costume_probe_v2','after_c_costume_probe_v2','after_d_costume_probe_v2')
def main():
 out=D/'joint_native_targets_v1';out.mkdir(exist_ok=False)
 src=N/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC';need(digest(src)==PARENT,'Parent');a=Archive(src.read_bytes())
 paths={};provenance={}
 for folder in AFTER:
  reg=json.loads((D/folder/'registration.json').read_text('utf8'))
  for r in reg['frames']:
   n=r['ref'];bp=ROOT/r['before_path'];ap=D/folder/f'after_{n:03}.png'
   need(digest(bp)==r['before_sha256']and sha(np.array(Image.open(ap)).tobytes())==r['native_sha256'],'Registered body')
   paths[n]=(bp,ap);provenance[n]={'registration':(D/folder/'registration.json').relative_to(ROOT).as_posix(),'registration_sha256':digest(D/folder/'registration.json')}
 edge=D/'common_arm_boundary_probe_v2';er=json.loads((edge/'report.json').read_text('utf8'))
 for r in er['frames']:
  n=r['ref'];bp,ap=edge/f'before_{n:03}.png',edge/f'after_{n:03}.png'
  need(sha(np.array(Image.open(bp)).tobytes())==r['before_index_sha256']and sha(np.array(Image.open(ap)).tobytes())==r['after_index_sha256'],'Common source boundary')
  paths[n]=(bp,ap);provenance[n]={'registration':(edge/'report.json').relative_to(ROOT).as_posix(),'registration_sha256':digest(edge/'report.json'),'jacket_boundary_sources':r['same_pose_body_boundary_from_after']}
 need(set(paths)==set(range(1,33)),'All32 references')
 layers_by_ref={};frames=[]
 for n,(bp,ap)in sorted(paths.items()):
  b,f=np.array(Image.open(bp)),np.array(Image.open(ap));need(b.shape==f.shape==(384,384)and max(b.max(),f.max())<16,'Format')
  need(not((f>0)&(b==0)).any(),'After must fit jacket')
  need(label(b>0,np.ones((3,3)))[1]==label(f>0,np.ones((3,3)))[1]==1,'Connected forms')
  layers={0:f,5:np.where((b!=f)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(f),7:np.zeros_like(f),8:np.zeros_like(f)}
  need(np.array_equal(np.where(layers[5],layers[5],layers[0]),b),'Before display')
  for pb in(6,7,8):need(not a.layer(n,pb)[0].any(),'Original nonempty layer')
  for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  for form,z in(('before',b),('after',f)):Image.fromarray(z).save(out/f'{form}_{n:03}.png')
  layers_by_ref[n]=layers;frames.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(ROOT).as_posix(),'after_source_sha256':digest(ap),'source_provenance':provenance[n],'base_sha256':sha(f.tobytes()),'before_sha256':sha(b.tobytes()),'after_sha256':sha(f.tobytes()),'layers':{str(pb):sha(z.tobytes())for pb,z in layers.items()}})
 checks=0
 for r in json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'))['frames']:
  n=r['ref'];x0,y0,x1,y1=r['window_world'];sl=np.s_[y0+160:y1+160,x0+160:x1+160];ls=layers_by_ref[n]
  for mask in range(16):
   for arm in(1,2):
    im=a.rgba(ls[0]);
    if mask&1:im.alpha_composite(a.rgba(ls[5],16))
    need(np.array_equal(np.array(im)[sl],np.array(a.composite(n,mask,arm)[0])[sl]),'Original all-mask muzzle');checks+=1
 rows=[]
 for n in range(1,33,2):
  ims=[]
  for mask in(15,0):
   ims.append(('before idle'if mask else'after idle',a.composite(0,mask)[0]))
   for ref in(n,n+1):
    ls=layers_by_ref[ref];im=a.rgba(ls[0]);
    if mask:im.alpha_composite(a.rgba(ls[5],16))
    ims.append((f'new {ref}',im))
  rows.append((f'run {n}/{n+1}',ims))
 for i in range(0,16,4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',4)
 write(out/'manifest.json',{'source_arc_sha256':PARENT,'frames':frames,'selected_refs':list(range(1,33)),
  'layer_semantics':{'0':'획득후 새 맨팔 몸체','5':'획득전 새 재킷 차분 및 palette15 보정','6/7/8':'기존 빈 층 보존'},
  'jacket_boundary_source_pixels':er['jacket_alpha_additions'],'bare_boundary_clipped':0,'source_rgb_skin_reregistration_pixels':57,
  'original_muzzle_rgba_checks':checks,'native_packed':False,'runtime_verified':False,'common_boundary_art_review_pending':True})
 print(json.dumps({'output':str(out),'references':len(frames),'muzzle_checks':checks}))
if __name__=='__main__':main()
