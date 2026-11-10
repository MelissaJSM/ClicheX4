"""실제 열람한 최종8판과 미실행 검증을 변경 없이 기록한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write

def main():
    d = H / 'prepared_ultimate_air01'
    out = H / 'ultimate_air_final_visual_review01.json'
    need(not out.exists(), 'Fresh report required')
    need(sha((d / 'PL02_U.ARC').read_bytes()) == '3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7', 'Candidate changed')
    sheets = [d / f'{form}_readback_{i:02}.png' for form in ('before', 'after') for i in range(4)]
    code = ['prepare_ultimate_air_targets.py', 'pack_ultimate_air_complete.py', 'register_ultimate_air_shot_arms.py', 'register_ultimate_air_extra_arm_fix.py', 'align_ultimate_air_shot_page01.py', 'align_ultimate_air_shot_page02.py', 'align_ultimate_air_shot_page03.py', 'align_ultimate_air_shot_page04.py']
    write(out, {'candidate_arc_sha256': sha((d / 'PL02_U.ARC').read_bytes()), 'target_lock_sha256': sha((H / 'ultimate_air_targets02/LOCK.json').read_bytes()), 'viewed_actual_readback_images': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sheets}, 'reviewed_display_count': 44, 'forms': ['Ultimate 캡슐 전 재킷', 'Ultimate 캡슐 후 수영복'], 'refs': list(range(33, 55)), 'observations': ['구형 공중 머리의 큰 단색면 대신 새 머릿결·귀 테두리·금테 장식이 실제 패킹 뒤에도 보인다.', '재킷의 칼라·지퍼·소매주름과 수영복의 맨팔/의상 경계를 구별하여 검토했다.', '사격짝은 같은 새 몸체를 유지하며 앞팔을 교체했다.42/44의 추가 팔은 국소 원화로 제거했고 팔 대신 드러난 머리만 두 의상에 공유했다.', '원화 전체가 달라진 국소 교정 결과를 전신으로 채택하지 않았다. 총열과 겹친 국소 영역은 승인34 모듈로 복구했다.', '54 재킷의 이전 굽힌팔 끝1px은 영역 밖에 남아 분리됨을 발견하여 새 원화 동일좌표의 투명을 등록했다.', '현재8판에서 추가 팔/몸체 분리/구형 흰소매 잔재를 발견하지 못했다. 이것은 실제 게임의 완전 검증을 뜻하지 않는다.'], 'casing_scope': '수용한 PL02 after34 총열60픽셀을 각 원총구 좌표로 평행이동. 옛각프레임 총열의 불균일형태/소매혼입도 동일하게 보존했다는 주장은 하지 않는다.', 'intermediate_rejected': ['ultimate_air_shot_native02의42/44 추가 팔', 'ultimate_air_extra_arm_native01의 총열 중첩은 진단용', 'ultimate_air_shot_aligned02는 총열 guard 실패 중간 출력', 'ultimate_air_targets01은 총열 불투명/보호영역 크기를 혼동한 검사 중단 출력'], 'validated': json.loads((d / 'verification.json').read_text('utf8')), 'registration_code_sha256': {name: sha((H / name).read_bytes()) for name in code}, 'not_tested_here': ['독립 구현 읽기 검사', '실제 게임CPU/GPU 렌더러', '에뮬레이터 공중 연속 조작', '사용자 최종 수용', '다른 미완료 모션의 통일화'], 'original_game_or_save_modified': False, 'ready_for_independent_review': True, 'whole_project_complete': False})
    print(sha(out.read_bytes()))

if __name__ == '__main__':
    main()
