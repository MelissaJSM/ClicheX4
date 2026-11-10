"""Record the BR15 runtime milestone without re-auditing frozen sprite assets."""
from pathlib import Path
import hashlib
import html
import json
import os
import re

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'work/sprite_style_unification_20261107'
D = Path(__file__).parent
PREV = D / 'full_scope_matrix02/coverage.json'
OUT = D / 'full_scope_matrix03'


def read(p):
    return json.loads(p.read_text('utf8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


assert sha(PREV) == 'd7967d529167a201d2cf63b667225bb73198d171dfd6015c5653a97534dfaa53'
j = read(PREV)
previous_evidence = dict(j['evidence'])
j['previous_snapshot'] = {'path': PREV.relative_to(ROOT).as_posix(), 'sha256': sha(PREV)}
for e in previous_evidence.values():
    assert sha(ROOT / e['path']) == e['sha256'], e['path']


def evidence(key, path, expected, purpose):
    assert sha(path) == expected, str(path)
    j['evidence'][key] = {'path': path.relative_to(ROOT).as_posix(),
                          'sha256': expected, 'purpose': purpose}


evidence('shibuki_run15_runtime', B / 'runtime/shibuki_run15_summary.json',
         '6e2e38d6095a8837ca46fefb7f2c7a7bb9a583e195e64d8208819ea57f833edd',
         '기본288·포스287·추가차지192 실제 창. 새 이동32 모두 각 폼 RAM/GPU 성공 표본, 미확정4건 별도.')
evidence('shibuki_run15_root_views', B / 'root_review_checkpoint82.json',
         '618f1a3eff80e2841b8b424d8fe0565a0d32da63f897a2b589098c59735869e7',
         '루트가 실제 열람한 기본/포스 이동32판과 추가차지4판. 이 장부 작성자의 새 이미지 열람 아님.')
r = read(ROOT / j['evidence']['shibuki_run15_runtime']['path'])
assert r['disc_sha256'] == j['integration']['br15']['bin_sha256']
assert [x['actual_captures'] for x in r['runs']] == [288, 287, 192]
assert [len(x['root_actually_viewed']) for x in r['runs']] == [16, 16, 4]
assert [len(x['unverified_events']) for x in r['runs']] == [3, 1, 0]
assert all(x['new_references_verified'] == list(range(1, 33)) for x in r['runs'][:2])
assert r['f1_f3_used'] is False and r['process_memory_written'] is False
assert r['active_build_pointers_changed'] is False
protection = r['protection']
evidence('shibuki_run15_protection', ROOT / protection['path'], protection['sha256'],
         '두 세션 종료 후 보호27. 원본·승인본·F1 등80파일 및 시험카드5쌍 보존 기록.')

for c in j['cells']:
    if c['character'] != 'shibuki':
        continue
    if c['category'] == 'run':
        if c['form'] in ('base', 'fourth'):
            run = r['runs'][0 if c['form'] == 'base' else 1]
            c['note'] = ('1..32는381d83 동결·BR15 통합.1은 수용 대기0 재사용이다. '
                         f"새 부팅 {run['actual_captures']}창에서32참조 모두 RAM/GPU 일치 표본 확보. "
                         f"비동기 미확정 사건{len(run['unverified_events'])}건은 별도로 보존한다. "
                         '모든60Hz 전환·부분아머·무기효과의 전수 실기나 사용자 최종수용은 아니다.')
            c['art_review'] = ('기존 재추출12판 및 독립8판 열람 근거 유지. '
                               '루트가 이번 폼의 실제 플레이16판을 직접 열람하여 추가 확정 파츠 분리·축소·윤곽 손실을 찾지 못했다. '
                               '이 장부 갱신은 보고서와 해시 연결이며 이미지 재검사는 하지 않았다.')
            c['runtime_coverage'] = {
                'evidence': 'shibuki_run15_runtime', 'run': run['name'],
                'actual_captures': run['actual_captures'],
                'new_references_with_successful_ram_gpu_sample': run['new_references_verified'],
                'root_viewed_boards': len(run['root_actually_viewed']),
                'unverified_events': run['unverified_events'],
                'all_60hz_transitions_verified': False,
                'all_partial_armor_combinations_verified': False,
            }
            c['evidence'] += ['shibuki_run15_runtime', 'shibuki_run15_root_views', 'shibuki_run15_protection']
        else:
            c['note'] = ('Ultimate3..32는 기존 새 원화 통합,1/2는 수용 세부 보존. '
                         '이번 BR15 이동32 대표 실기는 기본/포스 두 폼이며 Ultimate 실기로 확대하지 않는다.')
    if c['category'] == 'special' and c['form'] == 'fourth':
        c['note'] += (' BR15 추가 포스 차지샷 양방향192창/4판은 몸체 상주와 화면 발사·복귀 확인이다. '
                      '별도 효과 객체 각각의 GPU 업로드 전수 추적은 아니다.')
        c['evidence'] += ['shibuki_run15_runtime', 'shibuki_run15_root_views']
    c['evidence'] = list(dict.fromkeys(c['evidence']))

j['next_work'] = [p for p in j['next_work'] if p['scope'] != 'BR15 기본/포스 이동32']
j['completed_milestones_since_previous'] = [{
    'scope': 'BR15 기본/포스 이동·사격32 대표 실기 및 추가 포스 차지샷',
    'actual_captures': 767, 'root_viewed_boards': 36,
    'evidence': ['shibuki_run15_runtime', 'shibuki_run15_root_views', 'shibuki_run15_protection'],
    'unverified_events': 4, 'all_gameplay_verified': False,
    'limits': r['limits'],
}]
j['coverage_limits'].append(
    'BR15 새32의 각 폼 성공 표본이 있어도 기본29/16/74 및 포스9의 미확정 사건4건을 성공으로 덮지 않는다. '
    '약16fps 창767개·루트36판은 모든60Hz 전환/부분아머/효과 버퍼 수명 검증이 아니다.')
j['snapshot_summary'] = ('BR15/RN17 통합 기준. 이전 장부의 아트·후보 범위는 유지하고 '
                         'BR15 기본/포스 이동32 및 차지샷 대표 실기 근거만 추가. 전체 미술 작업은 계속 진행 중.')
assert len(j['cells']) == 144
assert j['all_art_complete'] is False and j['all_gameplay_verified'] is False
for c in j['cells']:
    for key in c['evidence']:
        assert key in j['evidence'], key
for key, e in previous_evidence.items():
    assert j['evidence'][key] == e
OUT.mkdir(exist_ok=True)
(OUT / 'coverage.json').write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n', 'utf8')

esc = html.escape


def link(key):
    e = j['evidence'][key]
    href = os.path.relpath(ROOT / e['path'], OUT).replace('\\', '/')
    return f'<a href="{esc(href)}">{esc(key)}</a>'


page = ['<!doctype html><html lang="ko"><meta charset="utf-8">',
        '<title>전체 폼·모션 범위 BR15 RN17 · 실기 갱신03</title>',
        '<style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547;position:sticky;top:0}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
        '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>BR15 / RN17 · 12폼 × 12범주. <b>수정 수는 미술 완료율이 아닙니다.</b></p>',
        '<p class="notice">시부키 기본/포스 새 이동32 모두 실제 RAM/GPU 일치 표본을 확보했습니다. 추가 차지샷을 포함해767창·루트36판이며, 비동기 미확정4건은 별도입니다. 전체60Hz·부분아머·효과의 전수 검증은 아닙니다. 시부키 사다리와 나나 피격 등 후속 미술 작업은 계속됩니다.</p>',
        '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix02/COVERAGE.html">이전 스냅샷</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ 보충판</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ 보충판</a></p>',
        '<p>새 실기 근거: ' + ' · '.join(link(k) for k in ('shibuki_run15_runtime', 'shibuki_run15_root_views', 'shibuki_run15_protection')) + '</p>',
        '<h2>다음 작업</h2><table><tr><th>담당</th><th>범위</th><th>상태</th></tr>']
for p in j['next_work']:
    page.append('<tr>' + ''.join('<td>' + esc(p[k]) + '</td>' for k in ('owner', 'scope', 'stage')) + '</tr>')
page.append('</table>')
for char, name in {'shibuki': '시부키', 'nana': '나나', 'riko': '리코', 'rin': '린'}.items():
    for form, form_name in j['forms'].items():
        cells = [c for c in j['cells'] if c['character'] == char and c['form'] == form]
        if not cells:
            continue
        page.append(f'<h2>{name} · {esc(form_name)}</h2><table><tr><th>범주</th><th>상태·참조</th><th>판단·남은 범위</th><th>실제 열람·근거</th></tr>')
        for c in cells:
            states = '<br>'.join(esc(s['label'] + ': ' + s['refs']) for s in c['states']) or '별도 사본 범위'
            page.append('<tr><td>' + esc(j['categories'][c['category']]) + '</td><td>' + states + '</td><td>' + esc(c['note']) + '</td><td><small>' + esc(c['art_review']) + '</small><details><summary>근거</summary>' + '<br>'.join(link(k) for k in c['evidence']) + '</details></td></tr>')
        page.append('</table>')
page.append('<h2>한계</h2><ul>' + ''.join('<li>' + esc(s) + '</li>' for s in j['coverage_limits']) + '</ul></html>')
(OUT / 'COVERAGE.html').write_text('\n'.join(page), 'utf8')
targets = re.findall(r'href="([^"]+)"', (OUT / 'COVERAGE.html').read_text('utf8'))
assert all((OUT / html.unescape(p)).resolve().is_file() for p in targets)
assert sha(PREV) == j['previous_snapshot']['sha256']
verification = {
    'passed': True, 'cells': 144, 'evidence_files': len(j['evidence']),
    'checked_local_links': len(targets), 'broken_links': 0,
    'prior_snapshot_preserved_sha256': sha(PREV),
    'inherited_evidence_unchanged': len(previous_evidence),
    'new_art_or_runtime_test_by_this_script': False, 'browser_test_performed': False,
    'all_art_complete': False, 'game_or_art_modified': False,
}
(OUT / 'verification.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'json_sha256': sha(OUT / 'coverage.json'),
                  'html_sha256': sha(OUT / 'COVERAGE.html'), **verification}))
