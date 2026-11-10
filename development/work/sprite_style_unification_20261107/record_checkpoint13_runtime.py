"""Bind actual v13 captures, limited visual review, and protected inputs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from PIL import Image

W = Path(__file__).resolve().parent
ROOT = W.parents[1]
R = W / 'runtime'
read = lambda p: json.loads(p.read_text('utf8'))
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
def bind(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
def write(p, obj):
    assert not p.exists(), p
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', 'utf8')

check = subprocess.run(['powershell', '-NoProfile', '-Command',
    '(Get-Process epsxe* -ErrorAction SilentlyContinue | Measure-Object).Count'],
    capture_output=True, text=True, check=True)
assert check.stdout.strip() == '0', check.stdout
protected = {}
for name, old in read(W/'protection_before.json')['files'].items():
    p = ROOT/name
    current = {'size': p.stat().st_size, 'sha256': sha(p)}
    assert current == old, name
    protected[name] = current
cards = []
for mode in ['ver_buki_riko', 'ver_rin_nana']:
    folder = ROOT/'work'/mode/'sprite_style_checkpoint13/cards'
    rows = read(folder/'copies.json')
    if mode == 'ver_buki_riko': rows += [read(folder/'fourth_copy.json')]
    for row in rows:
        assert sha(ROOT/row['source']) == sha(ROOT/row['copy']) == row['sha256']
        cards.append({k: row[k] for k in ['source', 'copy', 'sha256']})
write(W/'protection_checkpoint20.json', {'passed': True, 'protected_files': len(protected),
    'files': protected, 'test_cards': cards, 'epsxe_process_count': 0,
    'checked_utc': datetime.now(timezone.utc).isoformat()})

all_images = []
def viewed(paths):
    rows = [{**bind(p), 'root_actually_viewed': True} for p in paths]
    all_images.extend(rows)
    return rows

selections = []
for short, who, directory in [('br', 'riko', 'br13_selection_review_v2'),
                               ('rn', 'rin', 'rn13_selection_review')]:
    play = R/f'{short}13_selection_play'
    evidence = read(play/'evidence.json')
    gpu = read(R/f'{short}13_selection_gpu.json')
    assert gpu['passed'] and gpu['bytes_verified'] == 40960
    assert evidence['error'] is None and not evidence['memory_written'] and not evidence['save_keys_sent']
    with Image.open(play/'play.webp') as im: encoded = im.n_frames
    images = viewed(sorted((R/directory).glob('selection_*.png')))
    assert len(images) == 3
    selections.append({'character': who, 'session': evidence['session'], 'pid': evidence['pid'],
        'disc_sha256': evidence['bin_sha256'], 'actual_window_frames': evidence['frames'],
        'encoded_webp_frames': encoded, 'atlas_upload': bind(R/f'{short}13_selection_gpu.json'),
        'recording': bind(play/'evidence.json'), 'root_actually_viewed': images,
        'findings': '선택 공격·복귀·빛기둥과 로딩 전환 확인. 관측 장면에서 새 고정 깨짐을 발견하지 못함.',
        'limits': '32개 모든 표시의 실기 전수 검증과 다름. 전체 atlas 바이트 일치는 별도 검증.',
        'fresh_boot': True, 'session_closed': True})
write(R/'selection_checkpoint13_summary.json', {'runs': selections,
    'protection': bind(W/'protection_checkpoint20.json'),
    'all_character_runtime_complete': False, 'user_accepted': False})

dash = []
for form in ['base', 'fourth']:
    name = f'shibuki_{form}_dash13'
    play, watch = R/(name+'_play'), R/(name+'_watch')
    e, obs = read(play/'evidence.json'), read(watch/'evidence.json')
    assert e['error'] is None and not e['memory_written'] and not e['save_keys_sent']
    targets = set(range(67, 85)) | ({93, 94} if form == 'fourth' else set())
    refs = {f for b, f in obs['verified_bank_frames'] if b == 0}
    if form == 'base':
        pages = sorted((R/(name+'_review')).glob('*.png'))
        assert len(pages) == 12
    else:
        pages = [R/(name+'_review_v2')/(n+'.png') for n in
            ['ground_right_00', 'ground_left_00', 'air_right_00', 'air_right_01',
             'air_left_00', 'air_left_01', 'fire_right_00', 'fire_left_00']]
    with Image.open(play/'play.webp') as im: encoded = im.n_frames
    dash.append({'form': form, 'session': e['session'], 'pid': e['pid'],
        'disc_sha256': e['bin_sha256'], 'actual_window_frames': e['frames'],
        'encoded_webp_frames': encoded, 'verified_bank_frames': obs['verified_bank_frames'],
        'new_targets_verified': sorted(targets & refs), 'new_targets_missing': sorted(targets - refs),
        'unverified_events': [obs['events'][i] for i in obs['unverified_events']],
        'resident_assets_still_exact': obs['resident_assets_still_exact'],
        'watch': bind(watch/'evidence.json'), 'recording': bind(play/'evidence.json'),
        'root_actually_viewed': viewed(pages), 'fresh_boot': True, 'session_closed': True,
        'limits': ['기본형은 공중대시 능력이 없어93/94 실기 대상이 아님. 물보라가 일부 몸을 가림.'
                   if form == 'base' else '포스아머68은 이번 실기에서 미관측. 양쪽93/94는 검증.',
                   '비동기 실패 표본의 원인 미확정. 같은 참조의 다른 성공 표본과 구분.',
                   '약16fps 창 기록과 RAM/GPU 관측이며 모든60Hz 프레임 검사 아님.'],
        'findings': '직접 열람한 범위에서 추가 고정 팔·망토 분리/비정상 확장 없음. 질감·연결 확인.'})
write(R/'shibuki_checkpoint13_summary.json', {'runs': dash,
    'protection': bind(W/'protection_checkpoint20.json'),
    'all_character_runtime_complete': False, 'user_accepted': False})

write(W/'root_review_checkpoint42.json', {'actual_runtime_review_images': all_images,
    'findings': ['시부키 기본대시12판·포스대시8판, 리코/린 선택 각3판 직접 검토.',
                 '선택의 최신 상세도 반영 및 대시의 팔/망토/복귀 연결 확인.'],
    'limits': ['기본형 물보라 가림, 포스68 미관측, 비동기 실패 표본 원인 미확정.',
               '포스 검토하지 않은4개 후반 페이지와 이전 좁은 크롭은 이번 증거에 포함하지 않음.',
               '전 캐릭터 전체 품질 완료 또는 사용자 수용 아님.'],
    'summaries': [bind(R/'selection_checkpoint13_summary.json'), bind(R/'shibuki_checkpoint13_summary.json')],
    'final_user_accepted': False})

corrections = []
for row in read(R/'prior_clip_frame_counts13.json'):
    folder = R/row['name']
    e = read(folder/'evidence.json')
    decoded = []
    with Image.open(folder/'play.webp') as im:
        for i in range(im.n_frames):
            im.seek(i); im.load(); decoded.append(im.info['timestamp']/1000)
    corrections.append({**row, 'recording': bind(folder/'play.webp'),
        'maximum_absolute_label_error_seconds': max(abs(t-e['capture_times'][i]) for i,t in enumerate(decoded)),
        'decoded_frame_times_seconds': decoded})
write(R/'prior_clip_timing_correction13.json', {'clips': corrections,
    'correction': 'WebP가 같은 인접 캡처를 합쳐 일부 이전 비교판의 capture_times[index] 라벨에 오차가 있었다. 원영상 픽셀과 RAM/GPU 검증 결과는 바뀌지 않는다.',
    'new_helpers': [bind(W/'review_dash_runtime13.py'), bind(W/'review_selection_runtime.py')],
    'new_timing_rule': '디코드된 WebP timestamp/duration을 사용한다. 영상프레임 수와 원창 캡처 수를 구분한다.'})
print(json.dumps({'protected': len(protected), 'test_cards': len(cards), 'root_viewed_pages': len(all_images),
    'base_new_verified': len(dash[0]['new_targets_verified']), 'fourth_new_verified': len(dash[1]['new_targets_verified'])}))
