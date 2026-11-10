from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'docs/STATUS.md';old=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'
assert marker in old
prefix='''# 프로젝트 상태

**2026-11-08 / EXPANSION: 리코·시부키·나나·린 전체 스프라이트의 대기 기준 세부 묘사 통일을 계속 진행 중이다. 전체 완료가 아니다.** 사용자의 한도 해제 후 재개 지시를 따라 진행하며 추가 사용자 결정으로 막힌 항목은 없다. 활성 배포 포인터·원본·사용자 F1/카드·첫 완성본은 보존한다.

최신 통합 시험본은 [BR v18](../out/ver_buki_riko/sprite_style_unification_20261107_v18/shibuki_riko.cue) / [RN v21](../out/ver_rin_nana/sprite_style_unification_20261107_v21/rin_nana.cue)이다. BIN SHA-256은 각각 `b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88`, `c5608887658797cad4e034870882ad4aa3c47f5993afaac28aa6a2328674a0e3`. BR17의 시부키 기본/포스 피격13·RN20의 나나 기본/포스 사다리14를 계승하고 **시부키 Ultimate 피격13 / 나나 Ultimate 등장10**을 추가했다. 새 두 디스크의 전251,793섹터 비교·변경318/298섹터 EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사를 통과했다.

[단독 모음집 v22](../out/sprite_style_unification_20261107/review_v22/ALL_SPRITES_CURRENT.html)은28폼·4,510표시 중2,416변경표시를 포함한다(리코491/시부키688/나나597/린640). 오프라인28폼·2,416픽셀 대조·4재생루프 검사 통과. **의상/색상/UI 중복을 포함한 표시 수이며 원화장수나 품질 완료율이 아니다.** 최종 재추출과 원순서 직접 열람은 [시부키 검토109](../work/sprite_style_unification_20261107/root_review_checkpoint109.json), [나나 검토110](../work/sprite_style_unification_20261107/root_review_checkpoint110.json)에 연결한다.

BR17은 새 부팅·복사 포스아머 카드 로딩 후 피격233..236을 실제 재현했다.160실제창·12비교판 직접 열람 및 RAM/GPU 확인에서 추가 확정 몸체 분리·효과 잘림을 찾지 못했다. 미확정 사건0. [실기 요약](../work/sprite_style_unification_20261107/runtime/shibuki_fourth_hurt17_summary.json). **이는 시부키 포스233..236의 대표 실기이며 BR18의 Ultimate 피격/전방향/전피해원 완료가 아니다.** RN19 Ultimate 피격 대표 실기·다른 이전 검사도 해당 범위에서 유효하다. 새 등장10·사다리14는 현재 원순서/네이티브 검사까지이며 실제 해당 동작 검사는 별도다.

현재 나나 기본/포스 저체력6은 새 머릿결·옷·다리 묘사를 등록하고 입1픽셀·접지 호흡·사랑이 공통부·부분파츠 베일을 수정했다. ARC `ac1e35b7…` 재추출·원MIPS·원표6/322canvas·재현2/7입력거부 검사를 통과했으며 독립감사와 실기 준비 중이다. **아직 RN21에는 미포함**이다. [검토111](../work/sprite_style_unification_20261107/root_review_checkpoint111.json). 나나 Ultimate 승리/귀환과 시부키 Ultimate 등장도 계속 제작한다. 시부키 after135 팔 국소 생성1건은 이미지 도구 자동검토 거부로 미완료에 남겼으며 다른 도구로 우회하지 않았다.

리코·린의 모든 일반/블랙·특수·탑승·UI 사본 및 나머지 두 X 폼의 특수/끝점까지 전체 범위를 유지한다. 이미 근거가 있는 검사와 미술 잔여를 구분하며, 전수 실기·전체 미술 완료·사용자 최종 수용은 아직 아니다. [보호32](../work/sprite_style_unification_20261107/protection_checkpoint32.json)에서 원본 등80파일·시험카드5쌍 동일 및 시험 세션 종료를 확인했다.

'''
p.write_text(prefix+old[old.index(marker):],'utf8');print('STATUS updated to BR18/RN21/album22')
