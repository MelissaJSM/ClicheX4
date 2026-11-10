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
cards = read('work/ver_rin_nana/sprite_style_checkpoint11/cards/copies.json')
for row in cards:
    row['source_unchanged'] = digest(row['source']) == row['sha256']
    row['copy_unchanged'] = digest(row['copy']) == row['sha256']
assert not changed and all(row['source_unchanged'] and row['copy_unchanged'] for row in cards)
write(W / 'protection_checkpoint15.json', {'passed': True, 'protected_files': len(now),
    'mismatches': changed, 'files': now, 'additional_test_cards': cards,
    'utc': datetime.now(timezone.utc).isoformat()})

watch = read(R / 'rin_skills11_watch/evidence.json')
record = read(R / 'rin_skills11_play/evidence.json')
assert record['error'] is None and record['keys_released']
assert not record['memory_written'] and not record['save_keys_sent']
assert all(all(entries.values()) for entries in watch['resident_assets_still_exact'].values())
assert watch['disc_sha256'] == 'bfedca226e27bb34fcef3520faf62ee60a53357d007db08cf2cca46456dd5532'
manifest = read(R / 'rin_skills11_review/manifest.json')
assert len(manifest['pages']) == 16
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
assert not ice_missing
assert all((1,ref) in valid for ref in (144,161,163,165,167,169,171,173,175,146,156,158))
report = {
    'utc': datetime.now(timezone.utc).isoformat(), 'disc_version': 'sprite_style_unification_20261107_v11',
    'disc_sha256': watch['disc_sha256'],
    'rin_pl01_sha256': 'd3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8',
    'session': record['session'], 'pid': record['pid'], 'fresh_boot': True,
    'save_load_route': 'In-game copied memory-card1 DATA1, Iris dialogue then Space Port; no F3',
    'scene': 'Space Port stage10 area0', 'form': 'normal Rin; black palette not tested',
    'record': str(R / 'rin_skills11_play/evidence.json'),
    'watch': str(R / 'rin_skills11_watch/evidence.json'),
    'actual_window_frames': record['frames'], 'verified_unique_references': len(valid),
    'verified_bank_frames': watch['verified_bank_frames'],
    'new_ice_refs_verified': ice_seen, 'new_ice_refs_not_observed': ice_missing,
    'new_spin_and_entry_refs_verified': [ref for ref in (144,161,163,165,167,169,171,173,175) if (1,ref) in valid],
    'new_followthrough_refs_verified': [ref for ref in (146,156,158) if (1,ref) in valid],
    'new_ladder_saber_refs_not_observed': [ref for ref in (197,212) if (0,ref) not in valid],
    'observed_animations_event_counts': dict(sorted(Counter(e['animation'] for e in watch['events']).items())),
    'unverified_transient_events': unverified,
    'native_loop_counter': watch['native_main_loop_counter'],
    'resident_assets_still_exact': watch['resident_assets_still_exact'],
    'root_actually_viewed': review,
    'findings': [
        '정상색 린의 용염인·회전베기·빙열참 좌우와 지상3타·대시 공격을 새 부팅에서 실제 입력으로 발생시켰다.',
        '16개 실제 캡처판을 직접 검토했고 새 회전 몸체와 용염인 후속 자세에 추가 확정 분리·크기 급변은 찾지 못했다.',
        '높은 이단점프에서 빙열참을 다시 사용하여133..143의 새11참조를 모두 RAM/VRAM에서 관측했다.',
        '새 회전8참조와 진입144, 후속146/156/158을 관측했다. 이번 갱신의197/212는 사다리 베기 시작/복귀이며 실제 관측하지 않았다.',
        '비동기 읽기가 안정화되지 않은109/115의 전환2건은 미검증으로 보존한다. 과거 시험의 관측과 이번 표본을 혼합하지 않는다.',
    ],
    'limits': [
        '약16fps 실제창 기록과 비동기 RAM/VRAM 관측이다. 모든60Hz 프레임과 효과에 가려진 픽셀의 전수 검사가 아니다.',
        '정상색 린의 이 시험 동작에 한정한다. 블랙색·사다리·탑승·전장면 회귀 검사나 사용자 최종 수용이 아니다.',
    ],
    'session_closed_normally': True, 'f1_f3_used': False, 'process_memory_written': False,
    'active_build_pointers_changed': False, 'protected_original_files_unchanged': True,
    'protection_report': str(W / 'protection_checkpoint15.json'),
    'user_accepted': False, 'all_character_runtime_complete': False,
}
write(R / 'rin_checkpoint11_summary.json', report)
print(json.dumps({'protected': len(now), 'actual_frames': record['frames'],
    'verified_refs': len(valid), 'ice_seen': ice_seen, 'ice_not_observed': ice_missing,
    'unverified_transients': len(unverified), 'viewed_pages': len(review)}))
