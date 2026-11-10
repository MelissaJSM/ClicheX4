from pathlib import Path
import json, shutil, re
W=Path(__file__).resolve().parent; ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'))
assert read(W/'runtime/br31_vehicle_summary.json')['recorded_vehicle_captures']==224
assert read(W/'protection_checkpoint55.json')['passed']
snap=W/'docs_before_checkpoint47'; snap.mkdir(exist_ok=False)
runtime='''- BR31 새 부팅·복사 카드 DATA3 포스아머로 마그마 구역1→2를 정상 진행하여 라이드 아머에 탑승했다. 탑승 후224캡처/222인코딩프레임·직접17파일에서 양방향 짧은 이동/공격, 오른쪽 점프/공중공격/착지, 양방향 하차→재탑승을 확인했다. 관찰한 머리/조종석 표본에 추가 확정 부유·잘림·큰 크기 도약은 없었다. 상주 PL00 그래픽/조립/팔레트3항목 전체와 활성 포인터도 BR31 일치(스냅샷188)다. 후반 크롭2판의 머리 잘림은 같은 녹화를 넓게 다시 뽑아 구분했다. 초기 낙하/피격 및 게이트 앞 정체는 조작 실패 기록으로 남겼으며, 코어 높이에 맞춘 공격 후 구역2 진입에 성공했다. 기본/부분/Ultimate·다른 캐릭터 탑승·체이서 손잡이/발판·모든60Hz/19참조 전수는 별도다. [실기와 한계](../work/sprite_style_unification_20261107/runtime/br31_vehicle_summary.json)·[상주 자원](../work/sprite_style_unification_20261107/runtime/br31_vehicle_resident01.json).
'''
for name in ('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/name; shutil.copyfile(p,snap/name); t=p.read_text('utf8')
 marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.' if name=='STATUS.md' else '아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.'
 head,tail=t.split(marker,1)
 old='작은 머리의 실제 조종석 가림 검증은 아직 하지 않았다.'
 assert head.count(old)==1
 head=head.replace(old,'포스아머 작은 머리는 아래 실제 탑승 표본까지 확인했고, 나머지 의상/전체 참조 실기는 남아 있다.')
 anchor='**실제 게임 검증**\n\n'; assert head.count(anchor)==1
 head=head.replace(anchor,anchor+runtime,1)
 head=head.replace('[보호54](../work/sprite_style_unification_20261107/protection_checkpoint54.json)','[보호55](../work/sprite_style_unification_20261107/protection_checkpoint55.json)')
 head=head.replace('**새 BR31 실제 탑승 플레이나 체이서 손·발 접점 검증을 대신하지 않는다.**','**정적 비교의 근거다. 이후 BR31 포스 실제 탑승은 위 별도 기록으로 검증했으며, 체이서 손·발 접점 검증을 대신하지 않는다.**')
 head=head.replace('다음은 실제 차량 작은 머리의 조종석 가림·손잡이/발판, 기본 의상+발파츠와 나머지 부분 아머, 기존 대기와 짧은 전환의 추가 확인이다.','다음은 다른 의상의 차량 작은 머리, 라이드 체이서 손잡이/발판, 기본 의상+발파츠와 나머지 부분 아머, 기존 대기와 짧은 전환의 추가 확인이다. 시부키 포스 실제 라이드 아머 표본은 위 기록으로 추가했지만 전수 완료는 아니다.')
 progress='이번 차량 실기 검증에서는 새 원화를 추가하지 않아 변경 표시 비율은67.9%로 유지한다. 남은32.1% 전부가 미수정 결함이라는 뜻은 아니다. 원래 효과·빈 참조·수용 보존 항목을 포함하므로 재작화 수와 품질 검증 상태를 별도로 관리한다.\n\n'
 anchor='**진행 중/다음 작업**\n\n'; assert head.count(anchor)==1
 head=head.replace(anchor,anchor+progress,1)
 for link in re.findall(r'\]\(([^)]+)\)',head):
  if link.startswith('../'):
   assert (p.parent/link.split('#')[0]).exists(),link
 p.write_text(head+marker+tail,'utf8')
print('BR31/RN43 unchanged; vehicle224 captures/17 viewed files; protection55; whole task incomplete')
