from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix='''**2026-11-08 / EXPANSION — 네 캐릭터 모든 의상의 대기 기준 세부 묘사 통일 진행 중. 전체 미완료.** 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 범위에 유지한다. 추가 허락 대기 상태가 아니다.

현재 통합 시험본은 [BR21](../out/ver_buki_riko/sprite_style_unification_20261107_v21/shibuki_riko.cue) / [RN28](../out/ver_rin_nana/sprite_style_unification_20261107_v28/rin_nana.cue). BIN SHA-256은 BR `6d550cbcbcf06315c07aa17bbee75e07f64e4f0dc4efd6b2f381a3dc7a40db42`, RN `9ea0cc759b2884d026a305b45ce21a2d97f78aa2682f27b6349b864039784f58`. 양쪽 전251,793섹터 비교, 변경318/299섹터 EDC/ECC, 재추출, EXE 보존, 원MIPS/GPU 검사 통과. 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`, 기존 활성 포인터와 출시본은 보존했다.

BR21에 시부키 Ultimate 귀환156..158을 추가했다. 앞선 등장8(135 제외)·승리4와 새 머릿결·의상 주름을 이어가며 원래 귀환 이펙트와 합성했다. RN28에는 나나 기본/포스 사격 후속90/91을 추가했다. 기존 상세 사격88/89/97·특수95/96/98/99·회복138/139·저체력6 및 Ultimate 승리·귀환을 보존한다. [직접 검토121](../work/sprite_style_unification_20261107/root_review_checkpoint121.json), [122](../work/sprite_style_unification_20261107/root_review_checkpoint122.json).

[전체 스프라이트 모음집 v25](../out/sprite_style_unification_20261107/review_v25/ALL_SPRITES_CURRENT.html)은 BR21/RN28의28폼·4,510표시를 담았다. 변경2,511표시(리코491/시부키718/나나662/린640)의 픽셀 비교 및4재생루프 검사 통과. 이는 의상·팔레트·UI 중복을 포함한 표시 수이며 새 원화 수나 전체 품질 완료율이 아니다. [범위 장부08](../work/sprite_style_unification_20261107/zero_audit/full_scope_matrix08/COVERAGE.html)은 BR20/RN28 시점의 별도 스냅샷이다.

**실제 게임 검증:** RN28 새 부팅·시험카드 사본에서 새90/91과138/139를 포스아머 좌우 양방향으로 관측했다. 실제463창 중 시간순8비교판을 직접 검토했고 추가 확정 몸체 분리·크기 급변은 찾지 못했다. [실기 요약](../work/sprite_style_unification_20261107/runtime/nana_fourth_latest28_summary.json), [직접 검토123](../work/sprite_style_unification_20261107/root_review_checkpoint123.json). 이전 RN26의88/89·95/96·97/98/99 실기는 [별도 요약](../work/sprite_style_unification_20261107/runtime/nana_fourth_special26_summary.json)에 보존했다. 기본형·부분파츠·전체60Hz 전수 실기는 아니다. 두 세션 종료, 사용자F1/F3와 RAM쓰기 없음. [보호38](../work/sprite_style_unification_20261107/protection_checkpoint38.json)의80파일·시험카드5쌍 불변.

**진행 중:** 나나 기본/포스 등장7의 새 몸체4·빛 효과 파생3은 후보 `9599ca5f…`로 원MIPS/GPU 및 원표2의18스텝·402canvas를 통과했다. 아직 통합 전이다. 나나 Ultimate 사다리 허용7은 `dcaf1343…`로 독립 검토와 [직접 검토124](../work/sprite_style_unification_20261107/root_review_checkpoint124.json)를 통과했고 동결 중이다. 시부키 특수 자세는 새 도트 보존과 저장 공간 정합을 진행한다.

시부키 after135 팔, 나나 Ultimate 사다리149/151/153 의상 보정은 이미지 도구 자동 안전검토 거부로 미완료다. 우회하지 않았으며 관련 파생까지 사다리7참조는 기존 그림으로 보존했다. 나나 저체력120..125 실제 발동도 앞선 시험에서 실패해 미검증으로 남는다. 기존 리코/린 재작화·일반/블랙 실기 근거는 보존하며 전체 미술·실기·최종 사용자 수용 완료를 주장하지 않는다.

'''
p=ROOT/'docs/STATUS.md';old=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.';assert marker in old
p.write_text('# 프로젝트 상태\n\n'+prefix+old[old.index(marker):],'utf8')
p=ROOT/'docs/SPRITE_STYLE_UNIFICATION_20261107.md';old=p.read_text('utf8');title,tail=old.split('\n',1)
p.write_text(title+'\n\n'+prefix+'아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.\n'+tail,'utf8')
print('STATUS and sprite work record updated to BR21/RN28')
