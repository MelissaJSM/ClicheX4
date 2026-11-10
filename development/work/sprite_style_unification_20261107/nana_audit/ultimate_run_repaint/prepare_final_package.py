"""검증된 이동32 후보를 독립검사/통합용 새 경로로 모은다. 아직 동결 아님."""
from pathlib import Path
import sys,json,shutil
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D.parent/'native_restore'))
from preview_restore import digest,write,need
FINAL='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
def main():
 src=D/'packed_run_diagnostic_v1';out=D/'packed_run_candidate_v1';need(not out.exists(),'Fresh final candidate')
 need(digest(src/'PL02_U.ARC')==FINAL,'Candidate')
 proofpaths=[src/'verification.json',src/'extended_verification.json',D/'native_components_native_checks.json',D/'native_cycle_v1/verification.json']
 for p in proofpaths:need(json.loads(p.read_text('utf8'))['passed'],'Failed proof')
 ev=json.loads((src/'extended_verification.json').read_text('utf8'));need(ev['candidate_sha256']==FINAL and ev['reproduced_identical'],'Reproduction')
 out.mkdir()
 for name in('PL02_U.ARC','verification.json','extended_verification.json',*[f'readback_{i}.png'for i in range(1,5)]):shutil.copy2(src/name,out/name)
 for aid in(7,8,38,119,120,16,128):shutil.copy2(D/f'native_cycle_v1/timeline_{aid}.png',out/f'timeline_{aid}.png')
 prop=json.loads((src/'proposal.json').read_text('utf8'));prop['files']['PL02_U.ARC']['path']=(out/'PL02_U.ARC').relative_to(ROOT).as_posix()
 prop.update(changed_from_working_parent=list(range(1,33)),forms=['ultimate_before','ultimate_after'],freeze_pending='독립 읽기 및 최종 루트 미술 검토 이후 별도 FROZEN',runtime_verified=False)
 write(out/'proposal.json',prop)
 write(out/'baseline_binding.json',{'passed':True,'project':'ver_rin_nana','baseline_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','baseline_bin_sha256':prop['baseline_sha256'],
  'original_resource_sha256':prop['files']['PL02_U.ARC']['before'],'working_parent_sha256':prop['parent_arc_sha256'],'candidate_sha256':FINAL,
  'native_check_path':(D/'native_components_native_checks.json').relative_to(ROOT).as_posix(),'native_check_sha256':digest(D/'native_components_native_checks.json'),
  'explanation':'기존 미국판 원MIPS 검사 도구가 원기준 BIN/PL02와 실제 후보의 해시를 읽어 대조했다. 실제 게임 BIN 쓰기는 수행하지 않았다.'})
 # 현재 생산에 사용된 입력들을 해시로 고정한다. 새 후속 작업은 다른 폴더에 쓴다.
 exclude={'packed_run_diagnostic_v1','packed_run_candidate_v1','native_cycle_v1'}
 inputs=[]
 for p in sorted(D.rglob('*')):
  if p.is_file()and p.suffix.lower()in('.png','.json','.py','.txt')and not any(part in exclude or part=='__pycache__'for part in p.relative_to(D).parts):
   inputs.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
 write(out/'INPUT_FROZEN.json',{'inputs_fixed':True,'candidate_sha256':FINAL,'files':inputs,'scope':'이 후보 입력 고정. 최종 게임/미술 전체 완료나 FROZEN을 의미하지 않는다.'})
 write(out/'reproduction.json',{'passed':True,'candidate_sha256':FINAL,'same_process_rebuild_identical':True,'separate_output_reproduction':False,
  'producer_script_sha256':digest(D/'pack_native.py'),'targets_manifest_sha256':digest(D/'joint_native_targets_v1/manifest.json'),'rejection_count':len(ev['negative_cases'])})
 print(json.dumps({'out':str(out),'candidate_sha256':FINAL,'input_files':len(inputs),'proposal_sha256':digest(out/'proposal.json')}))
if __name__=='__main__':main()
