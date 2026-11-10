"""이미 수행한 읽기 조사와 네 비교판의 실제 열람을 별도 결론으로 기록한다."""
from pathlib import Path
import hashlib
import html
import json

D = Path(__file__).resolve().parent
O = D / 'shibuki_standing85_92_relations01'
ROOT = D.parents[2]
sha = lambda b: hashlib.sha256(b).hexdigest()
p = O / 'report.json'
expected = '3fc0eb8beb650be2ad8e8706bfe00bb9634f2afebd68ac11d63a00de4ca3f1f9'
assert sha(p.read_bytes()) == expected
r = json.loads(p.read_text('utf8'))
relations = {(q['archive'], q['source'], q['target']): q for q in r['relations']}
frames = {(q['archive'], q['ref']): q for q in r['frames']}
selected_pairs = [(0, 87), (0, 92), (85, 86), (89, 90), (90, 91), (89, 91)]
quantified = []
for archive in r['archives']:
    for source, target in selected_pairs:
        q = relations[archive, source, target]
        ls = {}
        for layer, v in q['layers'].items():
            nonempty = (frames[archive, source]['layers'][layer]['opaque'] or
                        frames[archive, target]['layers'][layer]['opaque'])
            ls[layer] = {
                'nonempty': bool(nonempty),
                'changed_pixels': v['changed_pixels'],
                'changed_bbox_exclusive_end_world': v['changed_bbox'],
                'exact_rigid_within_plus_minus_3': v['exact_rigid_shifts'] if nonempty else None,
                'best_rigid_within_plus_minus_3': v['best_rigid_within3'] if nonempty else None,
            }
        quantified.append({'archive': archive, 'source': source, 'target': target,
                           'layers': ls, 'full_RGBA_changes': q['RGBA']})

findings = [
    {'subject': '87/92와 대기0', 'status': '로컬 정적 검증',
     'finding': '원US PL00/PL02 모두 87과92는 대기0의 동일 그림이나 작은 평행이동 별칭이 아니다. 원본 PL00 주층의 0→87은1141셀, 0→92는967셀 차이이며 머리·몸·팔·다리층도 각각 다르다.',
     'recommendation': '복귀 중 팔과 몸의 자세를 보존한다. 수용된 대기의 세부를 새 복귀 자세에 재사용하는 것은 새 제작정책으로 구분하고, 87/92를 통째로0에 치환하지 않는다.'},
    {'subject': '85/86', 'status': '로컬 정적 검증',
     'finding': '원본은 작은 사격 반동이지만 전신 같은좌표/±3 평행이동 exact가 아니다. PL00 주층391셀·다리층108셀, PL02 주층390셀 차이다. 현재 Shibuki PL00은 주층97셀 차이로 줄었고 머리5만 exact이며 다른 몸/팔/다리층은 다르다.',
     'recommendation': '85 새원화를86에 그대로 복사하지 않는다. 기존 수용된86의 국소 반동과 원손/발 기준을 별도 보존·검토한 후 파생 가능성을 판단한다.'},
    {'subject': '89/90/91', 'status': '로컬 정적 검증',
     'finding': '원본90/91은89의 팔만 교체한 그림이 아니다. PL00 주층89→90은876셀,90→91은896셀; 다리층은337셀/286셀 차이다. 실제 원판에서도 어깨·몸통 회전과 두 다리의 체중 이동이 보인다.',
     'recommendation': '89·90·91을 각각의 자세로 준비한다. 현재 PL00의89/90 머리층 동일 및91머리의 y+1 관계는 부분공유 근거일 뿐 전신 공통화 근거가 아니다.'},
    {'subject': '원 시간표와 종료', 'status': '원US EXE 바이트 검증',
     'finding': '표91은85→86→88→89→90→91→92이며 유지시간은2/5/3/8/7/5/96 calls이다. 표88/89/90/94에도87→92가 있다. 마지막92의6000005c는 relative_step0이므로 표 자체에서0번 대기로 자동 이동하지 않는다.',
     'recommendation': '원순서와 시간을 유지하고 마지막92 이후 대기 전환은 별도 게임 상태 동작과 구분한다. 이번 조사에서 플레이 트리거를 새로 실행한 것은 아니다.'},
    {'subject': '효과 분리', 'status': '기존 독립 근거 연결',
     'finding': '이번85/86/87/89/90/91/92의 조립은 CLUT0/1이다. 88의89 x−1 및83셀 효과는 앞선 standing_special_relations01 조사를 연결한다. 여기서 CLUT2가 없다는 사실을 별도 런타임 탄환/효과가 없다는 주장으로 확대하지 않는다.',
     'recommendation': '89를 바꿀 때88의 몸체 연동과 원효과 형상·색·위치를 별도로 보존한다.'},
]

sharing = []
for archive in ('current_PL00', 'current_PL02'):
    for ref in r['refs']:
        f = frames[archive, ref]
        sharing.append({'archive': archive, 'ref': ref, 'raw_owners': f['raw_owners'],
                        'shared_record_users_by_layer': {
                            layer: values['record_owners'] for layer, values in f['layers'].items()
                        }})
boards = []
for item in r['boards']:
    b = ROOT / item['path']
    assert sha(b.read_bytes()) == item['sha256']
    boards.append({**item, 'actual_viewed': True, 'mode': '정수4배 동일원점 정적 비교, mask0/15·arm2',
                   'note': '표의 원본/현재 네 판을 직접 열람했다. 실기 화면이나 새 후보 미술 수용은 아니다.'})

out = {
    'scope': '시부키85~92의 원US/현재 PL00·PL02 관계 후속 읽기. 기존 원화·ARC·게임·동결 파일 변경 없음.',
    'report': {'path': p.relative_to(ROOT).as_posix(), 'sha256': expected},
    'archives': r['archives'], 'findings': findings, 'quantified_pairs': quantified,
    'sharing': sharing,
    'sharing_interpretation': [
        'record_users는 주소를 하나 이상 공유하는 사용자이며 전체 레이어나 전체 그림의 동일성을 뜻하지 않는다.',
        '현재 PL02의0/87/92/119/135/142는 주층의 일부 레코드를 공유한다. 새 대상 레코드를 분리하고 비대상 전체 소비 타일과 조립을 보호해야 한다.',
        '현재 PL02 빈6/7/8의 shared record도 비대상 목록에 포함했다. 빈층 exact는 몸체 별칭 증거가 아니다.',
        '현재 PL00 raw0은0/1/142, PL02 raw0은0/142와 공유하며89는 양쪽 모두88과 공유한다.',
    ],
    'tables': [{k: v for k, v in t.items() if k != 'unfiltered_source_callers'} for t in r['tables']],
    'caller_limitation': '기존 coverage의 unfiltered_source_callers에는 같은 번호를 쓰는 Zero 함수가 섞여 있어 X 발동 조건의 근거로 사용하지 않았다. 이번에는 실제 X 테이블 포인터와 모든 step bytes만 원EXE와 대조했다.',
    'visual': boards,
    'visual_findings': [
        '원본의87은 발사팔을 내리는 중간 자세,92는 팔을 더 내린 별도 마무리 자세로 보이며 idle0와 일치하지 않는다.',
        '현재 Shibuki89/90/91은 대기보다 머릿결과 옷의 내부 세부가 단순한 별도 자세로 읽힌다. 특히90/91의 하체 차이는 팔만 교환하는 방식으로 보존되지 않는다.',
        '현재 기본형87/92는 대기와 많은 부위를 공유하지만 포스 및Ultimate의 전체 의상까지 같은 픽셀이라는 근거는 없다.',
    ],
    'not_performed': ['원화 생성/수정', '패킹', '새MIPS 실행', '에뮬레이터 실기', '사용자 수용 판정'],
    'minimum_art_keys': '현재 조사만으로 전신 원화 최소개수를 확정하지 않는다.85/89 첫 제작 뒤86/87/92의 국소 파생을 별도 입증할 수 있지만90/91은 고유 자세로 남긴다.',
    'overall_complete': False,
}
cp = O / 'conclusions.json'
cp.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', 'utf8')
esc = html.escape
rows = ''.join('<tr><td>' + esc(f['subject']) + '</td><td>' + esc(f['finding']) +
               '</td><td>' + esc(f['recommendation']) + '</td></tr>' for f in findings)
pics = ''.join('<p>' + esc(Path(b['path']).stem) + '</p><a href="' + esc(Path(b['path']).name) +
               '"><img src="' + esc(Path(b['path']).name) + '"></a>' for b in boards)
page = '<!doctype html><meta charset="utf-8"><title>시부키85~92 관계 조사</title><style>body{font:16px/1.6 sans-serif;background:#17212b;color:#eee;margin:24px}a{color:#9dd7ff}table{border-collapse:collapse;max-width:1500px}td,th{border:1px solid #647384;padding:10px;vertical-align:top}img{max-width:100%;image-rendering:pixelated}</style><h1>시부키85~92 원본·현재 관계</h1><p>정적 읽기와 네 판 실제 열람. 원화/자원 변경 및 실기 없음. 전체 미술 완료 판정 아님.</p><p><a href="report.json">원시 조사 JSON</a> · <a href="conclusions.json">결론·공유 보호 목록 JSON</a></p><table><tr><th>대상</th><th>근거</th><th>제작 시 구분</th></tr>' + rows + '</table><p>현재PL02의0/87/92/119/135/142 일부 조립 공유와89/88 raw 공유를 보호한다. 빈층 공유를 전신 별칭으로 해석하지 않는다.</p>' + pics
(O / 'INDEX.html').write_text(page, 'utf8')
assert sha(p.read_bytes()) == expected
print(json.dumps({'conclusions_sha256': sha(cp.read_bytes()), 'report_sha256': expected,
                  'actual_boards_viewed': len(boards)}, ensure_ascii=False))
