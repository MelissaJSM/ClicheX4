"""Record the single actually viewed aura alignment comparison, without edits."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'work/sprite_style_unification_20261107'
P = B / 'nana_audit/hurt_repaint/aura_contact_probe_v2/comparison.png'
OUT = Path(__file__).parent / 'nana_hurt_relations01/aura_v2_visual_review.json'
report = {
    'scope': '나나 기본/포스 피격235/236의 오라 국소 이동 비교1판 정적 미술 의견',
    'actually_viewed': [{'path': P.relative_to(ROOT).as_posix(),
                         'sha256': hashlib.sha256(P.read_bytes()).hexdigest(),
                         'method': 'view_image', 'boards': 1}],
    'observations': [
        '235 새 뒤머리에서 머리색과 겹쳐 읽히던 분홍 오라의 경계가 분리된다.',
        '236 흰 윤곽이 새 머리·모자 내부를 가르는 인상이 줄었다.',
        '236 오른쪽 뒤머리 아래 틈은 이전보다 넓게 보이나, 이 정적판에서 다른 체형의 실루엣으로 확정적으로 어긋난다고 보이지는 않는다.',
        '바깥으로 튀는 오라 모양 안에서 겹친 조각만 옮긴 후보 방향은 타당해 보인다.',
    ],
    'producer_claims_not_recomputed': [
        '원래 오라85/172픽셀·색·8연결 조각 내부 형상 보존',
        '겹친 조각만1..3픽셀 강체 이동·새 몸체 겹침0',
        '236 뒤머리 쪽 최대 간격8픽셀',
    ],
    'limits': [
        '원표의235/236 빠른 교대에서 오라만 옆으로 흔들리는지는 별도 연속판에서 확인해야 한다.',
        '제작 함수·패킹 검증·새 ARC reader·MIPS·게임 실기를 수행한 보고가 아니다.',
        '미술 후보 의견이며 루트 또는 사용자 최종수용을 대신하지 않는다.',
    ],
    'art_or_game_changed': False, 'final_accepted': False,
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'path': OUT.relative_to(ROOT).as_posix(),
                  'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest()}))
