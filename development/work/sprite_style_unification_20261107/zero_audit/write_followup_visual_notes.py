"""이전 실제 열람의 제한된 관찰을 독립 기록으로 저장한다. 이미지/ARC는 수정하지 않는다."""
from pathlib import Path
import hashlib
import json

B = Path('work/sprite_style_unification_20261107')
D = B / 'zero_audit'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(relative, images, observations, limitations, evidence=None):
    out = D / relative
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        'scope': '앞선 view_image 실제 열람의 정적 의견만 기록. 생성/패킹/게임 실행 없음.',
        'actually_viewed': [{'path': p.as_posix(), 'sha256': sha(p)} for p in images],
        'observations': observations,
        'limitations': limitations,
        'additional_evidence': evidence or [],
        'runtime_verified': False,
        'user_final_accepted': False,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out.as_posix(), sha(out))

save(
    Path('shibuki_ultimate_hurt234_visual01/report.json'),
    [B / 'shibuki_audit/ultimate_hurt_native02' / f'{form}_comparison.png' for form in ['before', 'after']],
    [
        '234 before의 앞주먹은 얼굴 옆에 있고 팔꿈치는 아래로 접힌다. after에서는 전완이 얼굴/입 앞을 가로지르며 손끝 방향도 달라져 단순한 소매 제거 차이로 보기 어렵다.',
        '수용된 before 주먹·아래 팔꿈치 자세를 기준으로 맨팔만 국소 재작화하고 새 머리/몸/다리를 보존하는 방향이 타당하다.',
    ],
    [
        '이미지 두 판 중234의 팔·손 차이에 한정한 의견이다.',
        '후속 국소 생성4417737f 결과는 이 검토에서 열람하지 않았고 최종 정합·공통층·효과 수용 근거가 아니다.',
    ],
)

save(
    Path('nana_ultimate_ceremony_pistol_sources01/canonical_v2_visual_review.json'),
    [B / 'nana_audit/ultimate_ceremony_repaint/canonical_cases_probe_v2' / f'comparison_{i}.png' for i in range(1, 4)],
    [
        '133 하향,135 가슴,136 턱,137/138 머리 위로 이어지는 새 손/권총이 검정 덩어리보다 손잡이와 총열로 분리되어 읽힌다.',
        '세 판에서 권총이 새 손 밖으로 명백히 떠 있는 추가 결함은 찾지 못했다.137/138 위쪽 모듈도 귀/앞머리와 구별된다.',
    ],
    [
        '정본85의20텍셀·8px 모듈을90도 강체 등록한 제작 정책이다. 과거 사선 총의 방향과 완전히 같다는 판정이 아니다.',
        '공통 손,136 바깥1셀,46px 효과와 원순서 합성은 별도 후속 검사다.',
        '138 하체는 담당자가 새 원화 국소 보완을 진행하므로 이 무기 의견으로 몸체 최종 수용을 주장하지 않는다.',
    ],
)

dust_report = D / 'nana_arrival141_dust01/report.json'
save(
    Path('nana_arrival141_dust01/visual_review.json'),
    [D / 'nana_arrival141_dust01/dust_source_comparison.png'],
    [
        '현재 before141, 역사 먼지12px, 현재 after141, 현재 after idle0의 별도 비교판을 실제 열람했다.',
        '먼지는 발 주변의 작은 분리 조각으로 읽힌다. after의 몸체 바깥 추가5px를 함께 원효과로 보존할 근거는 없으며, 상세 좌표와 소비타일은 독립 기술 보고로 구분했다.',
    ],
    ['새141 패킹/원순서/게임은 이 검토에 포함하지 않는다.'],
    [{'path': dust_report.as_posix(), 'sha256': sha(dust_report)}],
)
