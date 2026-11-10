from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];read=lambda p:json.loads(p.read_text('utf8'))
v=read(ROOT/'out/sprite_style_unification_20261107/review_v36/browser_checks.json');assert v['passed']and len(v['modified_pixel_checks'])==2936
assert read(W/'staging_br_v30_native_checks.json')['passed']and read(W/'protection_checkpoint53.json')['passed']
assert read(W/'runtime/br30_hover_summary.json')['recorded_captures']==288
snapshot=W/'docs_before_checkpoint45';snapshot.mkdir(exist_ok=False)
for name in('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/name;shutil.copyfile(p,snapshot/name);t=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'if name=='STATUS.md'else'아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.';head,tail=t.split(marker,1)
 head=head.replace('[BR29](../out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.cue)','[BR30](../out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.cue)').replace('`753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252`','`ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875`')
 head=head.replace('모음집 v35','모음집 v36').replace('/review_v35/','/review_v36/').replace('BR29/RN43의','BR30/RN43의').replace('2,916','2,936').replace('시부키880','시부키900').replace('약64.7%','약65.1%')
 anchor='**최근 반영한 작업과 근거**\n\n';head=head.replace(anchor,anchor+'- 시부키 Ultimate 호버221..230의 50층을 BR30에 통합했다. 새 몸5·사격5, 원래 발사점에 맞춘 버스터60불투명+11투명 보호영역, 원래 추진 불꽃15단계·탄환7을 검증했다. 원MIPS10·3재현/18거부·원순서3000canvas 및 독립 검사, 최종11판 직접 검토를 연결했다. [동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_hover_ultimate01/FROZEN.json)·[직접 검토159](../work/sprite_style_unification_20261107/root_review_checkpoint159.json).\n',1)
 anchor='**실제 게임 검증**\n\n';head=head.replace(anchor,anchor+'- BR30 새 부팅·복사 카드 DATA3 획득 후 Ultimate에서 호버 전진/후진/정지 및 사격을288캡처·직접11판(넓은 사격 크롭 포함)으로 확인했다. 관찰한 표본에서 발·추진 불꽃 및 어깨·팔·버스터 연결을 확인했고 추가 확정 절단·큰 크기 도약은 발견하지 못했다. 오른쪽을 바라본 검증이며 왼쪽 방향·기본/포스·60Hz 전수는 미확인이다. [실기와 한계](../work/sprite_style_unification_20261107/runtime/br30_hover_summary.json).\n',1)
 head=head.replace('[보호52](../work/sprite_style_unification_20261107/protection_checkpoint52.json)','[보호53](../work/sprite_style_unification_20261107/protection_checkpoint53.json)')
 start=head.index('시부키 Ultimate 호버50층 후보');end=head.index('**효과 분류 정정:**',start)
 head=head[:start]+'''시부키 Ultimate 호버는 위 BR30에 통합·제한 실기 검증했다. 기본/포스 호버는 10개 몸의 공통 얼굴·손·하체와80부분 조합을 검토했다.223 오른신발1행 등록(겹친8픽셀 존재)·225 공통 하체·229 부분 연결을 보완했고, 높은 팔이 머리층에 들어가지 않도록 분리했다. 최종 body04는 body03과 픽셀이 같고 설명문 인코딩만 고쳤다.

기본/포스 사격5쌍의 원화 생성과 고정96셀 등록을 진행했다. 첫 페이지의 불필요한 세 번째 손은 반려 후 국소 재제작했다. 등록5비교판은 직접 열람했지만, 얼굴·공통 하체 보호와 원래 버스터 모듈에 팔을 접합하는 단계가 남는다. 현재 게임 자원에 이 기본/포스 호버 후보를 넣지 않았다. 작은 차량머리도 대기와 다른 평면적 머릿결·장식 누락을 추가 교정 중이며 완료로 세지 않는다.

'''+head[end:]
 p.write_text(head+marker+tail,'utf8')
print('BR30/RN43; album36 verified2936; hover288captures; protection53; full work incomplete')
