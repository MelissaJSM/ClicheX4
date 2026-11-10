from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];read=lambda p:json.loads(p.read_text('utf8'))
v=read(ROOT/'out/sprite_style_unification_20261107/review_v33/browser_checks.json');assert v['passed']and len(v['modified_pixel_checks'])==2882
for n in('br_v28','rn_v41'):assert read(W/f'staging_{n}_native_checks.json')['passed']
assert read(W/'runtime/rn41_hover_summary.json')['recorded_captures']==288
assert read(W/'runtime/br28_nova_summary.json')['recorded_captures']==112
assert read(W/'protection_checkpoint50.json')['passed']
snapshot=W/'docs_before_checkpoint42';snapshot.mkdir(exist_ok=False)
for name in('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/name;shutil.copyfile(p,snapshot/name);t=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'if name=='STATUS.md'else'아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.';head,tail=t.split(marker,1)
 start=head.index('최신 검증 통합 시험본');end=head.index('**최근 반영한 작업과 근거**',start)
 head=head[:start]+'''최신 검증 통합 시험본은 [BR28](../out/ver_buki_riko/sprite_style_unification_20261107_v28/shibuki_riko.cue) / [RN41](../out/ver_rin_nana/sprite_style_unification_20261107_v41/rin_nana.cue)다. BIN SHA-256은 BR `13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77`, RN `e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3`. 각251,793섹터·EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사 통과. 활성 배포 포인터·v1.0.0 출시본·사용자 F1/카드와 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`는 보존한다.

[전체 모음집 v33](../out/sprite_style_unification_20261107/review_v33/ALL_SPRITES_CURRENT.html)은 BR28/RN41의28폼·4,510표시 중2,882변경(리코491/시부키866/나나885/린640)을 수록했다. **약63.9%는 중복 의상·색상·UI 포함 변경 표시 비율이며 고유 원화나 품질 완료율이 아니다.** 2,882픽셀 비교와4재생루프 검사를 통과했다. [검사](../out/sprite_style_unification_20261107/review_v33/browser_checks.json).

'''+head[end:]
 anchor='**최근 반영한 작업과 근거**\n\n';assert head.count(anchor)==1
 head=head.replace(anchor,anchor+'''- 시부키 기본/포스·Ultimate 노바 준비213..216을 BR28에 통합했다. 두 후보의 새20층씩, 별칭·부분조합·원순서·독립 읽기·원코드 검사를 결속했다. 기본 미리보기217/220에 강제mask15를 적용했던 오류는 원코드에 맞는0/15로 정정했고 옛판은 최종근거에서 제외했다. [기본 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_nova_base01/FROZEN.json)·[Ultimate 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_nova_ultimate01/FROZEN.json)·[정정검토150](../work/sprite_style_unification_20261107/root_review_checkpoint150.json).
- 나나 기본/포스 호버221..230의 새50층을 RN41에 통합했다. 새머리/베일·공통손/다리·원총구 정합과229/230 굽힌신발20픽셀 보완을 포함한다. 7,296RGBA·498비대상raw·1,090층·1,732조립기록 보존, 동일재현1회/11거부·원MIPS15참조·원표12/84canvas·독립검사를 통과했다. 투명 헤드5개의1파트→0파트 저장변환은 별도 예외이며 원래count0 처리가 검증됐다. EXE와 은행 경계는 그대로다. [동결](../work/sprite_style_unification_20261107/root_nana_hover/packed_hover_final01/FROZEN.json)·[직접23판 검토151](../work/sprite_style_unification_20261107/root_review_checkpoint151.json)·[독립검사](../work/sprite_style_unification_20261107/nana_audit/base_hover_final_independent01/report.json).
''',1)
 anchor='**실제 게임 검증**\n\n';assert head.count(anchor)==1
 head=head.replace(anchor,anchor+'''- BR28 새 부팅·복사 카드 DATA3 획득후Ultimate에서 양방향 노바112캡처·6판을 직접 확인했다. 새 준비4의 추가 확정 분리/큰크기도약은 없었으나217..220은 기존그림으로 남아 있어 새돌진 완성으로 세지 않는다. [실기](../work/sprite_style_unification_20261107/runtime/br28_nova_summary.json).
- RN41 새 부팅·복사 카드 DATA3 포스아머로 정지·전진·후진 호버와 사격288캡처·12판을 확인했다. 새229/230 신발 포함 추가 확정 손/총·발/불꽃 분리나 큰크기도약을 찾지 못했다. 오른쪽을 본 전진/후진 시험이며 왼쪽 방향·부분아머 전수 실기는 별도다. [실기와 한계](../work/sprite_style_unification_20261107/runtime/rn41_hover_summary.json).
''',1)
 head=head.replace('[보호48](../work/sprite_style_unification_20261107/protection_checkpoint48.json)','[보호50](../work/sprite_style_unification_20261107/protection_checkpoint50.json)')
 start=head.index('**진행 중/다음 작업**');end=head.index('**검증 기록 충돌',start)
 head=head[:start]+'''**진행 중/다음 작업**

활성 작업은 네 캐릭터 전체 대기 기준 통일이다. 리코·린 일반/블랙/UI·등장·승리·귀환을 계속 범위에 두며 현재 추가 확정 재작화 후보는 없다. 시부키 차량13+13은 BR27부터 유지하지만 실제 손잡이·발판 검증은 미실행이다. 나나 Ultimate 노바8의 RN40 실기112캡처·6판 근거도 유지한다.

시부키 기본/포스 노바217/220 새몸·원효과 후보 `36d4d029…`는 준비됐고 [직접8판 검토152](../work/sprite_style_unification_20261107/root_review_checkpoint152.json)를 마쳤다. 비대상6참조 저장타일 순열은 표시를 그대로 유지하며 고정은행에 수납했다. 기존 제작기24파트 제한과 원코드 실제count 처리를 구분하여31본체+7파츠 검증/독립검사 후 통합한다. 아직 BR28에는 미포함이다. Ultimate217 새몸과 효과 연결도 제작 중이다.

나나 기본/포스 노바213/215의 새4셀·부분조합을 검토했고214는 원US 외부효과124셀을213몸에 합성한 파생임을 확인했다. 216은215별칭,218/219는효과,220은217몸/효과파생이다. 새217을 만들고 최종20/40층·패킹·원순서·실기 확인을 이어간다. [잔여 분류](../work/sprite_style_unification_20261107/zero_audit/nana_remaining_after_hover_read01/conclusions.json)·[214 출처](../work/sprite_style_unification_20261107/zero_audit/nana_base_nova214_relations01/conclusions.json).

나나 Ultimate 사다리148/149/150/151/152/153/155는 이전 도구 거부/연결 보류 상태로 부모를 보존했다. 재시도나 우회로 완료 처리하지 않는다. 140/208..212의 실루엣·광선은 원화수가 아닌 효과 보존 검토로 관리하며 Ultimate 결과를 PL00에 무근거 확대하지 않는다. 현재 작업을 막는 새로운 사용자 결정은 없다. 전체 완료 및 최종 사용자 수용은 아니다.

'''+head[end:]
 p.write_text(head+marker+tail,'utf8')
print('BR28/RN41; album33 verified2882; Nova112/Hover288 actual; protection50; all-character work continues')
