from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'docs/STATUS.md';old=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.';assert marker in old
prefix='''# 프로젝트 상태

**2026-11-08 / EXPANSION — 네 캐릭터·모든 의상의 대기 기준 상세 통일 계속. 전체 미완료.** 한도 해제 후 재개한다. 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 모두 범위에 유지한다. 중복 표시 수를 품질 완료율로 사용하지 않는다.

최신 통합 시험본은 [BR20](../out/ver_buki_riko/sprite_style_unification_20261107_v20/shibuki_riko.cue) / [RN27](../out/ver_rin_nana/sprite_style_unification_20261107_v27/rin_nana.cue). BIN SHA-256: BR `9bfd915f5e717781dd433eb291daa1aac1bad424734ad7decad69498d521598b`, RN `62e3850cf773bb013eebda6c22eee23ba37ca69ff5ac06baa5f601e712f2b7a1`. 양쪽 전251,793섹터 비교, 변경318/299섹터 EDC/ECC, 재추출, EXE 보존, 원MIPS/GPU 검사를 통과했다. 원본 미국판 SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b` 및 기존 활성 포인터·출시본은 변경하지 않는다.

BR19/20에 시부키 Ultimate 등장8(135 제외)·승리4를 추가했다. RN24..27에 나나 기본/포스 특수95/96/98/99, 사격88/89/97, 회복138/139와 Ultimate 귀환156..158을 추가했다. 대기 크기·머릿결·주름을 기준으로 새 그림을 등록했고 손/권총·발 기준점·부분파츠 소유를 보완했다. [루트 검토114~119 및 관련 증거](../work/sprite_style_unification_20261107/root_review_checkpoint119.json). 앞선 나나 저체력6과 Ultimate 승리4도 유지된다.

[네 캐릭터 모음집 v24](../out/sprite_style_unification_20261107/review_v24/ALL_SPRITES_CURRENT.html)은 BR20/RN27의 28폼·4,510표시 중 변경2,499표시(리코491/시부키712/나나656/린640)를 모았다. 의상·팔레트·UI 사본 중복을 포함하며 새 원화 수·전체 품질 완료율이 아니다. 이전 [전체 범위 장부07](../work/sprite_style_unification_20261107/zero_audit/full_scope_matrix07/COVERAGE.html)은 BR18/RN25 시점이다.

**실제 검증:** RN26 새 부팅·카드 사본으로 포스아머 양방향 차지샷88/89, 더블 사이클론97/98/99, 프로스트 타워95/96을 관측했다. 실제815창을 기록하고22개 시간순 비교판을 직접 검토했다. 추가 확정 몸체 분리·크기 급변은 찾지 못했다. 차지 기록의29 한 전환은 안정 표본이 없어 미검증, 기본형/부분파츠/전체 캐릭터 전수 실기는 아니다. RN26에서 관측한138/139는 이전 그림이므로 RN27 신규138/139 실기 근거로 계산하지 않는다. [실기 요약](../work/sprite_style_unification_20261107/runtime/nana_fourth_special26_summary.json), [직접 검토120](../work/sprite_style_unification_20261107/root_review_checkpoint120.json). 세션 정상 종료, [보호36](../work/sprite_style_unification_20261107/protection_checkpoint36.json)의80보호파일·카드5쌍 동일. 사용자 F1/F3·RAM 쓰기 없음.

**현재 작업/남은 한계:** 나나 기본/포스 사격 후속90/91의 새 그림과 부분파츠 베일을 수정했다. 후보 `ef69d0a1…`는 아직 RN27에 미포함이다. 기존 조립 레코드에 새 머리 픽셀을 손실 없이 배치해 공간 제약을 해결했고 재현·독립 검토 중이다. 시부키 Ultimate 귀환156..158, 나나 Ultimate 사다리와 기본/포스 등장 잔여 등의 상세 작업을 계속한다. 시부키 after135 팔 및 나나 Ultimate 사다리149/151/153 의상 보정은 이미지 도구 자동 안전검토 거부로 미완료이며 우회하지 않는다. 독립 작업은 계속한다. 나나 기본/포스 저체력120..125의 실제 발동은 이전 RN22 시험에서 실패했으며 정적 통과로 대신하지 않는다.

기존 리코/린 재작화 및 정상/블랙 실기 근거는 보존한다. 전체 미술·전수실기·최종 사용자 수용 완료를 주장하지 않는다. 승인 범위는 앞선 사용자 지시에 따른 네 캐릭터 전체 수정과 반복 검증이며 추가 사용자 결정으로 멈춘 상태가 아니다.

'''
p.write_text(prefix+old[old.index(marker):],'utf8');print('STATUS updated BR20/RN27, album24, RN26 actual limits, pending candidates')
