import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

report_path = OUT / 'report.json'
report = json.loads(report_path.read_text(encoding='utf-8'))
assert digest(report_path) == 'f60ca982db7d2790377a5986751480c3eac54011509231e11aa72fb08d2439ea'
for item in report['new_readback_sheets']:
    assert digest(ROOT / item['path']) == item['sha256']
review = {
    'scope': '독립 reader가 실제 시부키 기본/포스 피격13 후보에서 재추출한 5판, 구/신 양폼 52표시를 view_image로 실제 열람했다. 기술 보고서는 변경하지 않는다.',
    'candidate_sha256': report['candidate_sha256'],
    'independent_report_sha256': digest(report_path),
    'viewed': report['new_readback_sheets'],
    'observations': [
        '106/110의 새 머릿결과 측면 그늘, 기본형 붉은 앞끈·소매 끝, 포스의 어두운 옷과 금색 경계가 구형의 큰 색면보다 분리되어 읽힌다. 손목과 접힌 무릎·발에 새로 확인되는 절단은 찾지 못했다.',
        '233의 들어 올린 다리와 234의 뻗은 정강이에서 무릎·발목 연결이 보인다. 포스233의 신발과 옷도 구형 검정 덩어리보다 구분된다.',
        '107/108의 번개와 111의 방사형 효과는 원래 별도 위치에 남는다. 109의 섬광은 새 실루엣을 따르며 112~114의 공통 CLUT2 표현은 일반 의상 팔레트와 구분했다.',
        '235/236은 원오라를 뒤에 놓고 새234 몸체를 앞에 합성한다. 포스의 구형 몸 색차가 사라지고 같은 새몸으로 이어지며, 이 정지판에서 추가로 확정되는 몸체·오라의 연결 단절은 찾지 못했다.'
    ],
    'new_confirmed_art_defects': [],
    'limitations': [
        '정지 재추출판의 미술 의견이다. 원표 연속 재생·실제 피격 팔레트 전환·60Hz 전환·게임 접점은 이번 열람에 포함하지 않았다.',
        '고정 등록65층과 기존 독립 원효과 출처를 실제 ARC에 대조했으나 새 생성원화의 재양자화 전과정은 이번 독립 reader 범위 밖이다.',
        '235/236의 원256/464픽셀 오라 출처는 보존하되 새 몸체로 가리는 규칙이다. 과거 포스 의상 차이와 오라 재색상의 화면 완전보존을 주장하지 않는다.',
        '최종 미술 수용은 루트의 별도 검토와 구분하며 사용자 최종 수용이나 실제 게임 검증으로 확대하지 않는다.'
    ],
    'user_final_accepted': False,
    'runtime_verified': False
}
path = OUT / 'visual_review.json'
assert not path.exists()
path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}, ensure_ascii=False))
