"""첫3 중144/146의 기존 재킷 반전 위치를 새 양폼에 명시적으로 적용한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PAIRS=((144,145,-1),(146,147,0));PBS=(0,5,6,7,8)
def mirrored(z,k):
 y,x=np.nonzero(z);xx=320-x+k;need(np.all((xx>=0)&(xx<384)),'반전캔버스');out=np.zeros_like(z);out[y,xx]=z[y,x];return out
def full(a,n):
 z=a.layer(n)[0].copy()
 for pb in (8,5,7,6):v=a.layer(n,pb)[0];z[v>0]=v[v>0]
 return z
def composite(a,ls,mask,arm):
 im=a.rgba(ls[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes());need(digest(parent)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29','부모')
 audit=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ladder_relations01/report.json';need(digest(audit)=='353e70e04744969589557ba347b9825ae0a35c0b1e639a382c0ce27d2a248d18','독립관계 보고')
 src=D/'a_layers_probe_v1';out=D/'a_mirror_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for sn,tn,k in PAIRS:
  oldb=full(a,tn);need(np.array_equal(mirrored(full(a,sn),k),oldb),'기존재킷반전exact');oldadiff=int((mirrored(a.layer(sn)[0],k)!=a.layer(tn)[0]).sum());need(oldadiff==({145:159,147:244}[tn]),'후폼기존차이')
  ls={pb:mirrored(np.array(Image.open(src/f'layer{pb}_{sn:03}.png')),k)for pb in PBS}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{tn:03}.png')
  sourceb=np.array(Image.open(D/f'a_grip_probe_v1/before_{sn:03}_indices.png'));sourcea=np.array(Image.open(D/f'a_grip_probe_v1/after_{sn:03}_indices.png'));b=mirrored(sourceb,k);v=mirrored(sourcea,k)
  for form,z in(('before',b),('after',v)):Image.fromarray(z).save(out/f'{form}_{tn:03}_indices.png')
  hashes=[]
  for mask in range(32):
   for arm in (1,2):im=composite(a,ls,mask,arm);expected=a.rgba(b,16)if mask&1 else a.rgba(v);need(im.tobytes()==expected.tobytes(),'반전후32마스크');hashes.append(sha(im.tobytes()))
  rows.append((str(tn),[('old before',a.composite(tn,15)[0]),('new before mirror',a.rgba(b,16)),('old after',a.composite(tn,0)[0]),('new after mirror',a.rgba(v))]))
  records.append({'source_ref':sn,'target_ref':tn,'world_x_formula':f'-source_x{k:+d}','world_y_unchanged':True,'old_before_mirror_exact':True,'old_after_mismatch_pixels':oldadiff,'new_after_is_new_common_body_policy':True,'layers':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'direct_rgba_combinations':64,'rgba_hashes':hashes})
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'parent_sha256':digest(parent),'relation_report':audit.relative_to(ROOT).as_posix(),'relation_report_sha256':digest(audit),'source_target_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'source_manifest_sha256':digest(src/'manifest.json'),'pairs':records,'scope':'기존 재킷의 원반전 좌표를 새 양폼 공통몸체에 적용한 후보. 이전 후폼은반전exact아니므로 복원/원5층exact라고 주장하지 않는다.149/151/153 보류원화나그파생148/152는 처리하지 않음.','native_packed':False,'runtime_verified':False});print(json.dumps({'new_mirror_refs':2,'target_layers':10,'rgba_combinations':128,'manifest_sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
