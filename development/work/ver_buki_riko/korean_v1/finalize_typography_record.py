"""Record the accepted typography revision and the subsequent label-only build."""
import json,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'work/ver_buki_riko/korean_v1'
BUILD=ROOT/'out/ver_buki_riko/korean_20261028T060610973785Z'
CANDIDATE=D/'integrated_proposal_v11'
SESSION='work/ver_buki_riko/emulator_sessions/20261028T060757944797Z'
def read(path):return json.loads(path.read_text('utf-8'))
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

manifest=read(BUILD/'manifest.json');proposal=read(CANDIDATE/'proposal.json')
assert sha(BUILD/'shibuki_riko.bin')==manifest['modified_bin']['sha256']
delta=read(CANDIDATE/'buster_delta_verification.json')
assert delta['changed_resources']==['PL00_U.ARC','PL02_U.ARC']
record={
 'build':str(BUILD.relative_to(ROOT)),
 'bin_sha256':manifest['modified_bin']['sha256'],
 'session':SESSION,
 'user_accepted_prior_build':'out/ver_buki_riko/korean_20261028T060024547794Z',
 'user_accepted_prior_sha256':'01e4166c738314811955893c3a20d4b767acc4f6257f80a78e4ea7aa72363b79',
 'user_acceptance_quote':'좋아 내가 테스트해보니 잘나왔네',
 'accepted_scope':'화면별 서체·로딩 풀네임·타이틀 균형 및 이어하기 반복 배경 수정에 대한 사용자 테스트 수용',
 'followup_request':'일시정지의 버스터를 시부키 버스터로 변경',
 'followup_changed_resources':delta['changed_resources'],
 'followup_changed_frames':{'PL00_U.ARC':[0],'PL02_U.ARC':[0]},
 'followup_runtime_visual_verified':True,
 'followup_runtime_verification_source':'사용자 테스트',
 'followup_user_acceptance_quote':'좋아 내가 테스트하니 제대로나왔어',
 'full_game_runtime_verified':False,
 'unit_tests_latest_run':212,
 'base_component_reproduction':'reproduction_v9_base/verification.json',
 'accepted_postprocess_reproduction':'integrated_proposal_v10/reproduction_verification.json',
 'followup_delta_verification':'integrated_proposal_v11/buster_delta_verification.json',
 'loading_background_protection':'integrated_proposal_v11/loading_names_verification.json',
 'typewriter_cpu_verification':'dialogue_full_v5/native_cpu_verification.json',
 'typewriter_time_series_verified':False,
 'typewriter_time_series_note':'세 관찰에서 진행 중 본문을 포착하지 못했다. 선택 입력도 포커스 또는 대기 상태 조건 미충족으로 전부 미전송. 실제 한 글자별 시간 측정 성공으로 기록하지 않는다.',
 'protected_inputs':'typography_final_preservation.json',
 'rejected_prior_build':'out/ver_buki_riko/korean_20261028T055415127114Z',
 'rejected_reason':'로딩 풀네임이 이어하기의 직접 UV 반복 배경과 충돌; v10에서 전체 하단48px 보존으로 수정',
}
save(D/'typography_runtime_record.json',record)
project_path=ROOT/'projects/ver_buki_riko/project.json';project=read(project_path)
project.update(latest_integrated_build=str(BUILD.relative_to(ROOT)),latest_integrated_bin_sha256=record['bin_sha256'],active_substage='KOREAN_TYPOGRAPHY_AND_BUSTER_USER_ACCEPTED')
save(project_path,project)
candidate_path=ROOT/'projects/ver_buki_riko/korean_candidate.json';candidate=read(candidate_path)
candidate.update(stage=project['active_substage'],proposal=str(CANDIDATE.relative_to(ROOT)),proposal_sha256=sha(CANDIDATE/'proposal.json'),coverage=proposal['coverage'],build=record['build'],bin_sha256=record['bin_sha256'],runtime_verified=False,full_game_runtime_verified=False,runtime_verified_scope=[],runtime_evidence=str((D/'typography_runtime_record.json').relative_to(ROOT)),reproduction='work/ver_buki_riko/korean_v1/integrated_proposal_v10/reproduction_verification.json',user_accepted_previous_build=record['user_accepted_prior_build'],user_acceptance_quote=record['user_acceptance_quote'],pending_runtime_check='시부키 버스터 문구만 사용자 최종 확인 대기; 기존 UI 수정은 v10 사용자 수용')
save(candidate_path,candidate)
candidate.update(runtime_verified=True,runtime_verified_scope=['user_accepted_typography_loading_full_names_title_balance_continue_background','user_accepted_shibuki_buster_pause_label'],user_acceptance_quote=record['followup_user_acceptance_quote'],pending_runtime_check='전체 스토리와 모든 UI 상태의 자동 전수 검수는 미완료; 이번 수정 범위는 사용자 수용')
save(candidate_path,candidate)
manifest.update(runtime_verified=False,full_game_runtime_verified=False,runtime_evidence=str((D/'typography_runtime_record.json').relative_to(ROOT)),user_accepted_previous_build=record['user_accepted_prior_build'],followup_label_static_verified=True)
save(BUILD/'manifest.json',manifest)
manifest.update(runtime_verified=True,runtime_verified_scope=candidate['runtime_verified_scope'],runtime_verification_source='user_test',user_acceptance_quote=record['followup_user_acceptance_quote'])
save(BUILD/'manifest.json',manifest)
print(json.dumps({'build':record['build'],'sha256':record['bin_sha256'],'user_accepted_previous_build':True,'latest_label_user_accepted':True}))
