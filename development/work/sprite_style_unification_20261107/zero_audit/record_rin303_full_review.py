"""Record completed visual inspection; never mutate frozen resources."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
O = D / 'rin_extension/all_unique_review303'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inventory = json.loads((O / 'inventory.json').read_text('utf8'))
source = ROOT / inventory['source']
assert sha(source) == inventory['source_sha256'] == '1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
assert len(inventory['pages']) == 58
expected = {f'{v}_{n:02}.png' for v in ('normal', 'black') for n in range(29)}
assert {p['file'] for p in inventory['pages']} == expected
for page in inventory['pages']:
    page.update(viewed=True, actual_view_image=True, sha256=sha(O / page['file']))
inventory['all_visually_reviewed'] = True
inventory['full_art_unification_complete'] = False
inventory['visual_review_scope'] = '319개 동일 색인 형태의 대표를 일반·레드 각각 실제 열람. 436참조의 모든 번역 위치를 개별 열람한 의미는 아니다.'
(O / 'inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', 'utf8')

groups = [
    (0, 2, '대기·달리기·점프', '대기의 머릿결·보닛·커프·앞치마 기준과 비교했다. 달리기와 공중의 새 얼굴·의상 선이 큰 단색 면으로 남은 자세를 추가로 찾지 못했다. 각도·머리 상하 이동의 실제 연속성은 각 배치 원순서 검사와 실기를 함께 봐야 한다.'),
    (3, 7, '벽·지상 준비와 1·2타', '목·손목·허리·부츠의 연결과 내부 명암을 비교했다. 효과와 몸체가 분리된 칸도 있으므로 이 판만으로 검기 동시 접점을 통과시킨 것은 아니다.'),
    (8, 10, '지상 3타·피격·회복·대기', '소매·치맛단·머리 내부 명암과 피격 표정을 확인했다. 수용 대기147의 세부를 보존하며 새 몸체가 지나치게 가는 선으로 수축한 확정 사례는 찾지 못했다.'),
    (11, 14, '지상 질풍아·사다리·후면·사다리 베기', '낮게 접힌 몸과 후면 머리층·등끈·치맛단·종아리 명암을 확인했다. 기존 저세부 머리나 단순 의상으로 돌아가는 확정 자세는 추가로 찾지 못했다.'),
    (15, 17, '공중 검격·등장 전반', '커프·앞치마·부츠와 새 머리의 명암이 이어진다. 별도 검기 참조의 빛을 몸체 결함으로 분류하지 않았다.247/248 섬광의 실시간 가림은 단독판 범위 밖이다.'),
    (18, 18, '등장 후반·승리·귀환 빛', '249..253의 바닥과 다리 연결, 승리1..6의 정면·측면 변화와 지지다리 폭을 보았다. 현재 판에서 추가 확정 절단이나 급격한 체형 축소는 찾지 못했다.'),
    (19, 21, '체이서·벽 검격·탑승 머리', '체이서의 새 머리·부츠와 리본 위상, 탑승 머리의 명암을 확인했다.75/77의 실제 조종석 내 크기는 앞선 cockpit 비교와 root39 근거를 따르며 이번 독립 머리판으로 대체하지 않는다.'),
    (22, 24, '뇌신격·특수 검격·회복', '앞팔·장갑·자루 주변과 치마·부츠 세부를 보았다. 원효과는 별도 참조이며 실제 동시 표시·팔레트 전환은 이 정적판만으로 증명하지 않는다.'),
    (25, 27, '빙열참·용염인·공중 회전', '새 낮은 몸체·후두부·커프·발목을 확인했다. 회전은 원표 종료와 미술 반복이 다르므로 기존 원순서 증거를 유지한다. 별도 무기 객체 VRAM을 이 몸체판에 복원한 것은 아니다.'),
    (28, 28, '낙봉파 준비·발동·회복', '178..181의 흰 부츠와 파란/레드 신발 역할이 최신 국소 원화에서 복원됐고177·186과 이어진다. 원구체와 몸체의 별도 16판 원순서 검사 및 root52 실제 열람을 함께 연결한다.'),
]
report = {
    'scope': '최신 린303 후보의 전체 단독 표시 미술 재검토. 새 기술 검사나 전수 실기 완료 보고가 아니다.',
    'source': str(source.relative_to(ROOT)), 'source_sha256': sha(source),
    'frozen': str((D / 'rin_extension/prepared_burst_remaining02/FROZEN.json').relative_to(ROOT)),
    'frozen_sha256': sha(D / 'rin_extension/prepared_burst_remaining02/FROZEN.json'),
    'inventory': str((O / 'inventory.json').relative_to(ROOT)), 'inventory_sha256': sha(O / 'inventory.json'),
    'standalone_references': 436, 'exact_shape_groups': 319,
    'actually_viewed_sheets': 58, 'normal_sheets': 29, 'red_sheets': 29,
    'view_method': '각 PNG를 view_image로 실제 열람했다. 대기147을 각 시트에 함께 두고 원점160·페이지 고정 crop·최근접 정수4배로 비교했다.',
    'pages': [{k:p[k] for k in ('file','variant','sha256','actual_view_image')} for p in inventory['pages']],
    'observations': [{'pages': [lo, hi], 'variants': ['normal','black'], 'group': group, 'finding': finding} for lo, hi, group, finding in groups],
    'new_confirmed_art_defects': [],
    'conclusion': '이번 전체판에서 추가 확정 재작화 대상은 찾지 못했다. 이전의 큰 단색 의상·흐린 머리·심한 체형 축소가 남았다고 확정할 참조는 없었다. 이는 모든 픽셀과 실제 동작의 완성 선언이 아니다.',
    'limits': [
        '동일 cropped 색인 형태만 묶었다. 번역 위치가 다른 alias는 목록과 bbox로 남겼으며 모든 alias를 별도 칸으로 열람하지 않았다.',
        '큰 효과가 포함된 넓은 시트는 화면 표시에서 축소될 수 있어 모든 texel의 현미경 검사는 아니다. 새 제작 배치별 확대 source/readback 증거는 별도 유지한다.',
        'b1_42..49는 이전 VRAM에 의존하는 부분 업로드이므로 독립 완성 그림으로 복원하거나 미사용 참조로 판정하지 않았다.',
        '몸체0/13은 현재 팔레트이다. 나머지3 CLUT는 역사 캡처 미리보기이므로 현재 게임 효과 색상 증거가 아니다.',
        '차량 가림·검기/불꽃/구체의 실제 동시 표시·방향 전환·조립 도중 VRAM·움직임과 판정은 이 정적판으로 검증하지 않았다.',
        '303은 누적 수정·파생 참조 수이며 완료율이 아니다. 수용 대기10·정적 몸체효과2 보존과 전수 실기 미실행은 별도다.'
    ],
    'remaining_preserved_review': str((D / 'rin_extension/remaining303_review/report.json').relative_to(ROOT)),
    'latest_burst_sequence_review': str((D / 'rin_extension/burst303_review_v2/visual_review.json').relative_to(ROOT)),
    'runtime_verified': False, 'user_accepted': False, 'full_art_unification_complete': False,
    'next': ['최신 선택 화면 독립 사본이 현재 몸체와 일치하는지 읽기 대조', '실제 게임 미관측·불안정 표본을 최신 동결 자원별로 구분']
}
(O / 'visual_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'sheets': 58, 'report': str((O / 'visual_review.json').relative_to(ROOT)), 'sha256': sha(O / 'visual_review.json')}))
