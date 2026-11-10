from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];read=lambda p:json.loads(p.read_text('utf8'))
v=read(ROOT/'out/sprite_style_unification_20261107/review_v35/browser_checks.json');assert v['passed']and len(v['modified_pixel_checks'])==2916
assert read(W/'staging_rn_v43_native_checks.json')['passed']and read(W/'protection_checkpoint52.json')['passed']
snapshot=W/'docs_before_checkpoint44';snapshot.mkdir(exist_ok=False)
for name in('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/name;shutil.copyfile(p,snapshot/name);t=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'if name=='STATUS.md'else'아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.';head,tail=t.split(marker,1)
 head=head.replace('[RN42](../out/ver_rin_nana/sprite_style_unification_20261107_v42/rin_nana.cue)','[RN43](../out/ver_rin_nana/sprite_style_unification_20261107_v43/rin_nana.cue)').replace('`11bd3ecd39e4456ca21a759304400d61cfe5c0981abed55b93fd0377c3ea18a8`','`e751a82bc3d1e228d26389d911ca4b46efa12612dcea69b6c99fdeb3ba3ca637`')
 head=head.replace('모음집 v34','모음집 v35').replace('/review_v34/','/review_v35/').replace('BR29/RN42의','BR29/RN43의').replace('2,914','2,916').replace('나나903','나나905').replace('약64.6%','약64.7%')
 anchor='**최근 반영한 작업과 근거**\n\n';head=head.replace(anchor,anchor+'- 나나 등장 섬광140의 의상 추가 알파149픽셀을 RN43에 통합했다. 기본 섬광·기존46광선·원10타일·208..212 보존, 원MIPS·독립검사·부분32 및 최종3판 검토를 결속했다. [동결](../work/sprite_style_unification_20261107/nana_audit/base_flash140_restore01/packed_flash_candidate_v1/FROZEN.json)·[직접 검토157](../work/sprite_style_unification_20261107/root_review_checkpoint157.json).\n',1)
 anchor='**실제 게임 검증**\n\n';head=head.replace(anchor,anchor+'''- RN43 새 부팅·복사 카드 DATA3 포스아머에서 오른쪽 노바1회의 준비·새 돌진·효과·복귀를112캡처·6판으로 확인했다. 확인 표본의 추가 확정 절단·큰 크기 도약은 없었다. 두 번째 입력에서는 발동하지 않아 왼쪽 성공으로 세지 않는다. [실기](../work/sprite_style_unification_20261107/runtime/rn43_nova_summary.json).
- RN43 등장319캡처/285인코딩프레임과 직접4판에서는 READY·광선·착지·준비·포스 대기 연결을 확인했다. **140의3틱 의상 섬광 자체는 약16Hz 표본에서 미포착**이므로 실기 확인 완료로 세지 않는다. 8.281초의 다른 구형 효과 속 실루엣과 혼동하지 않는다. [관찰 한계](../work/sprite_style_unification_20261107/runtime/rn43_arrival_summary.json).
''',1)
 head=head.replace('새 기본/포스 노바의 실제 게임 검증은 아직 별도다.','새 기본/포스 노바의 실기는 아래 RN43 포스 오른쪽1회로 제한한다.')
 head=head.replace('[보호51](../work/sprite_style_unification_20261107/protection_checkpoint51.json)','[보호52](../work/sprite_style_unification_20261107/protection_checkpoint52.json)')
 start=head.index('나나 PL00 등장 섬광140은');end=head.index('**효과 분류 정정:**',start)
 head=head[:start]+'''시부키 Ultimate 호버50층 후보 `3f168863…`는 [직접 최종11판 검토159](../work/sprite_style_unification_20261107/root_review_checkpoint159.json), 독립 읽기·원MIPS10·3재현/18거부·원순서3000canvas 검사를 마쳤고 다음BR 통합을 준비한다. 222 손목은 밝은바탕에서도 연결되고228은 원래 짧은 발사점에 맞춰 팔을 굽힌 자세다. 기존 판과 실제 게임의 접점 검증은 별도로 유지한다.

기본/포스 호버는 새10몸의 독립 제트/얼굴 검토 후 공통 얼굴·손·하체를 정합 중이다.223 오른신발1행 등록과225 포스 하체 공통사용,229 부분mask10/11의1픽셀 의상연결을 보완한 진단을 준비했다. 기존 머리층이 높은 팔을 선택하지 않도록 팔 의미영역도 분리했다. 아직 사격5쌍·최종패킹·실기가 남으며 완료로 세지 않는다.

'''+head[end:]
 p.write_text(head+marker+tail,'utf8')
print('BR29/RN43; album35 verified2916; RN43 rightNova1; flash140 not captured; protection52')
