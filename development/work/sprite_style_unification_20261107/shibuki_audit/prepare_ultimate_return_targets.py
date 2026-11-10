"""새156→새몸157 테두리→새몸158 역사빛. 기존157 가림예외는 복사하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page
P=H/'prepared_ultimate_victory01/PL02_U.ARC'
PARENT='ec7a6847ec8de42a3b25c1d0b87fdc96330bc61488c2296426ab24cbe9cfa9b8'
PBS=(0,5,6,7,8);REFS=(156,157,158);OUT=H/'ultimate_return_targets01'
def shift(a,dy):
 out=np.zeros_like(a);y,x=np.nonzero(a);need((y+dy).min()>=0 and (y+dy).max()<a.shape[0],'Shift clips');out[y+dy,x]=a[y,x];return out
def aura(a):
 m=a>0;inner=binary_dilation(m,np.ones((3,3)));outer=binary_dilation(m,np.ones((3,3)),iterations=2);v=a.copy();v[outer&~inner]=14;v[inner&~m]=9;return v
def main():
 need(not OUT.exists(),'Fresh target output');need(sha(P.read_bytes())==PARENT,'Wrong frozen parent');OUT.mkdir();a=Archive(P.read_bytes());s=H/'ultimate_return_contacts02';base={f:np.array(Image.open(s/f'{f}_156_indices.png'))for f in ('before','after')};need(not((base['after']>0)&(base['before']==0)).any(),'After outside before');beam=a.layer(159)[0];need(int((beam>0).sum())==1875 and sha(beam.tobytes())=='5940e1569783b6638ec8b6ac868a7537dfc234c7337ab68cfff68e7fcba1d02a','Historical beam changed');Image.fromarray(beam).save(OUT/'historical159_indices.png');forms={156:base,157:{f:aura(shift(v,-1))for f,v in base.items()},158:{}}
 for f,v in base.items():
  b=shift(v,-10);z=beam.copy();z[b>0]=b[b>0];forms[158][f]=z;Image.fromarray(b).save(OUT/f'{f}_158_body_indices.png')
 targets={};rows=[]
 for n,pair in forms.items():
  before,after=pair['before'],pair['after'];need(not((after>0)&(before==0)).any(),'Form alpha union differs');ls={0:after,5:np.where(same_rgba(a,before,after),0,before).astype(np.uint8),**{b:np.zeros_like(after)for b in (6,7,8)}};targets[str(n)]={}
  for b,v in ls.items():Image.fromarray(v).save(OUT/f'{n:03}_bank{b}_indices.png');targets[str(n)][str(b)]=sha(v.tobytes())
  for f,v in pair.items():Image.fromarray(v).save(OUT/f'{f}_{n:03}_indices.png');a.rgba(v,16 if f=='before'else 0).save(OUT/f'{f}_{n:03}.png')
  rows.append({'ref':n,'before_pixels':int((before>0).sum()),'after_pixels':int((after>0).sum()),'overlay_pixels':int((ls[5]>0).sum()),'after_outside_before':0})
 # 158 표시는 동일 배경 위의 신체색 차이만 전경 파츠에 저장한다.
 body_after=shift(base['after'],-10);body_before=shift(base['before'],-10);over=np.where(same_rgba(a,body_before,body_after),0,body_before).astype(np.uint8);need(np.array_equal(over,np.array(Image.open(OUT/'158_bank5_indices.png'))),'Beam unexpectedly needs costume overlay');Image.fromarray(over).save(OUT/'158_body_overlay_indices.png')
 sources={}
 for name in ('ultimate_return_inputs01','ultimate_return_native01','ultimate_return_arm_edit02','ultimate_return_arm_native02','ultimate_return_contacts02'):
  for q in sorted((H/name).rglob('*')):
   if q.is_file():sources[q.relative_to(ROOT).as_posix()]=sha(q.read_bytes())
 for name in ('prepare_ultimate_return_inputs.py','register_ultimate_return.py','prepare_return_arm_edit.py','probe_ultimate_return_contacts.py','prepare_ultimate_return_targets.py'):
  q=H/name;sources[q.relative_to(ROOT).as_posix()]=sha(q.read_bytes())
 rel=ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_ultimate_return_relations01'
 for name in ('report.json','conclusions.json'):q=rel/name;sources[q.relative_to(ROOT).as_posix()]=sha(q.read_bytes())
 write(OUT/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'targets':targets,'source_files':sources,'rows':rows,'new_art_policy':'새 기본형의 귀환 자세를 참고한 Ultimate 새156. 머리/몸통은 첫 새원화 보호, 팔 국소원화와 새발목/샌들 강체등록. 원US 자세 전체복원 주장은 하지 않는다.','157_policy':'각 새156 y−1의 Chebyshev1/2 밖테두리9/14. 옛157 내부51셀 및437/470px 역사 가림예외를 신작몸에 자동복사하지 않는 신규 제작정책.','158_policy':'현재159 역사빛1875px 전체를 뒤에 두고 각 새156 y−10을 앞에 합성. 원래빛의 숨은texel/18레코드도 패커에서 보호.','blank_aliases_protected':[0,141,142,88,89,231,232],'pure_effect_refs_unchanged':[159,160,161],'old_art_overlaid':False,'palette_changed':False,'runtime_verified':False,'visual_review_pending':True})
 for f,mask in (('before',15),('after',0)):
  page([(f'{n} parent {f}',a.composite(n,mask)[0])for n in REFS]+[(f'{n} new {f}',Image.open(OUT/f'{f}_{n:03}.png'))for n in REFS],a.composite(0,mask)[0],OUT/f'{f}_comparison.png',cols=3,scale=4)
 print(json.dumps({'manifest':sha((OUT/'manifest.json').read_bytes()),'rows':rows}))
if __name__=='__main__':main()
