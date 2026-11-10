from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];read=lambda p:json.loads(p.read_text('utf8'))
v=read(ROOT/'out/sprite_style_unification_20261107/review_v34/browser_checks.json');assert v['passed']and len(v['modified_pixel_checks'])==2914
for n in('br_v29','rn_v42'):assert read(W/f'staging_{n}_native_checks.json')['passed']
assert read(W/'runtime/br29_nova_summary.json')['recorded_captures']==112
assert read(W/'protection_checkpoint51.json')['passed']
snapshot=W/'docs_before_checkpoint43';snapshot.mkdir(exist_ok=False)
for name in('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/name;shutil.copyfile(p,snapshot/name);t=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'if name=='STATUS.md'else'아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.';head,tail=t.split(marker,1)
 start=head.index('최신 검증 통합 시험본');end=head.index('**최근 반영한 작업과 근거**',start)
 head=head[:start]+'''최신 검증 통합 시험본은 [BR29](../out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.cue) / [RN42](../out/ver_rin_nana/sprite_style_unification_20261107_v42/rin_nana.cue)다. BIN SHA-256은 BR `753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252`, RN `11bd3ecd39e4456ca21a759304400d61cfe5c0981abed55b93fd0377c3ea18a8`. 각 251,793섹터·EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사 통과. 활성 배포 포인터·v1.0.0 출시본·사용자 F1/카드와 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`는 보존한다.

[전체 모음집 v34](../out/sprite_style_unification_20261107/review_v34/ALL_SPRITES_CURRENT.html)은 BR29/RN42의 28폼·4,510표시 중 2,914변경(리코491/시부키880/나나903/린640)을 수록했다. **약64.6%는 중복 의상·색상·UI 포함 변경 표시 비율이며 고유 원화나 품질 완료율이 아니다.** 2,914픽셀 비교와 4재생루프 검사를 통과했다. [검사](../out/sprite_style_unification_20261107/review_v34/browser_checks.json).

'''+head[end:]
 anchor='**최근 반영한 작업과 근거**\n\n'
 head=head.replace(anchor,anchor+'''- 시부키 기본/포스 노바217/220 및 Ultimate217..220의 새 돌진 몸·효과를 BR29에 통합했다. 기본 새10층·Ultimate 새20층, 원래 준비→돌진→복귀 순서와 부분조합을 검사했다. 기본31본체+7파츠는 원코드의 실제16bit count와 풀 경계에서 검사했으며 제작기의 옛24파트 제한과 구분했다. Ultimate220의 몸 가림에 따른 효과93픽셀 변화는 기록된 변경이며 전체효과 바이트불변으로 주장하지 않는다. [기본 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_nova_strike_base01/FROZEN.json)·[Ultimate 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_nova_strike_ultimate01/FROZEN.json)·[직접검토155](../work/sprite_style_unification_20261107/root_review_checkpoint155.json).
- 나나 기본/포스 노바213/214/215/216/217/220 새30층을 RN42에 통합했다. 두 의상 새6셀, 214 원외부효과124픽셀, 216별칭, 217테두리와 220몸/효과를 구분하고 218/219는 보존한다. 7,296RGBA·502비대상raw·1,110층·1,757조립·부분192·114GPU와 원표13스텝/48canvas·독립검사를 통과했다. [동결](../work/sprite_style_unification_20261107/nana_audit/base_nova_repaint/packed_nova_candidate_v1/FROZEN.json)·[직접9판 검토156](../work/sprite_style_unification_20261107/root_review_checkpoint156.json). 새 기본/포스 노바의 실제 게임 검증은 아직 별도다.
''',1)
 anchor='**실제 게임 검증**\n\n'
 head=head.replace(anchor,anchor+'''- BR29 새 부팅·복사 카드 DATA3 획득 후 Ultimate에서 새 돌진 몸을 포함한 양방향 노바 준비·돌진·점멸·복귀를 112캡처/111인코딩프레임·6판으로 직접 확인했다. 확인한 표본에서 추가 확정 절단·큰 크기 도약은 보이지 않았다. 적 효과가 가린 모든 픽셀이나 60Hz 전수를 검증한 것은 아니다. [실기와 한계](../work/sprite_style_unification_20261107/runtime/br29_nova_summary.json).
''',1)
 head=head.replace('[보호50](../work/sprite_style_unification_20261107/protection_checkpoint50.json)','[보호51](../work/sprite_style_unification_20261107/protection_checkpoint51.json)')
 start=head.index('**진행 중/다음 작업**');end=head.index('**검증 기록 충돌',start)
 head=head[:start]+'''**진행 중/다음 작업**

네 캐릭터 전체 대기 기준 통일을 계속한다. 리코·린의 일반/블랙/UI·등장·승리·귀환을 계속 범위에 두며 현재 추가 확정 재작화 후보는 없다. 시부키 차량13+13은 BR27부터 유지하지만 실제 손잡이·발판 검증은 미실행이다. 나나 Ultimate 노바8의 RN40 실기112캡처·6판 근거도 유지한다.

시부키 기본/포스와 Ultimate 호버221..230의 새 몸·사격 팔을 제작 중이다. 기본은 실제 진입 가능한 mask8, 포스는15이며 하체8 공유·머리5·몸통6·팔7 정책과 원래 제트15위상·발사점5좌표를 확인했다. 새229의 긴 귀/낮은 손, Ultimate 일부 사격의 추가 팔/총구 이동은 발견 즉시 보류하고 국소 교정한다. 새 호버는 아직 BR29에 포함되지 않았다. [PL00 소유 조사](../work/sprite_style_unification_20261107/zero_audit/shibuki_base_hover_ownership01/conclusions.json).

나나 PL00 등장 섬광140은 현재 대기의 의상 추가 알파149픽셀을 복원한 후보 `2822a938…`를 준비했다. 기존46광선·10타일·208..212는 보존하고 원MIPS·7,296RGBA·독립검사 및 [직접3판 검토157](../work/sprite_style_unification_20261107/root_review_checkpoint157.json)를 통과했다. [동결](../work/sprite_style_unification_20261107/nana_audit/base_flash140_restore01/packed_flash_candidate_v1/FROZEN.json). RN42에는 미포함이며 다음 시험본에 통합한다.

**효과 분류 정정:** 208..212는 플레이어 귀환이 아니라 소울보디 분신 소멸이다. 원호출자가 아머를 그리지 않으므로 현재 공통 실루엣을 보존한다. 210은 과거 제작기의 수평좌표0.45배 산포와 현재298픽셀이 정확히 같으며 단순 bbox 축소로 추정하지 않는다. 140은 등장 이벤트에서 아머마스크를 복원한 후 그려지므로 의상 실루엣 보완이 가능하다. 원US140에도 아머층은 비어 있었으므로 이번 보완은 원본 누락 복구가 아니라 현재 캐릭터 외형을 일치시키는 변경이다. [호출 근거](../work/sprite_style_unification_20261107/zero_audit/nana_base_effect_callers01/conclusions.json).

나나 Ultimate 사다리148/149/150/151/152/153/155와 시부키 Ultimate135는 이전 도구 거부/보류로 부모를 보존했다. 재시도·우회로 완료 처리하지 않는다. 현재 작업을 막는 새로운 사용자 결정은 없다. 전체 완료 및 최종 사용자 수용은 아니다.

'''+head[end:]
 p.write_text(head+marker+tail,'utf8')
print('BR29/RN42; album34 verified2914; Nova112/111 actual; protection51; 140/hover pending')
