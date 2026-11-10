from pathlib import Path
import json
import shutil

W = Path(__file__).resolve().parent
ROOT = W.parents[1]
read = lambda p: json.loads(p.read_text('utf8'))
album = ROOT / 'out/sprite_style_unification_20261107/review_v37'
checks = read(album / 'browser_checks.json')
assert checks['passed'] and len(checks['modified_pixel_checks']) == 3061
assert read(W / 'staging_br_v31_native_checks.json')['passed']
assert read(W / 'protection_checkpoint54.json')['passed']
assert read(W / 'runtime/br31_hover_summary.json')['recorded_captures'] == 479
snapshot = W / 'docs_before_checkpoint46'
snapshot.mkdir(exist_ok=False)

for name in ('STATUS.md', 'SPRITE_STYLE_UNIFICATION_20261107.md'):
    p = ROOT / 'docs' / name
    shutil.copyfile(p, snapshot / name)
    t = p.read_text('utf8')
    marker = '아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.' if name == 'STATUS.md' else '아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.'
    head, tail = t.split(marker, 1)
    head = head.replace('[BR30](../out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.cue)', '[BR31](../out/ver_buki_riko/sprite_style_unification_20261107_v31/shibuki_riko.cue)')
    head = head.replace('`ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875`', '`ad4f2ceab100098e88977f383d314efd0337379feb70999989eaa53926332516`')
    head = head.replace('모음집 v36', '모음집 v37').replace('/review_v36/', '/review_v37/').replace('BR30/RN43의', 'BR31/RN43의')
    head = head.replace('2,936', '3,061').replace('시부키900', '시부키1025').replace('약65.1%', '약67.9%')
    anchor = '**최근 반영한 작업과 근거**\n\n'
    assert anchor in head
    head = head.replace(anchor, anchor + '''- 시부키 기본/포스 호버221..230을 BR31에 통합했다. 10참조50층·공통 얼굴/손/하체·원버스터60불투명+11투명 보호영역을 결속했고, 팔레트 소유가 달랐던 피부3픽셀을 고쳤다. 픽셀을 단순화하지 않고 기존16참조의 타일 저장순서만 가역 변경하여 은행 경계와 26바이트 여유를 지켰다. 비선택층/부분조합·3회 동일재현/10거부·원MIPS/GPU·원표12개·독립 검사와 최종5쌍 직접 검토를 통과했다. [동결](../work/sprite_style_unification_20261107/root_shibuki_hover/packed_hover_candidate03/FROZEN.json)·[원게임 디코더 검사](../work/sprite_style_unification_20261107/root_shibuki_hover/native_components03_native_checks.json)·[직접 검토162](../work/sprite_style_unification_20261107/root_review_checkpoint162.json).
- 시부키 네 의상의 차량용 작은 머리19참조씩을 BR31에 통합했다. 대기와 맞는 머릿결·장식을 정리하고 눈 위치와13×15크기를 보존했다. 기본/포스는 알파 동일, Ultimate는 귀의1픽셀 추가/1픽셀 삭제가 있다. 빈198과 원래 가림/순서용 참조를 보존했다. [기본/포스 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_vehicle_head_base01/FROZEN.json)·[Ultimate 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_vehicle_head_ultimate01/FROZEN.json)·[BR31 재추출](../work/sprite_style_unification_20261107/shibuki_audit/br31_readback01.json). 작은 머리의 실제 조종석 가림 검증은 아직 하지 않았다.
''', 1)
    anchor = '**실제 게임 검증**\n\n'
    assert anchor in head
    head = head.replace(anchor, anchor + '''- BR31 새 부팅·복사 카드 DATA3 포스아머에서479캡처/478인코딩프레임과16판을 직접 검토했다. 오른쪽 전진/후진/정지 및 왼쪽 전진/후진 호버·사격 표본에서 어깨/버스터와 발/불꽃 연결을 확인했다. 최초 후진 입력은 일반 점프로 끝나 실패로 남겼고, 간격을 늘린 재시도에서 발동을 확인했다. 일부 초기 크롭 잘림은 범위를 넓혀 구분했으며 실제 화면 끝에 걸친 표본은 온전한 외형 검증에서 제외했다. 기본 의상+발파츠·나머지 부분아머·모든60Hz 전수는 미확인이다. [실기와 한계](../work/sprite_style_unification_20261107/runtime/br31_hover_summary.json).
''', 1)
    head = head.replace('[보호53](../work/sprite_style_unification_20261107/protection_checkpoint53.json)', '[보호54](../work/sprite_style_unification_20261107/protection_checkpoint54.json)')
    start = head.index('시부키 기본/포스와 Ultimate 호버221..230의 새 몸·사격 팔을 제작 중이다.')
    end = head.index('**효과 분류 정정:**', start)
    head = head[:start] + '''시부키 호버·작은 머리는 위 BR31까지 실제 통합했다. 기본 호버의 실제 도달 가능한 조합은 발파츠가 있는 mask8, 포스는15이다. 기본/포스의223 오른신발1행 등록은38픽셀 이동 중8픽셀 겹침이 있으므로 알파 완전 불변으로 기록하지 않는다. 225 공통 하체·229 부분 연결·높은 팔/머리층 분리와 사격 피부3픽셀 교정을 보존한다. 저장순서만 바꾼16참조는 새 원화 수에 넣지 않는다.

시부키 최신 범위 장부는 [장부44](../work/sprite_style_unification_20261107/shibuki_audit/fullform_ledger44.json)다. 네 폼의762고유 표시 키는 새 동결678·수용 보존24·효과56·동일 대기 혼합2·보류135두폼2로 구분했다. 이것은 네 캐릭터 전체의 품질 완료율이 아니다. 리코·린에는 현재 추가 확정 재작화 후보가 없지만 전환·색상·UI를 포함한 전체 범위를 유지한다. 나나의 기본/포스 노바·호버·등장 보완은 RN43까지 통합했고, Ultimate 사다리 보류는 아래와 같다.

다음은 실제 차량 작은 머리의 조종석 가림·손잡이/발판, 기본 의상+발파츠와 나머지 부분 아머, 기존 대기와 짧은 전환의 추가 확인이다. 자동 검사 통과·그림을 변경한 비율·사용자 최종 수용을 구분한다. BR31/RN43은 별도 시험본이며 활성 배포 포인터와 기존 완성본은 갱신하지 않았다.

''' + head[end:]
    p.write_text(head + marker + tail, 'utf8')

print('BR31/RN43; album37 verified3061; fourth hover479captures; protection54; full work incomplete')
