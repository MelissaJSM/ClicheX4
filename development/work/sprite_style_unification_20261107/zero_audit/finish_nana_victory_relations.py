from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_ultimate_victory_relations01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
r=json.loads((O/'report.json').read_text(encoding='utf8'))
for v in r['boards']:assert sha(ROOT/v['path'])==v['sha256']
result={'technical_report':{'path':rel(O/'report.json'),'sha256':sha(O/'report.json')},
 'source_sha256':r['source_sha256'],'actually_viewed':r['boards']+r['historical_source'][:1],
 'conclusions':[
  '204/205/206/207은 현재와 원US 모두 각자 raw stream이다. 현재16/16/16/17타일. ±4픽셀 평행이동으로 전신이 같은 쌍은 없고 y>=12 하체도 쌍마다63픽셀 이상 다르다. 한 원화의 하체를 그대로 복사할 근거로 사용하지 않는다.',
  '현재204..207 base는 역사 normalized204..207 전체와 exact, before는 역사 baseline의 전체표시와 exact이다. 원화 프롬프트와 실제 generated_first 열람상204는 빈손 가슴/허리,205는 빈손 경례,206은 얼굴옆 권총,207은 머리 위 권총이다.',
  '현재4개는 별도 광선/번개/오라가 합성된 프레임으로 분류하지 않는다. 실제표시와 원화에 몸/손/권총만 있으며 base와overlay5는 일반색인이다. 입자나 발광을 새로 추가할 근거가 없다.',
  'Ultimate overlay5는 머리만이 아니라 새 재킷 의상을 전신범위로 보완하는 층이다.6/7/8은 현재 빈층.207 overlay5 레코드는89와 실제 주소를 공유하므로 새 의상 기록은 분리 또는89 전체소비 보존 검사가 필요하다.',
  '빈층도 무시하지 않는다.204/206의6/7/8은97/144/145와 공유하고207의6/7/8은86/87/132/146/147/183과 공유한다.같은 레코드주소는 같은 그림이라는 뜻이 아니다.',
  '원표39는81(2calls)→204(3)→205(16)→206(2)→207(48,event0x80)→207(96,relative0)이다.마지막96을 추가정지시간으로 항상실행한다고 주장하지 않는다: caller가relative0에서상태를전환한다.',
  'player_script_victory는item_step4에서39로들어가종료후idle,player_stage_clear는조건D_80173C84==0에서39로들어가종료후40(156..160)와beam_out으로연결한다.207 event0x80의기존func_8001540C(0,0x21,0)호출을보존하며그이벤트를그래픽발광효과로간주하지않는다.',
  '새204205를 우선 제작하더라도 최신81과206207 및마지막156의연속판을검토해야한다.현재시트에서는81의최근상세와구형승리네자세의거친윤곽/얼굴차이가읽히며이것은후속미술정합대상이다.'
 ],
 'visual_limit':'고정원점 재독출3판과 역사 생성원화1장을 실제 열람했다. 새 원화 수용/현재 동작의 게임 실행 검증은 아니다.',
 'preserve':['시간표/이벤트','156..160귀환','참조89의overlay5','모든비대상raw/조립/팔레트','사용자자료/게임/BIN/포인터'],
 'next':'제작자는 새 손/권총과 의상 영역을 해당 원화에서 등록하고 독립수정 범위로 패킹한다. 이 조사는 원화·ARC를 쓰지 않았다.'}
p=O/'conclusions.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':rel(p),'sha256':sha(p)},ensure_ascii=False))
