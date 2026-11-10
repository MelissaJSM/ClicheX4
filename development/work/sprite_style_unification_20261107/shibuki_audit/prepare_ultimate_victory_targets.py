"""새 승리4 양폼에서20층을 만들고 원화/등록 출처를 고정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive
P=H/'prepared_ultimate_arrival_partial01/PL02_U.ARC'
PARENT='3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138'
PBS=(0,5,6,7,8);REFS=(204,205,206,207);OUT=H/'ultimate_victory_targets01'
SOURCES={204:'ultimate_victory_common_probe02',205:'ultimate_victory_common_probe02',206:'ultimate_victory_late_common02',207:'ultimate_victory_late_common02'}
def main():
 need(not OUT.exists(),'Fresh targets');need(sha(P.read_bytes())==PARENT,'Parent changed');OUT.mkdir();a=Archive(P.read_bytes());targets={};source={};rows=[]
 for n in REFS:
  s=H/SOURCES[n];before=np.array(Image.open(s/f'before_{n:03}_indices.png'));after=np.array(Image.open(s/f'after_{n:03}_indices.png'));need(not ((after>0)&(before==0)).any(),'After alpha leaks outside before')
  ls={0:after,5:np.where(same_rgba(a,before,after),0,before).astype(np.uint8),**{b:np.zeros_like(after)for b in(6,7,8)}};targets[str(n)]={}
  for b,v in ls.items():Image.fromarray(v).save(OUT/f'{n:03}_bank{b}_indices.png');targets[str(n)][str(b)]=sha(v.tobytes())
  for form,v,pal in(('before',before,16),('after',after,0)):Image.fromarray(v).save(OUT/f'{form}_{n:03}_indices.png');a.rgba(v,pal).save(OUT/f'{form}_{n:03}.png')
  rows.append({'ref':n,'new_source':SOURCES[n],'before_alpha':int((before>0).sum()),'after_alpha':int((after>0).sum()),'overlay_pixels':int((ls[5]>0).sum()),'after_alpha_outside_before':0})
 source_dirs=['ultimate_victory_inputs01/page01','ultimate_victory_inputs01/page02','ultimate_victory204_arm01','ultimate_victory206_arm01','ultimate_victory_native01','ultimate_victory_native02','ultimate_victory204_arm_native01','ultimate_victory206_arm_native01','ultimate_victory_common_probe02','ultimate_victory_late_common02']
 for directory in source_dirs:
  for p in sorted((H/directory).rglob('*')):
   if p.is_file():source[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
 for name in('register_ultimate_arrival_separate.py','probe_ultimate_victory_common02.py','probe_ultimate_victory_late_common02.py','prepare_ultimate_victory_targets.py'):
  p=H/name;source[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
 write(OUT/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'targets':targets,'source_files':source,'rows':rows,'new_art_policy':'새 기본형 수용 포즈의 관절/접지 좌표를 제작 참고로 사용한 Ultimate 새 원화. 원US 자세 전체 복원 주장이 아님.','common_policy':'새 재킷 원화의 의미상 머리/사지/손을 후폼에 공유. 의상은 새 전후 원화를 구분. 204/206 앞팔은 builtin 국소원화 donor만 사용.','contact_registration':'206/207 새 발목·샌들 y+1,207 새 높은 주먹·손목 y−1 강체등록. 접속 원행은 보존. 전신비율 변형 없음.','old_art_overlaid':False,'palette_changed':False,'source_scale':.125,'alpha_cutoff':128,'runtime_verified':False});print(sha((OUT/'manifest.json').read_bytes()))
if __name__=='__main__':main()
