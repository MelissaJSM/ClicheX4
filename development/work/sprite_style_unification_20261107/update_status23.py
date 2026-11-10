from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'docs/STATUS.md';old=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'
assert marker in old
prefix='''# 프로젝트 상태

**2026-11-08 / EXPANSION — 네 캐릭터와 모든 의상의 대기 기준 세부 묘사 통일을 계속 진행 중이다. 전체 완료가 아니다.** 사용자의 한도 해제 후 재개 지시에 따라 작업한다. 최신 시험본과 기존 활성 포인터를 구분하며 원본·출시본·사용자 F1/메모리카드는 보존한다.

최신 통합 시험본은 [BR v18](../out/ver_buki_riko/sprite_style_unification_20261107_v18/shibuki_riko.cue) / [RN v23](../out/ver_rin_nana/sprite_style_unification_20261107_v23/rin_nana.cue)이다. BIN SHA-256은 각각 `b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88`, `fe225d3fee86aaa9a26e47e855d661265eefcdef229bdc5c8801a6521dccaa98`. BR18은 시부키 Ultimate 피격13을 포함한다. RN21의 나나 Ultimate 등장10에 RN22의 기본/포스 저체력6, RN23의 Ultimate 승리4를 추가했다. 전251,793섹터 비교·변경318/298섹터 EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사를 통과했다.

[모음집 v23](../out/sprite_style_unification_20261107/review_v23/ALL_SPRITES_CURRENT.html)은 BR18/RN23을 바탕으로28폼·4,510표시를 제공한다. 변경표시2,442(리코491/시부키688/나나623/린640)의 픽셀 대조 및4재생루프 검사 통과. **중복 의상·팔레트·UI가 포함된 표시 수이며 품질 완료율이나 새 원화 수가 아니다.** [전체 범위 장부06](../work/sprite_style_unification_20261107/zero_audit/full_scope_matrix06/COVERAGE.html)은 BR18/RN22 시점이다.

저체력6은 새 한 몸에 접지 호흡과 입1픽셀을 적용했고, 기본/포스의 발·권총·베일 소유를 수정했다. [직접 검토111](../work/sprite_style_unification_20261107/root_review_checkpoint111.json), 원표6/16스텝·322canvas·192부분파츠·독립검사·재현2/입력거부7을 통과했다. RN22 새 부팅에서 PL00 RAM 로딩과33관측참조의 GPU 검사는 성공했지만 목표120..125는 발동시키지 못했다. 체력28 뒤 사망·재등장으로 끝났으며 이를 실기 성공으로 계산하지 않는다. [실기 실패와 관찰 범위](../work/sprite_style_unification_20261107/runtime/nana_base_lowhp22_summary.json). 직접 열람6장과 저장된160장 전체 열람도 구분했다.

Ultimate 승리204..207은 새4자세×2의상이며 206/207은 수용85의 동일8px 권총을 손에 정합했다. [직접 검토112](../work/sprite_style_unification_20261107/root_review_checkpoint112.json), 원표39/40·66canvas·128부분파츠·독립/원MIPS 검사와 입력거부8을 통과했다. **실제 스테이지 클리어 및 귀환156..160 완료는 아니다.** 귀환156은 별도 새 원화를 제작 중이다.

현재 루트 작업은 나나 기본/포스 특수 자세95/98의 새 머릿결·옷 주름 등록과96/99의 원래X+1 관계 보존이다. 처음 등록에서 발끝1px, 권총 교체 중 손목 연결, 부분파츠 베일 조각을 찾아 수정했다. 신규4참조는 아직 RN23에 미포함이다. 시부키 Ultimate 등장8참조의 검증도 진행한다. after135 팔 편집1건은 이미지 도구 자동검토 거부로 미완료에 남겼으며 다른 프롬프트/도구로 우회하지 않는다.

리코·린의 일반/블랙·특수·탑승·UI 및 두 X 캐릭터의 기본/포스/Ultimate 전후를 모두 범위에 유지한다. 기존 통과 근거와 미술 잔여를 구분하며 전수 실기·전체 미술 완료·최종 사용자 수용은 주장하지 않는다. [보호34](../work/sprite_style_unification_20261107/protection_checkpoint34.json)에서80보호파일·시험카드5쌍 동일, RN22 시험 세션 종료를 확인했다. BR17 포스 피격·RN19 Ultimate 피격 등 이전 실기는 해당 범위에서 보존한다.

'''
p.write_text(prefix+old[old.index(marker):],'utf8');print('STATUS updated: BR18/RN23, album23; unfinished work separated')
