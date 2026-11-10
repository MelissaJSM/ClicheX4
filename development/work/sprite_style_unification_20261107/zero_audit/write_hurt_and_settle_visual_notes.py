from pathlib import Path
import hashlib, json

B = Path('work/sprite_style_unification_20261107')
D = B / 'zero_audit'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

notes = [
    ('nana_ultimate_ceremony_pistol_sources01/settle_legs_visual_review.json',
     'nana_audit/ultimate_ceremony_repaint/settle_legs_registered_v1/comparison.png',
     ['양폼 마지막열에서 이전의 성긴 정강이보다 종아리의 밝은 면과 안쪽 어두운 선이 나뉘고 발목에서 초록 신발 윗선으로 이어지는 연결이 분명하다.',
      '대기와 나란히 보았을 때 어두운 선이 과도하게 굵은 검정 띠로 읽히거나 무릎/발목이 끊기는 추가 확정 결함을 이 판에서 찾지 못했다.'],
     ['하체 국소 한 판의 정적 미술 의견이다. 원화 등록 수치/보존/최종패킹/실기를 검사했다는 뜻이 아니다.',
      '새 원화 전체열의 머리/손 등은 국소 채택 대상과 구별한다.']),
    ('shibuki_ultimate_hurt234_visual01/common02_visual_review.json',
     'shibuki_audit/ultimate_hurt_common_probe02/after_comparison_01.png',
     ['새234 앞팔이 얼굴을 가로지르던 형태에서 주먹 옆으로 팔꿈치가 아래에 접히는 모습으로 돌아왔다.',
      '새 머리/몸/다리와 국소 팔의 연결에서 추가 확정 절단을 찾지 못했다.'],
     ['233/234 공통화 새그림 비교 한 판만 실제 열람했다. 전체13 피격 효과와 최종 ARC 열람은 별도다.',
      '후속 b43e 후보의 전체GPU/부분조합/게임 수용을 뜻하지 않는다.']),
]
for out_rel, image_rel, observations, limitations in notes:
    p = B / image_rel
    out = D / out_rel
    data = {'scope': 'view_image 실제 열람의 제한된 정적 의견',
            'actually_viewed': {'path': p.as_posix(), 'sha256': sha(p)},
            'observations': observations, 'limitations': limitations,
            'runtime_verified': False, 'user_final_accepted': False}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(out.as_posix(), sha(out))
