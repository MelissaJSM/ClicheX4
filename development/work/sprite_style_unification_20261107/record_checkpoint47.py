"""Record only images the root reviewer actually opened."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
paths = [W / 'shibuki_audit/prepared_ultimate_dash01' / f'{form}_readback_{i:02d}.png'
         for form in ('before', 'after') for i in range(4)]
paths += [W / 'nana_audit/ultimate_run_repaint/common_arm_boundary_probe_v2' / f'comparison_{i}.png'
          for i in range(1, 5)]
paths += [W / 'x_selection_audit13/shibuki/comparison_00.png']
record = {
    'art_review_images': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p),
                           'root_actually_viewed': True} for p in paths],
    'shibuki_candidate_sha256': 'bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb',
    'native_proof': {'path': (W / 'shibuki_ultimate_dash14_components_native_checks.json').relative_to(ROOT).as_posix(),
                     'sha256': sha(W / 'shibuki_ultimate_dash14_components_native_checks.json')},
    'findings': [
        '시부키 Ultimate 대시20참조의 전후 의상 재추출8판 전부 직접 열람. 귀/머릿결/의상 음영의 대기 기준 세부와 팔 접점이 유지되는 방향을 수용한다. 추가 확정 절단은 찾지 못했다.',
        '나나 이동사격 팔 공통경계4판 직접 열람. 맨팔을 자르지 않고 원화의 가장자리 셀을 재킷과 공유하는 수정 방향 수용. 최종 ARC는 별도 검토한다.',
        '시부키 선택화면23은 플레이용160과 달리 주황색 구형 빛기둥이 남아 있음을 확인했다. 별도 동기화 후보가 필요하다.'
    ],
    'limits': ['시부키 새 Ultimate 대시의 실제 게임 검증은 아직 수행하지 않았다.',
               '나나 공통경계는 입력 후보 검토이며 최종 패킹/원순서 연결 검토와 구별한다.',
               '선택화면23 수정 후보 자체는 이 기록에 포함하지 않는다.'],
    'final_user_accepted': False
}
dest = W / 'root_review_checkpoint47.json'
body = json.dumps(record, ensure_ascii=False, indent=2) + '\n'
if dest.exists():
    assert dest.read_text('utf8') == body
else:
    dest.write_text(body, 'utf8')
print(json.dumps({'record': str(dest), 'images': len(paths), 'sha256': sha(dest)}))
