from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix='''**2026-11-08 / EXPANSION — 네 캐릭터 모든 의상의 대기 기준 세부 묘사 통일 작업 진행 중. 전체 미완료.** 사용자는 사용한도 해제 후 계속 작업을 요청했고, 진행도 질문도 작업 중단 지시가 아니다. 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 범위에 유지한다.

통합과 원MIPS/GPU 검사를 마친 최신 시험본은 [BR22](../out/ver_buki_riko/sprite_style_unification_20261107_v22/shibuki_riko.cue) / [RN32](../out/ver_rin_nana/sprite_style_unification_20261107_v32/rin_nana.cue)다. BIN SHA-256은 BR `54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99`, RN `cdcbd7b6c9b97b952378b6427b4c9d2bbadd4ea82457ed178271f268933ca4bf`. 전251,793섹터 비교·변경319/301섹터 EDC/ECC·재추출·EXE 보존 검사 통과. 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`, 활성 포인터·출시본·사용자 저장은 보존한다.

BR22는 시부키 네 의상의 특수95/96/97을 추가했다. 기존 대기 질감의 머릿결·옷 주름을 유지하며 원표95/104 순서를 검토했다. [직접 검토127](../work/sprite_style_unification_20261107/root_review_checkpoint127.json). 고정 ARC 내부에서 PL00 그래픽bank0을280B 늘려 bank12 디코더 미소비 꼬리280B를 활용했다. 길이/LBA/EXE/외부항목 및bank13 전체는 동일하며 [실제 원로더·디렉터리508참조 검사](../work/sprite_style_unification_20261107/zero_audit/shibuki_standing3_directory_native01/report.json)와 독립 비대상 보존검사를 통과했다. 이미 승인된 내부 재패킹 범위의 구현 판단이며 새 사용자 승인 문구를 만들어 기록하지 않는다.

RN29/30은 나나 Ultimate 사다리7과 기본/포스 등장7, RN31은 Ultimate88/89/97, RN32는 기본/포스 승리204..207을 추가했다. 승리206의 다리가 길고 발이 내려갔던 초안은 반려해 세 번째 원화로 바꿨다.207은 원래 승리 자세 눈·바닥을 따라 y−5 위치 등록했으며 전체몸 축소는 하지 않았다. [승리 동결](../work/sprite_style_unification_20261107/root_nana_victory/packed_victory02/FROZEN.json), [직접 검토129](../work/sprite_style_unification_20261107/root_review_checkpoint129.json). 독립20층/128부분조합·재현2/거부7·원MIPS·원표39/322canvas 검사를 통과했으며 승리의 실제 스테이지클리어는 별도다.

[마지막 전체 모음집 v26](../out/sprite_style_unification_20261107/review_v26/ALL_SPRITES_CURRENT.html)은 BR21/RN30 시점의28폼·4,510표시이며 변경2,546(리코491/시부키718/나나697/린640)의 픽셀·재생검사를 통과했다. 이는 중복 의상·색상·UI를 포함한 표시 수다. 약56%라는 비율은 이 시점 변경 표시 비율일 뿐 고유 원화·품질 완료율이 아니다. 새 통합본 모음집과 범위장부는 다음 갱신 대상이다.

**실제 게임 검증:** RN30 새 부팅·카드 사본에서 등장7 모두 RAM/GPU 일치를 확인했고 [정정된 시간순 캡처](../work/sprite_style_unification_20261107/runtime/nana_arrival30_summary.json)를 직접 검토했다. 전체 포스아머 저장을 불렀어도 등장126..139의 실제 플레이어 표시마스크는0이고140부터15였다. 따라서 새 등장7의 기본형 표시는 실기 확인, 포스 의상은 정적 검사로 구분한다. [직접 검토126](../work/sprite_style_unification_20261107/root_review_checkpoint126.json). RN28의90/91·138/139 양방향 포스 실기와 RN26의88/89·95/96·97/98/99 실기 근거도 보존한다. 사용자F1/F3·RAM쓰기 없음, 실험 세션 종료. [보호40](../work/sprite_style_unification_20261107/protection_checkpoint40.json)의80파일·카드5쌍 불변.

**캡처 검토 방식 수정:** 애니메이션WebP가 동일 화면을 합쳐 저장하는데 옛 검토 도구가 캡처 번호를 파일프레임 번호로 사용한 문제를 발견했다. 누적 표시시간으로 대응시킨 판을 새로 만들었다. RN30 등장3판과 RN26차지6판을 다시 직접 봤으며, RN26의 이전 선택 구간은 병합 전이라 기존 판도 실제로는 영향 없었다. RN28도 프레임 수가 같아 영향 없다. [43녹화 감사](../work/sprite_style_unification_20261107/zero_audit/runtime_webp_index_audit01/report.json). 과거 Nana dash12/Ultimate01의16판은 추가 정정 검토 대상이며 RAM/GPU 로그 증거 자체가 바뀐 것은 아니다.

**진행 중:** 나나 Ultimate90/91은 독립·직접 검토130을 통과해 RN33 통합 중이다. 기본/포스 귀환156 새 몸체와157/158 빛 효과 파생은 조립 중이며, 부분 파츠에서 떨어진7픽셀은 해당 머리/팔 소유층으로 바로잡았다. 시부키85..92와 나나 Ultimate95/96/98/99를 이어서 제작한다. 리코·린의 재작화·일반/블랙·UI 검토 결과를 보존하며 현재 재점검에서 추가 확정 후보는 없다.

시부키 after135 팔과 나나 Ultimate 사다리149/151/153 보정은 이미지 도구 자동 안전검토 거부로 미완료이며 우회하지 않는다. 관련 사다리7참조는 기존 그림을 유지했다. 나나 저체력120..125 실제 발동도 이전 실패로 미검증이다. 전체 미술·전수 실기·최종 사용자 수용 완료를 주장하지 않는다.

'''
p=ROOT/'docs/STATUS.md';old=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.';assert marker in old;p.write_text('# 프로젝트 상태\n\n'+prefix+old[old.index(marker):],'utf8')
p=ROOT/'docs/SPRITE_STYLE_UNIFICATION_20261107.md';old=p.read_text('utf8');title=old.split('\n',1)[0];marker='아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.';assert marker in old;p.write_text(title+'\n\n'+prefix+old[old.index(marker):],'utf8')
print('STATUS and active art log: BR22/RN32, RN30 actual capture limits, continued work')
