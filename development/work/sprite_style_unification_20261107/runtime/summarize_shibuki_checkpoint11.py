"""Record reviewed v11 Rising Fire evidence without promoting the build."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

W = Path('work/sprite_style_unification_20261107')
R = W / 'runtime'
def read(path):
    return json.loads(Path(path).read_text('utf8'))
def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')

baseline = read(W / 'protection_before.json')['files']
now = {name: {'size': Path(name).stat().st_size, 'sha256': digest(name)} for name in baseline}
changed = [name for name in baseline if baseline[name] != now[name]]
cards = read('work/ver_buki_riko/sprite_style_checkpoint11/cards/copies.json')
for row in cards:
    row['source_unchanged'] = digest(row['source']) == row['sha256']
    row['copy_unchanged'] = digest(row['copy']) == row['sha256']
assert not changed and all(row['source_unchanged'] and row['copy_unchanged'] for row in cards)
write(W / 'protection_checkpoint16.json', {'passed': True, 'protected_files': len(now),
    'mismatches': changed, 'files': now, 'additional_test_cards': cards,
    'utc': datetime.now(timezone.utc).isoformat()})
watch = read(R / 'shibuki_rising11_watch/evidence.json')
record = read(R / 'shibuki_rising11_play/evidence.json')
assert record['error'] is None and record['keys_released']
assert not record['memory_written'] and not record['save_keys_sent']
assert all(all(entries.values()) for entries in watch['resident_assets_still_exact'].values())
assert not watch['unverified_events']
assert watch['disc_sha256'] == 'db5f870db9545547d530e67db98ea17d2cbc20fdddd36eb6ad5446de905c3b99'
new_refs = [100, 101, 102, 103, 104, 231, 232]
assert all([0, ref] in watch['verified_bank_frames'] for ref in new_refs)
manifest = read(R / 'shibuki_rising11_review/manifest.json')
assert len(manifest['pages']) == 12
review = [{'path': row['path'], 'sha256': digest(row['path']), 'root_actually_viewed': True} for row in manifest['pages']]
closed = read(Path(record['session']) / 'close.local.json')
assert closed['exited']
report = {
    'utc': datetime.now(timezone.utc).isoformat(), 'disc_version': 'sprite_style_unification_20261107_v11',
    'disc_sha256': watch['disc_sha256'],
    'shibuki_pl02_sha256': 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d',
    'session': record['session'], 'pid': record['pid'],
    'fresh_boot': True, 'save_load_route': 'In-game copied memory-card 1 DATA3; no F3',
    'scene': 'Space Port stage 10 area 0', 'costume': 'Ultimate after capsule, swimsuit',
    'character': watch['character'], 'armor': watch['player_armor'], 'ultimate': watch['ultimate_or_black'],
    'weapon': 4, 'ordinary_pause_menu_selection': True,
    'record': str(R / 'shibuki_rising11_play/evidence.json'),
    'watch': str(R / 'shibuki_rising11_watch/evidence.json'),
    'actual_window_frames': record['frames'], 'verified_unique_references': len(watch['verified_bank_frames']),
    'verified_bank_frames': watch['verified_bank_frames'], 'all_seven_rising_refs_verified': new_refs, 'new_hand_corrected_refs': [103,104],
    'observed_animations_event_counts': dict(sorted(Counter(e['animation'] for e in watch['events']).items())),
    'native_loop_counter': watch['native_main_loop_counter'], 'unverified_events': watch['unverified_events'],
    'resident_assets_still_exact': watch['resident_assets_still_exact'], 'root_actually_viewed': review,
    'findings': [
        '일반 라이징 파이어 지상/공중과 차지 상승의 양방향을 실제 게임에서 발생시키고7참조 업로드를 모두 검증했다.',
        '12개 실제 캡처 비교판에서 새103/104의 올린 손과 불꽃 출발이 같은 쪽에 놓이는 것을 직접 확인했다. 기존 반대손 어긋남은 이번 표본에서 찾지 못했다.',
        '손 교정은 네 의상의 미술·독립·원MIPS/GPU 검사를 마쳤지만 이 실제 게임은 Ultimate 후폼에 한정한다.',
        '발사 종료 후 기존 공중 자세의 단순한 머리/몸 묘사 차이는 여전히 보인다. 후속 공중22 재작업은 아직v11에 미포함이다.',
    ],
    'limits': [
        'Ultimate 획득 후 폼만 시험했다. 기본/포스/재킷 및 다른 캐릭터의 이 중간판 전수 실기가 아니다.',
        '약16fps 실제 창 기록과 비동기 RAM/VRAM 업로드 표본이며 모든60Hz 표시나 불꽃에 가려진 최종 픽셀까지 검증한 것은 아니다.',
        '미술 수정 전 대비 전체 게임 회귀 검사나 사용자 최종 수용이 아니다.',
    ],
    'session_closed_normally': True, 'f1_f3_used': False, 'process_memory_written': False,
    'active_build_pointers_changed': False, 'protected_original_files_unchanged': True,
    'protection_report': str(W / 'protection_checkpoint16.json'),
    'user_accepted': False, 'all_character_runtime_complete': False,
}
write(R / 'shibuki_checkpoint11_summary.json', report)
print(json.dumps({'protected': len(now), 'actual_frames': record['frames'],
    'verified_refs': len(watch['verified_bank_frames']), 'viewed_pages': len(review), 'hand_origin_observed': True, 'pending_art': 'remaining ordinary air22'}))
