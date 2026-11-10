"""사다리 진행/도구거부/허용된 독립 검사를 별도 상태파일에 기록한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}
def main():
 status={
 'scope':'나나 Ultimate 사다리14참조 상세 통일. 기존 동결 자원과 RN27 통합본은 변경하지 않음.',
 'complete':False,'native_packed_first7_candidate':True,'runtime_verified':False,
 'parent':ref(D.parent/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC'),
 'immutable_scope_snapshot':ref(D.parent/'scope_summary_v18/manifest.json'),
 'generated_candidates':{
  'first_bodies_143_144_146':{'source':ref(D/'a_v1/generated.png'),'bare_arm_source':ref(D/'a_arm_v1/generated.png'),'registration':ref(D/'a_arm_registered_v1/manifest.json'),'state':'허용된 원화의 손·머리·사지 공통화 후보. 최종미술/자원 동결 아님.'},
  'second_bodies_149_151_153':{'source':ref(D/'b_v1/generated.png'),'state':'후폼 하의가 기준 디자인과 달라 해당 의상 미채택. 기존 원화 보존, 수정/패킹 없음.'},
  'last_bodies_154_183':{'source':ref(D/'c_v1/generated.png'),'registration':ref(D/'c_registered_v1/registration.json'),'common':ref(D/'c_common_probe_v2/manifest.json'),'state':'별개 미제작4전신 생성/고정등록. 원발높이·154눈 exact, 새공통손·의상 경계 후보.'}
 },
 'blocked_correction':{
  'failure':ref(D/'b_costume_inputs_v1/generation_failure.json'),
  'request_id':'40512cd8-f6e7-4053-8b11-e04a67c8584e','tool_response':'HTTP400 moderation_blocked, output/sexual',
  'output_saved':False,'retry_performed':False,'bypass_performed':False,
  'policy':'루트의 재요청/우회 금지 지시를 유지한다. 이 하의의 색 교체/다른 경로 재요청으로 보정하지 않음.'
 },
 'permitted_first_three_checks':{
  'hand_share':ref(D/'a_grip_probe_v1/manifest.json'),
  'layers':ref(D/'a_layers_probe_v1/manifest.json'),
  'source_reconstruction':ref(D/'a_layers_probe_v1/source_reconstruction.json'),
  'refs':[143,144,146],'layers_count':15,'direct_rgba_combinations':192,
  'floor_y':24,'source_hand_cells_shared':[4,4,2],
  'visual_review_files':[ref(D/'a_grip_probe_v1/comparison.png'),ref(D/'a_layers_probe_v1/comparison.png'),ref(D/'a_layers_probe_v1/partial.png')],
  'visual_observation':'실제 세 판에서 손목·발목의 새 확정 단절을 찾지 못했다. 대기 옆 머릿결과 옷 명암은 유지된다.144의 이전 고립된 손끝과 새 손 모양 차이는 단순 전체팔 이동으로 맞추지 않으며 손바닥/손목 의미를 함께 검토한다.',
  'not_claimed':['최종 미술 수용','ARC 패킹','GPU/원MIPS 실행','전체사다리 반전 검증','게임 실기']
 },
 'current_first7_candidate':{'targets':ref(D/'first7_targets_v1/manifest.json'),'source_reconstruction':ref(D/'first7_targets_v1/source_reconstruction.json'),'refs':[143,144,145,146,147,154,183],'new_unique_bodies':5,'mirrored_refs':2,'native_packed':True,'arc':ref(D/'packed_first7_diagnostic_v1/PL02_U.ARC'),'verification':ref(D/'packed_first7_diagnostic_v1/verification.json'),'input_lock':ref(D/'packed_first7_diagnostic_v1/INPUT_FROZEN.json'),'reproduction':ref(D/'packed_first7_diagnostic_v1/reproduction.json'),'native_checks':ref(D/'native_first7_components_v1_native_checks.json'),'native_cycle':ref(D/'first7_native_cycle_v1/verification.json'),'root_final_review':'대기','independent_reader':'진행 대기','final_frozen':False,'user_accepted':False},
 'relation_read':ref(D.parent.parent/'zero_audit/nana_ultimate_ladder_relations01/conclusions.json'),
 'remaining':{
  'native_relation_read':'HUD읽기완료. 기존재킷4반전exact이나후폼159/244/183/150셀 차이. 새양폼반전은새공통몸체정책으로구분.',
  '154_183':'새공통층 후보 정적/최종자원 검토 필요.',
  '150_155':'새 사격팔 미제작. 실제 몸체/총구 관계를 읽은 뒤 입력 준비.',
  '145_147_148_152':'145/147은첫7후보에원재킷반전좌표로파생.148/152는보류149/151에연결되어미수정.',
  '149_151_153_costume':'거부된 의상 교정 미완료/미채택 유지.'
 }
 }
 frozen=D/'packed_first7_diagnostic_v1/FROZEN.json'
 if frozen.exists():
  status['immutable_scope_snapshot']=ref(D.parent/'scope_summary_v19/manifest.json')
  status['current_first7_candidate'].update({'root_final_review':ref(D.parent.parent/'root_review_checkpoint124.json'),'independent_reader':ref(D.parent.parent/'zero_audit/nana_ultimate_ladder_first7_independent01/report.json'),'final_frozen':True,'frozen':ref(frozen)})
  status['generated_candidates']['first_bodies_143_144_146']['state']='새전신6+맨팔3과 공통층을 검증하여 허용7 동결에 포함.'
  status['generated_candidates']['last_bodies_154_183']['state']='별개 새4전신·고정원점·공통손을 검증하여 허용7 동결에 포함.'
  status['remaining']['154_183']='허용7 동결에 포함. 실제 게임 검증은 별도.'
  status['remaining']['150_155']='보류149 몸체와 연결되므로 기존 raw/그림/권총 그대로 보존. 새 사격팔 미제작.'
  status['remaining']['145_147_148_152']='145/147 새양폼 반전은 허용7에 동결.148/152는 보류149/151에 연결되어 미수정.'
 p=D/'production_status.json';p.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}))
if __name__=='__main__':main()
