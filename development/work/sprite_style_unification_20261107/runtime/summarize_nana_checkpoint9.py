"""Record the reviewed, fresh-boot Nana test without changing a game or save."""
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
cards = read('work/ver_rin_nana/sprite_style_checkpoint9/cards/copies.json')
for row in cards:
    row['source_unchanged'] = digest(row['source']) == row['sha256']
    row['copy_unchanged'] = digest(row['copy']) == row['sha256']
assert not changed and all(row['source_unchanged'] and row['copy_unchanged'] for row in cards)
write(W / 'protection_checkpoint12.json', {
    'passed': True, 'protected_files': len(now), 'mismatches': changed,
    'files': now, 'additional_test_cards': cards,
    'utc': datetime.now(timezone.utc).isoformat(),
})
watch = read(R / 'nana_ultimate01_watch/evidence.json')
record = read(R / 'nana_ultimate01_play/evidence.json')
assert record['error'] is None and record['keys_released']
assert not record['memory_written'] and not record['save_keys_sent']
assert watch['resident_assets_still_exact'] and not watch['unverified_events']
assert watch['disc_sha256'] == 'f00e6cf3f582294d0de0e96ff8b9adf55628c0185997b07cb994ac01ea1c301e'
manifest = read(R / 'nana_ultimate01_review/manifest.json')
assert len(manifest['pages']) == 15
# All fifteen specific boards have now been opened by root, including charge_02.
review = [{'path': row['path'], 'sha256': digest(row['path']), 'root_actually_viewed': True} for row in manifest['pages']]
report = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'disc_version': 'sprite_style_unification_20261107_v9',
    'disc_sha256': watch['disc_sha256'],
    'nana_pl02_sha256': '122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18',
    'session': record['session'], 'pid': record['pid'],
    'fresh_boot': True, 'save_load_route': 'In-game copied memory-card 1 DATA3; no F3',
    'scene': 'Space Port stage 10 area 0', 'costume': 'Ultimate after capsule, swimsuit',
    'character': watch['character'], 'armor': watch['player_armor'], 'ultimate': watch['ultimate_or_black'],
    'record': str(R / 'nana_ultimate01_play/evidence.json'),
    'watch': str(R / 'nana_ultimate01_watch/evidence.json'),
    'actual_window_frames': record['frames'],
    'verified_unique_references': len(watch['verified_bank_frames']),
    'verified_bank_frames': watch['verified_bank_frames'],
    'observed_animations_event_counts': dict(sorted(Counter(e['animation'] for e in watch['events']).items())),
    'native_loop_counter': watch['native_main_loop_counter'],
    'unverified_events': watch['unverified_events'],
    'resident_assets_still_exact': watch['resident_assets_still_exact'],
    'root_actually_viewed': review,
    'findings': [
        '새 공중 동작의 머릿결/얼굴/의복 세부, 좌우 점프사격과 착지 전환을 실제 창 캡처에서 확인했다.',
        '검토한 표본에서 새 공중 팔/총 연결의 추가 확정 결함이나 갑작스러운 체형 축소를 찾지 못했다.',
        '서서 일반/차지 발사, 이동사격, 대시도 관측했다. 기존 Ultimate 대시의 머릿결/얼굴 단순함은 대기·새 공중보다 남아 있어 후속 재작업 목록에 유지했다.',
    ],
    'limits': [
        'Ultimate 획득 후 폼만 시험했다. 재킷/기본/포스, 벽/사다리/특수기/등장/승리/탑승 전수 실기가 아니다.',
        '창 캡처 약16fps로 모든60Hz 표시는 담지 못했다. 비동기 RAM/VRAM 검증은 관측한 업로드 표본이며 이펙트에 가려진 최종 화면 전체 픽셀 일치를 뜻하지 않는다.',
        '새 벽12와 그 이후 원화는 이 v9 BIN에 포함되지 않았다.',
        '사용자 최종 수용이나 네 캐릭터 전체 미술 완료가 아니다.',
    ],
    'session_closed_normally': True, 'f1_f3_used': False, 'process_memory_written': False,
    'active_build_pointers_changed': False, 'protected_original_files_unchanged': True,
    'protection_report': str(W / 'protection_checkpoint12.json'),
    'user_accepted': False, 'all_character_runtime_complete': False,
}
assert (Path(record['session']) / 'close.local.json').exists()
write(R / 'nana_checkpoint9_summary.json', report)
print(json.dumps({'protected': len(now), 'actual_frames': record['frames'], 'verified_refs': len(watch['verified_bank_frames']), 'viewed_pages': len(review)}))
