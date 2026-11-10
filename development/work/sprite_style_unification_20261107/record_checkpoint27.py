"""Persist only images actually opened by the root reviewer."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path('work/sprite_style_unification_20261107')
paths = [
    'nana_audit/ultimate_dash_repaint/local_legs_registered_v4/comparison.png',
    'nana_audit/ultimate_dash_repaint/before_last_registered_v1/comparison.png',
    'nana_audit/ultimate_dash_repaint/fold94_registered_v1/comparison.png',
    *[f'shibuki_audit/rising_ultimate_right_native02/{form}_comparison.png' for form in ('before', 'after')],
    *[f'shibuki_audit/rising_ultimate_prepare103_native01/{form}_comparison.png' for form in ('before', 'after')],
    *[f'shibuki_audit/rising_right_base_pack{version:02}/{form}_readback_00.png' for version in (1, 2) for form in ('base', 'fourth')],
    *[f'shibuki_audit/rising_right_ultimate_pack01/{form}_readback_00.png' for form in ('before', 'after')],
    'shibuki_audit/rising_right_packed_contact01/four_forms_native_effect_overlay.png',
    *[f'zero_audit/rin_extension/ladder_dash01/body_probe/{color}_comparison.png' for color in ('normal', 'black')],
]
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / p).as_posix(), 'sha256': hashlib.sha256((W / p).read_bytes()).hexdigest(), 'root_actually_viewed': True} for p in paths],
    'findings': {
        'shibuki': '오른손 라이징 준비/상승103104의 네 의상 최종 재추출4판과 양방향 원화염 위치 합성판을 열람했다. 몸체/의상 연결과 손 방향은 통합 후보로 수용. 별도 원MIPS/GPU도 통과. 새 손 교정의 실제 게임은 아직 미검증이다.',
        'nana': '국소 보완71/75의 신발 분리와81의 발 간격은 개선되어 패킹 후보 방향 수용.83후속 원화는 방향 수용.94앞다리가 낮게 처져 국소 재수정 후 fold94_registered_v1에서 앞다리 접힘과 긴 뒷다리 보존을 확인했다. 이 기록은 전체 대시 패킹이나 실기 수용이 아니다.',
        'rin': '사다리베기199/202의 새 머리는 보존하고 몸체-2y한 후보에서 목/어깨/발 연결을 확인했다.155/156도 새 머릿결/장갑과 발높이 확인. 손/검기 검사와 실제 재삽입은 별도 후속이다.',
    },
    'actual_rin_runtime_review': 'work/sprite_style_unification_20261107/runtime/rin_checkpoint11_summary.json',
    'all_characters_complete': False,
    'user_acceptance': False,
}
dest = W / 'root_review_checkpoint27.json'
assert not (W / 'staging_br_v11.json').exists(), 'Do not alter a bound review'
dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
