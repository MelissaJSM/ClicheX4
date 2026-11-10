"""Bind reviewed art, reproducible native packing, and independent evidence."""
from pathlib import Path
import sys,json,hashlib
import pack_ladder
import scripts.prepare_shibuki_armor_remaining
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_ladder07'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 assert not (out/'FROZEN.json').exists()
 assert read(out/'report.json')['passed'] and read(out/'reproduction.json')['passed']
 assert read(D/'ladder_components_native_checks.json')['passed']
 assert read(D/'native_sequence01/browser_verification.json')['passed']
 independent=W/'zero_audit/nana_base_ladder14_independent01'
 assert sha(independent/'report.json')=='dc4d6c320acaedd14bbe4232198c2d5a7726aadcdbea29e89adaa19ebe10f02c'
 assert sha(independent/'visual_review.json')=='494466afbb0beeb84ed501fa57b62c20ed98ea9f8c83851329dc7b8961f218b0'
 assert sha(W/'root_review_checkpoint105.json')=='7649de811f3fdacaeb6b77d618e5f4a868ea159d1fc3eba015456d270a537646'
 paths=set(D.glob('*.py'))
 for mod in list(sys.modules.values()):
  name=getattr(mod,'__file__',None)
  if name:
   p=Path(name).resolve()
   if p.suffix=='.py' and p.is_relative_to(ROOT) and '/work/tools/' not in p.as_posix():paths.add(p)
 for name in ('first_inputs01','first_art01','first_registered01','inputs_page02','art_page02','registered_page02','inputs_page03','art_page03','registered_page03','inputs_page04','art_page04','registered_page04','contact_registration02','shot_inputs01','shot_art01','shot_registered01','shot_modules03','common_legs02','joint_layers05'):
  folder=D/name;assert folder.is_dir(),name
  paths.update(p for p in folder.rglob('*') if p.is_file())
 lock={'scope':'선택한 새 원화·등록·부분파츠·패킹 코드 입력 잠금. 제외 후보를 최종안으로 취급하지 않음.','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted(paths)]}
 (out/'INPUT_FROZEN.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8')
 proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',D/'ladder_components.json',D/'ladder_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',independent/'report.json',independent/'visual_review.json',W/'root_review_checkpoint105.json']
 proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':read(out/'report.json')['refs'],'new_authored_body_refs':[143,144,146,149,151,153,154,183],'new_authored_arm_refs':[150,155],'derived_mirror_refs':[145,147,148,152],'preserved':['全非対象体・パレット・EXE・アニメーション表・判定・音声'],'runtime_verified':False,'user_accepted':False}
 proposal['preserved']=['비대상 몸체·팔레트·EXE·애니메이션 표·판정·음향']
 (out/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8');proof.append(out/'proposal.json')
 freeze={'frozen':True,'character':'nana','forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'나나 기본/포스 사다리14 새 세부묘사 후보. 원형 재현2·잘못된 입력7거부·원MIPS/GPU·448부분조합·독립/루트 시각·8원표38단계/1526canvas 검사 통과. 실기는 별도. joint_layers05 초기 status는 제작 당시 기록이며 이 동결 단계가 후속이다.','runtime_verified':False,'final_user_accepted':False}
 (out/'FROZEN.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'frozen':True,'input_files':len(paths),'sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
if __name__=='__main__':main()
