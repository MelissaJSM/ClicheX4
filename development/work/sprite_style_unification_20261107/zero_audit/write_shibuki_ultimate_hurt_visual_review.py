from pathlib import Path
import hashlib, json

D = Path('work/sprite_style_unification_20261107/zero_audit')
O = D / 'shibuki_ultimate_hurt13_independent01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads((O / 'report.json').read_text('utf8'))
assert r['passed'] and r['candidate_sha256'] == 'b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94'
viewed = []
for i in range(5):
    p = O / f'readback_{i:02}.png'
    assert sha(p) == r['readback_sheets'][i]['sha256']
    viewed.append({'path': p.as_posix(), 'sha256': sha(p)})
out = {
    'scope': '독립 실제ARC 재추출 전후5판을 view_image로 모두 실제 열람.13참조×구/신×양폼52표시.',
    'candidate_sha256': r['candidate_sha256'],
    'independent_report_sha256': sha(O / 'report.json'),
    'actually_viewed': viewed,
    'observations': [
        '106/110/233/234의 새 머릿결·안경·재킷 접힘·맨팔 경계와 신발 표현이 이전의 큰 단색 면보다 나뉜다. 감긴 눈과 피격 표정도 새 머리 안에서 읽힌다.',
        '234 맨팔의 앞주먹과 아래 팔꿈치가 연결되어 얼굴을 가로지르던 초기 after 원화의 자세 오류는 이 최종재추출에서 보이지 않는다.106/110/233도 손목·어깨·무릎/발목에 추가 확정 절단을 찾지 못했다.',
        '107/108 전기선이 새몸과 겹치며109는 각폼의 새 외곽을 따른다. 전기99/76px 전체표시는 기존의 일부 가림과 다른 제작 정책임을 기술보고에서 구분했다.',
        '111의 전기 외곽과 새110몸이 연결되어 표시되며 GPU 수정 전후 그림 자체는 같다는 독립 대조 결과와 모순되는 새 잘림을 찾지 못했다.',
        '112~114 공통 재킷 실루엣과235/236 뒤쪽 오라가 새몸 외곽에 이어진다. 옛 의상 파편을 몸 밖 효과로 함께 보존한 형상은 보이지 않는다.',
    ],
    'new_confirmed_art_defects': [],
    'limitations': [
        '이번 실제 열람은 양폼52표시이며416부분 아머 조합 전부를 육안으로 봤다는 뜻이 아니다.',
        '112~114는 양폼 모두 새재킷110 공통CLUT2실루엣이다. 각폼별 새몸을 독립 반영한 것으로 확대하지 않는다.',
        '오라 전체256/464px 원형 보존과 새몸의 가림은 정적 합성 규칙이다. 실제 시간표·피격 팔레트 전환·게임 재현은 별도다.',
        '최종 루트 미술 수용과 사용자 수용은 별도다.',
    ],
    'runtime_verified': False,
    'user_final_accepted': False,
}
p = O / 'visual_review.json'
p.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', 'utf8')
print(p.as_posix(), sha(p))
