"""Summarize reviewed actual gameplay, retaining missed transient observations."""
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
cards = read('work/ver_rin_nana/sprite_style_checkpoint10/cards/copies.json')
for row in cards:
    row['source_unchanged'] = digest(row['source']) == row['sha256']
    row['copy_unchanged'] = digest(row['copy']) == row['sha256']
assert not changed and all(row['source_unchanged'] and row['copy_unchanged'] for row in cards)
write(W / 'protection_checkpoint14.json', {'passed': True, 'protected_files': len(now),
    'mismatches': changed, 'files': now, 'additional_test_cards': cards,
    'utc': datetime.now(timezone.utc).isoformat()})

watch = read(R / 'rin_skills10_watch/evidence.json')
record = read(R / 'rin_skills10_play/evidence.json')
assert record['error'] is None and record['keys_released']
assert not record['memory_written'] and not record['save_keys_sent']
assert all(all(entries.values()) for entries in watch['resident_assets_still_exact'].values())
assert watch['disc_sha256'] == 'd55f32aad27362fb1041ef6f10d1bb9f997eff1dc7c4b57fcd69595960eacf01'
manifest = read(R / 'rin_skills10_review/manifest.json')
assert len(manifest['pages']) == 14
review = [{'path': row['path'], 'sha256': digest(row['path']), 'root_actually_viewed': True} for row in manifest['pages']]
assert read(Path(record['session']) / 'close.local.json')['exited']
valid = set(map(tuple, watch['verified_bank_frames']))
unverified = []
for i in watch['unverified_events']:
    entry = watch['events'][i]
    unverified.append({'event_index': i, **entry,
        'same_reference_verified_elsewhere_in_clip': (entry['bank'], entry['frame']) in valid})
ice_seen = [ref for ref in range(133, 144) if (1, ref) in valid]
ice_missing = [ref for ref in range(133, 144) if (1, ref) not in valid]
report = {
    'utc': datetime.now(timezone.utc).isoformat(), 'disc_version': 'sprite_style_unification_20261107_v10',
    'disc_sha256': watch['disc_sha256'],
    'rin_pl01_sha256': '70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8',
    'session': record['session'], 'pid': record['pid'], 'fresh_boot': True,
    'save_load_route': 'In-game copied memory-card1 DATA1, Iris dialogue then Space Port; no F3',
    'scene': 'Space Port stage10 area0', 'form': 'normal Rin; black palette not tested',
    'record': str(R / 'rin_skills10_play/evidence.json'),
    'watch': str(R / 'rin_skills10_watch/evidence.json'),
    'actual_window_frames': record['frames'], 'verified_unique_references': len(valid),
    'verified_bank_frames': watch['verified_bank_frames'],
    'new_ice_refs_verified': ice_seen, 'new_ice_refs_not_observed': ice_missing,
    'observed_animations_event_counts': dict(sorted(Counter(e['animation'] for e in watch['events']).items())),
    'unverified_transient_events': unverified,
    'native_loop_counter': watch['native_main_loop_counter'],
    'resident_assets_still_exact': watch['resident_assets_still_exact'],
    'root_actually_viewed': review,
    'findings': [
        '지상3타 좌우, 빙열참 좌우, 대시 공격, 공중 회전베기, 낙봉파를 실제 입력으로 발생시켰다.',
        '14개 실제 캡처판에서 새 지상 공격/빙열참의 머리·장갑·의상 연결을 확인했으며 추가 확정 분리 결함은 찾지 못했다.',
        '관측한 빙열참은 새11참조 중9개다.136/137은 이번 RAM/VRAM 표본에 없으므로 전수 실기 완료로 처리하지 않는다.',
        '회전베기는 아직v10의 기존 그림이다. 새 누적200후보의 회전 원화 검수와 이 실제 플레이 증거를 혼동하지 않는다.',
        '미검증 전환5건을 그대로 보존한다.105/184는 같은 참조의 다른 표본에서 일치했고,107/168/170은 안정 표본이 없었다. 이 사실만으로 게임 결함 또는 완전 통과를 단정하지 않는다.',
    ],
    'limits': [
        '약16fps 실제창 기록과 비동기 RAM/VRAM 관측이다. 모든60Hz 프레임과 효과에 가려진 픽셀의 전수 검사가 아니다.',
        '정상색 린의 이 시험 동작에 한정한다. 블랙색·사다리·탑승·전장면 회귀 검사나 사용자 최종 수용이 아니다.',
    ],
    'session_closed_normally': True, 'f1_f3_used': False, 'process_memory_written': False,
    'active_build_pointers_changed': False, 'protected_original_files_unchanged': True,
    'protection_report': str(W / 'protection_checkpoint14.json'),
    'user_accepted': False, 'all_character_runtime_complete': False,
}
write(R / 'rin_checkpoint10_summary.json', report)
print(json.dumps({'protected': len(now), 'actual_frames': record['frames'],
    'verified_refs': len(valid), 'ice_seen': ice_seen, 'ice_not_observed': ice_missing,
    'unverified_transients': len(unverified), 'viewed_pages': len(review)}))
