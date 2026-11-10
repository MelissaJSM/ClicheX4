from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
prefix='''**2026-11-08 / EXPANSION — 네 캐릭터 모든 의상의 대기 기준 세부 묘사 통일 작업 진행 중. 전체 미완료.** 사용자의 진행도 질문은 작업 중단 지시가 아니다. 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 범위에 유지한다.

통합과 원MIPS/GPU 검사를 마친 최신 시험본은 [BR22](../out/ver_buki_riko/sprite_style_unification_20261107_v22/shibuki_riko.cue) / [RN34](../out/ver_rin_nana/sprite_style_unification_20261107_v34/rin_nana.cue)다. BIN SHA-256은 BR `54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99`, RN `43b63a99328f4aa4e2aa004e8799834397efe91ff4510a36d4cd6b4dd48445d0`. 전251,793섹터 비교·EDC/ECC·재추출·EXE 보존 검사 통과. 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`, 활성 포인터·출시본·사용자 저장은 보존한다.

BR22는 시부키 네 의상의 특수95/96/97을 추가했다. [직접 검토127](../work/sprite_style_unification_20261107/root_review_checkpoint127.json). PL00 고정 그래픽항목 내부280B 재배치는 실제 원로더·디렉터리508참조 검사와 독립 비대상 보존검사를 통과했으며 EXE/LBA/외부항목은 그대로다. 새 사용자 승인 문구를 만들어 기록하지 않는다.

RN29/30은 나나 Ultimate 사다리7과 기본/포스 등장7, RN31은 Ultimate88/89/97, RN32는 기본/포스 승리204..207, RN33은 Ultimate90/91, RN34는 기본/포스 귀환156..158을 추가했다. 승리206 초안의 긴 다리는 반려했고 새 원화로 수정했다. 귀환의 부분 아머에서 떨어졌던7셀은 소유층을 바로잡았으며 원래157의 빛 윤곽 규칙과158의 상승/159빛을 보존했다. [귀환 동결](../work/sprite_style_unification_20261107/root_nana_return/packed_return03/FROZEN.json), [직접 검토131](../work/sprite_style_unification_20261107/root_review_checkpoint131.json), [독립검사](../work/sprite_style_unification_20261107/zero_audit/nana_base_return3_independent01/report.json). 귀환15층·96부분조합·재현2/거부7·원MIPS·원표3/40의724canvas 검사 통과. 새 승리·귀환·Ultimate90/91의 실제 게임 발동은 별도 미검증이다.

[최신 전체 모음집 v27](../out/sprite_style_unification_20261107/review_v27/ALL_SPRITES_CURRENT.html)은 BR22/RN34의28폼·4,510표시이며 변경2,592(리코491/시부키733/나나728/린640)의 픽셀·4재생루프 검사를 통과했다. 약57.5%는 중복 의상·색상·UI를 포함한 변경 표시 비율이며 고유 원화·품질 완료율이 아니다.

**실제 게임 검증:** RN30 새 부팅·카드 사본에서 등장7 모두 RAM/GPU 일치를 확인했고 [시간순 캡처](../work/sprite_style_unification_20261107/runtime/nana_arrival30_summary.json)를 직접 검토했다. 전체 포스 저장이어도 등장126..139의 실제 표시마스크는0,140부터15였다. 따라서 새 등장7의 기본형 표시는 실기 확인, 포스는 정적 검사다. RN28의90/91·138/139 양방향 포스 실기와 RN26의88/89·95/96·97/98/99 실기 근거도 보존한다. 사용자F1/F3·RAM쓰기 없음, 세션 종료. [보호41](../work/sprite_style_unification_20261107/protection_checkpoint41.json)의80파일·카드5쌍 불변.

**캡처 검토 방식 수정:** 같은 화면을 합치는 animated WebP와 캡처 번호를 혼동한 옛 도구를 수정했다. RN30 등장3판·RN26차지6판은 직접 재검토했다. 과거 Nana dash12/Ultimate01의16판도 시간 대응을 교정한 뒤 담당 검토자가 열람했다([교정 근거](../work/sprite_style_unification_20261107/zero_audit/nana_legacy_timeline_review01/manifest.json)). 이16판은 옛RN12/RN9 근거이며 최신 그림의 실기 검증으로 계산하지 않는다. 원본 영상·RAM/GPU 로그는 보존했다.

**진행 중:** 나나 기본/포스 라이드 체이서162..174의 새 몸체8개와 원래 평행이동 파생9개를 조립 중이다. 시부키85..92와 나나 Ultimate95/96/98/99를 이어서 제작한다. 새 승리·귀환에 대응하는 RN 선택화면18..21 사본 동기화도 남아 있다. 리코·린의 재작화·일반/블랙·UI 검토 결과를 보존하며 현재 재점검에서 추가 확정 후보는 없다. 범위장부09 갱신 중이다.

시부키 after135 팔과 나나 Ultimate 사다리149/151/153 보정은 이미지 도구 자동 안전검토 거부로 미완료이며 우회하지 않는다. 관련 사다리7참조는 기존 그림을 유지했다. 나나 저체력120..125 실제 발동도 이전 실패로 미검증이다. 전체 미술·전수 실기·최종 사용자 수용 완료를 주장하지 않는다.

'''
for name,marker in [('STATUS.md','아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'),('SPRITE_STYLE_UNIFICATION_20261107.md','아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.')]:
 p=ROOT/'docs'/name;old=p.read_text('utf8');assert marker in old;p.write_text(old.split('\n',1)[0]+'\n\n'+prefix+old[old.index(marker):],'utf8')
print('BR22/RN34, album27, protection41, continued full scope')
