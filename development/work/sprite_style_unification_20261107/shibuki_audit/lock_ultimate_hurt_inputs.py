"""Ultimate 피격 새 원화/국소팔/공통부/원효과 출처 잠금."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
 out=H/'ultimate_hurt_locked_inputs01';need(not out.exists(),'Fresh lock');out.mkdir();report=json.loads((H/'ultimate_hurt_pack_probe01/report.json').read_text('utf8'));need(report['passed'],'Probe failed');files={}
 for name in('ultimate_hurt_inputs01','ultimate_hurt_native01','ultimate_hurt_native02','ultimate_hurt234_arm01','ultimate_hurt_common_probe02','ultimate_hurt_effect_probe02'):
  for p in sorted((H/name).rglob('*')):
   if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
 for name in('prepare_shibuki_ultimate_hurt_inputs.py','register_shibuki_ultimate_hurt.py','prepare_ultimate_hurt234_arm.py','inspect_ultimate_hurt_common.py','probe_ultimate_hurt_common.py','prepare_ultimate_hurt_effects.py','ultimate_hurt_common_inspection01/report.json','ultimate_hurt_common_inspection01/after_234_arm_donor_indices.png','prepared_hurt_base01/PL00_U.ARC','prepared_hurt_base01/FROZEN.json','prepared_ultimate_ladder01/FROZEN.json'):
  p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
 meta=json.loads((H/'ultimate_hurt_effect_probe02/manifest.json').read_text('utf8'))
 for n,h in meta['source_arrays'].items():need(sha((ROOT/n).read_bytes())==h,'Source changed');files[n]=h
 p=H.parent/'zero_audit/shibuki_hurt_sources01/report.json';need(sha(p.read_bytes())==meta['independent_source_report_sha256'],'Audit source changed');files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
 write(out/'LOCK.json',{'parent_sha256':report['parent_sha256'],'candidate_sha256':report['candidate_sha256'],'refs':meta['refs'],'files':files,'scope':'새원화2페이지+234맨팔국소1페이지·고정1/8등록·새공통머리/사지·각효과의실제출처.원본/실기수정없음.','pending':'독립reader·원MIPS/GPU·root최종미술·원순서및게임실기는별도'})
 print(json.dumps({'sha':sha((out/'LOCK.json').read_bytes()),'files':len(files)}))
if __name__=='__main__':main()
