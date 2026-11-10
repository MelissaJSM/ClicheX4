"""노바 준비4와 돌진/효과4의 원0/5층 정책에 맞춰40층을 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PBS=(0,5,6,7,8);GROUPS=((213,214),(215,216),(217,),(218,),(219,),(220,));REFS=tuple(range(213,221))
PARENT=N/'ultimate_hover_repaint/packed_hover_candidate_v1/PL02_U.ARC';BEFORE='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
def comp(a,l,mask,arm=2):
 im=a.rgba(l[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(l[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 need(digest(PARENT)==BEFORE,'호버 동결 부모');a=Archive(PARENT.read_bytes());out=D/'targets_preview_v1';out.mkdir(exist_ok=False);all_layers={};frames=[];rows=[];rgba=0;zero=np.zeros((384,384),np.uint8)
 for n in REFS:
  if n<217:
   key=n if n%2 else n-1;bp=D/f'common_probe_v5/before_{key:03}_indices.png';ap=D/f'common_probe_v5/after_{key:03}_indices.png';before=np.array(Image.open(bp));after=np.array(Image.open(ap));need(not ((after>0)&(before==0)).any(),'맨팔 바깥 클립없음');desired=np.array(a.rgba(before,16));base_rgba=np.array(a.rgba(after));different=np.any(desired!=base_rgba,2);over=np.where(different,before,0).astype(np.uint8);l={0:after,5:over,6:zero,7:zero,8:zero}
   for mask in range(32):
    for arm in(1,2):need(comp(a,l,mask,arm).tobytes()==(a.rgba(before,16)if mask&1 else a.rgba(after)).tobytes(),'양폼 원소유 조립');rgba+=1
   source={'before':bp.relative_to(ROOT).as_posix(),'before_sha256':digest(bp),'after':ap.relative_to(ROOT).as_posix(),'after_sha256':digest(ap),'master_ref':key,'alias_policy':'현재 수용Nana 214=213/216=215 유지. 원US 각짝 exact복원 아님.'}
   if n==key:rows.append((str(n),[('old before',a.composite(n,15)[0]),('new before',comp(a,l,15)),('new after',comp(a,l,0)),('costume layer5',a.rgba(over,16))]))
  else:
   bodyp=D/'effects_probe_v1/body_217_indices.png';body=np.array(Image.open(bodyp));fxp=D/f'effects_probe_v1/effect_{n:03}_indices.png';fx=np.array(Image.open(fxp))if n!=217 else zero;l={0:zero if n==219 else body,5:fx,6:zero,7:zero,8:zero};source={'body':bodyp.relative_to(ROOT).as_posix(),'body_sha256':digest(bodyp),'effect':fxp.relative_to(ROOT).as_posix()if n!=217 else None,'effect_sha256':digest(fxp)if n!=217 else None,'actual_mask':15,'policy':'217..220 mask15 양폼공통.219 base빈/실루엣5,218220 본체0/효과5. 효과전체바이트보존과새몸 가림재등록은구분.'}
   for mask in range(32):
    for arm in(1,2):im=a.rgba(l[0]);im.alpha_composite(a.rgba(fx,16)if mask&1 else a.rgba(zero));need(comp(a,l,mask,arm).tobytes()==im.tobytes(),'원본체/효과 소유 조립');rgba+=1
  all_layers[str(n)]={str(pb):sha(z.tobytes())for pb,z in l.items()}
  for pb,z in l.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  frames.append({'ref':n,'sources':source,'layer_hashes':all_layers[str(n)]})
 helper.grid(rows,out/'preparation_layers.png',6);write(out/'manifest.json',{'parent_arc':PARENT.relative_to(ROOT).as_posix(),'parent_arc_sha256':BEFORE,'refs':REFS,'frames':frames,'targets':all_layers,'direct_rgba_combinations':rgba,'new_unique_bodies':[213,215,217],'derived_refs':[214,216,218,219,220],'native_packed':False,'runtime_verified':False,'scope':'새준비2×양의상4원화+215팔국소/돌진1몸체를8참조40층으로등록. 파생5를새고유그림5장으로세지않는다. 효과/부분조립 정책은출처보고와분리해검증.'});print(json.dumps({'layers':len(REFS)*5,'rgba':rgba,'manifest_sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
