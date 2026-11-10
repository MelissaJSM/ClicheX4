from pathlib import Path
import hashlib
import json

W = Path(__file__).resolve().parent
ROOT = W.parents[1]
R = W / 'runtime'
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def entry(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}

names = ['br31_stage_play/last.png']
names += [f'br31_hover_{s}_play/contact.png' for s in ('move', 'shot', 'retry')]
names += [f'br31_hover_move_review01/{s}_00.png' for s in ('forward_move', 'backward_move', 'stationary_hover')]
names += [f'br31_hover_shot_wide_review01/{s}_00.png' for s in ('forward_shot', 'backward_shot')]
names += ['br31_hover_shot_review01/stationary_shot_00.png']
names += ['br31_hover_retry_review01/right_facing_backward_00.png']
names += [f'br31_hover_retry_wide_review01/{s}_00.png' for s in ('right_facing_backward', 'left_facing_forward', 'left_facing_backward')]
names += [f'br31_hover_retry_fullwidth_review01/{s}_00.png' for s in ('left_facing_forward', 'left_facing_backward')]
assert len(names) == 16
recs = [read(R / f'br31_hover_{s}_play/evidence.json') for s in ('move', 'shot', 'retry')]
assert [r['frames'] for r in recs] == [144, 144, 191]
assert all(r['error'] is None and r['keys_released'] and not r['memory_written'] and not r['save_keys_sent'] for r in recs)
maps = [read(R / f'br31_hover_{s}/manifest.json')['mapping'] for s in ('move_review01', 'shot_wide_review01', 'retry_fullwidth_review01')]
assert [m['encoded_frames'] for m in maps] == [144, 144, 190]
session = ROOT / 'work/ver_buki_riko/emulator_sessions/20261108T011958033212Z'
assert read(session / 'close.local.json')['exited']
assert read(W / 'protection_checkpoint54.json')['passed']
assert read(R / 'br31_load_fourth.json')['source_record_authenticated']
evidence = [R / f'br31_hover_{s}_play/evidence.json' for s in ('move', 'shot', 'retry')]
evidence += [R / f'br31_hover_{s}/manifest.json' for s in ('move_review01', 'shot_wide_review01', 'shot_review01', 'retry_review01', 'retry_wide_review01', 'retry_fullwidth_review01')]
evidence += [R / 'br31_load_fourth.json', R / 'br31_ram_discovery.json', R / 'tools_binding_br31_fourth.json']
data = {
    'project': 'ver_buki_riko',
    'bin_sha256': 'ad4f2ceab100098e88977f383d314efd0337379feb70999989eaa53926332516',
    'source_asset_sha256': '8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397',
    'session': session.relative_to(ROOT).as_posix(),
    'fresh_boot': True,
    'recorded_captures': 479,
    'encoded_frames': 478,
    'actually_viewed_files': [dict(entry(R / n), actually_viewed=True) for n in names],
    'observations': [
        '새 부팅·복사 카드 DATA3의 포스아머(armor15, Ultimate0)에서 호버 이동·사격을 시험했다.',
        '오른쪽을 본 전진·정지 호버/사격을 확인했다. 최초 이동 시험의 후진은 일반 점프로 끝났으므로 성공으로 세지 않았다.',
        '후속 사격 시험과 간격을 늘린 재시도에서 오른쪽을 본 후진 및 왼쪽을 본 전진·후진 호버와 사격을 확인했다.',
        '직접 본 표본에서 어깨·팔·버스터, 발·추진 불꽃이 연결되며 추가 확정 절단이나 큰 크기 도약을 찾지 못했다.',
        '재시도 초기 크롭의 하단/좌측 잘림은 더 넓은 크롭으로 구분했다. 왼쪽 화면 끝에 실제로 걸친 일부 총구/머리 표본은 완전한 외형 검증에서 제외한다.',
    ],
    'limits': [
        '약16Hz 창 캡처이며 모든60Hz 표시나 참조별 RAM/GPU 업로드 추적을 수행한 것은 아니다.',
        '기본 의상+발파츠 조합과 나머지 부분아머, 작은 차량 머리/손잡이/발판은 이번 실기 범위가 아니다.',
        '불꽃·발사 섬광·화면 가장자리가 가린 모든 픽셀을 관측한 것은 아니다.',
        '모든 방향의 정지/일반/사격 세부 전환을 전수 검증했다는 의미가 아니다.',
    ],
    'evidence': [entry(p) for p in evidence],
    'protection': entry(W / 'protection_checkpoint54.json'),
    'session_closed': True,
    'memory_written': False,
    'F1_F3_sent': False,
    'all_character_work_complete': False,
}
p = R / 'br31_hover_summary.json'
assert not p.exists()
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(sha(p))
