from pathlib import Path
import hashlib
import json

D = Path(__file__).parent
O = D / 'nana_base_standing3_independent01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads((O / 'report.json').read_text('utf8'))
assert sha(O / 'report.json') == 'e70fa9d4cd0c447819861d014bac577cb5bec49f03bf73ce6ed65a00c121d3d5'
names = ['full_088.png', 'full_089.png', 'full_097.png', 'partial_089.png', 'partial_097.png']
review = {
    'candidate_sha256': r['candidate_sha256'],
    'independent_report_sha256': sha(O / 'report.json'),
    'actually_viewed': [{'file': n, 'sha256': sha(O / n)} for n in names],
    'observations': [
        '최종 ARC에서 독립 재추출한 전체 3판과 부분 소유 2판을 직접 열람했다.',
        '88은 원래 밝은 빛의 호를 유지하면서 새 머리·옷·부츠의 명암이 보인다. 손과 새 권총 사이의 추가 확정 분리를 찾지 못했다.',
        '89는 위로 든 팔과 권총이 연결되고 머릿결·검정 베일·상의가 구분된다. 기본 부츠와 포스 맨다리의 재질 구분이 유지된다.',
        '97은 하나의 녹색 눈이 더 명료하게 읽히며 볼 옆 권총과 손목이 이어진다. 새 목·팔꿈치·발목의 확정 단절을 찾지 못했다.',
        '부분 89/97 판에서 베일이 다리 소유와 함께 이어지고, 97 body-only의 오른쪽 위 베일 고립 조각이 사라진 것을 확인했다.'
    ],
    'new_confirmed_visual_defects': [],
    'new_runtime_or_native_execution': False,
    'user_accepted': False,
    'limits': [
        '이번 시각 기록은 정적 5판에 한정하며 실제 게임이나 원표 연속 재생의 관찰이 아니다.',
        '기존 original MIPS 결과는 기술 보고에서 후보 해시와 결속했다. 새 MIPS 실행이나 전체 7296 RGBA 검사를 반복하지 않았다.',
        '인접 86/90/91은 변경 대상이 아니며 이번 시각 수용 범위에 추가하지 않는다.'
    ]
}
(O / 'visual_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'report': sha(O / 'report.json'), 'visual': sha(O / 'visual_review.json')}))
