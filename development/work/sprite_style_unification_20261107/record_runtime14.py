"""Bind reviewed actual window captures without equating samples with full coverage."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
W = Path(__file__).resolve().parent; ROOT = W.parents[1]; R = W / 'runtime'
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bind = lambda p: {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
p = argparse.ArgumentParser(); p.add_argument('name'); p.add_argument('--checkpoint', type=int, required=True)
p.add_argument('--target', nargs='+', type=int, required=True); a = p.parse_args()
watch, play, review = [R / (a.name + suffix) for suffix in ('_watch', '_play', '_review')]
obs, vid, gallery = [read(folder / name) for folder, name in ((watch, 'evidence.json'), (play, 'evidence.json'), (review, 'manifest.json'))]
close = ROOT / vid['session'] / 'close.local.json'
assert read(close)['exited'] and vid['error'] is None and vid['keys_released']
assert not vid['memory_written'] and not vid['save_keys_sent']
targets = set(a.target); observed = {f for b, f in obs['verified_bank_frames'] if b == 0}
pages = [ROOT / q['path'] for q in gallery['pages']]
assert a.name in ('shibuki_ultimate_dash14', 'nana_ultimate_run14')
findings = ['새 자세의 실제 업로드와 양방향 연결을 기록했다. 직접 열람한 비교판에서 추가 확정 절단은 찾지 못했다.']
limits = ['Ultimate 획득 후 수영복 폼의 시험이며, 캡슐 전 재킷 폼의 실기로 확대하지 않는다.',
          '각 참조 성공 표본과 모든 전환/모든60Hz 표시의 검증은 다르다.',
          '일부 비동기 관측의 실패/안정표본 부족은 원인이 확정되지 않은 상태로 별도 보존한다.']
summary = {'session': vid['session'], 'pid': vid['pid'], 'disc_sha256': vid['bin_sha256'],
    'fresh_boot': True, 'save_load_route': '시험카드 사본1 DATA3를 게임 메뉴에서 불러오기',
    'actual_window_captures': vid['frames'], 'encoded_webp_frames': Image.open(play / 'play.webp').n_frames,
    'recording': bind(play / 'evidence.json'), 'observer': bind(watch / 'evidence.json'),
    'verified_bank_frames': obs['verified_bank_frames'], 'new_targets_verified': sorted(targets & observed),
    'new_targets_unobserved': sorted(targets - observed),
    'unverified_events': [obs['events'][i] for i in obs['unverified_events']],
    'root_viewed_pages': [{**bind(q), 'root_actually_viewed': True} for q in pages],
    'findings': findings, 'limits': limits, 'close': bind(close),
    'all_character_runtime_complete': False, 'final_user_accepted': False}
dest = R / (a.name + '_summary.json'); assert not dest.exists()
dest.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', 'utf8')
record = W / f'root_review_checkpoint{a.checkpoint}.json'; assert not record.exists()
record.write_text(json.dumps({'actual_runtime_review_images': summary['root_viewed_pages'],
    'summary': bind(dest), 'findings': findings, 'limits': limits, 'final_user_accepted': False}, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'verified': len(targets & observed), 'missing': sorted(targets - observed),
                  'viewed_pages': len(pages), 'summary': str(dest), 'root_record_sha256': sha(record)}))
