"""완료된 읽기 계산에 실제 열람 및 제작자 전달용 요약을 별도 결속한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'shibuki_ultimate_arrival_relations01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
r=json.loads((O/'report.json').read_text(encoding='utf8'))
viewed=[]
for q in r['sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];viewed.append(q)
data={
 'kind':'읽기 관계 조사 및 실제 정적 이미지 열람. 새 후보 승인/실기 아님.',
 'technical_report':{'path':rel(O/'report.json'),'sha256':sha(O/'report.json')},
 'source_sha256':r['source_sha256'],'actually_viewed_sheets':viewed,
 'visual_observations':[
  '126..129는 전후 의상과 무관한 빛줄기/구체로 보이며 현재 표시가 같다.',
  '130/131은 몸체 실루엣과 광선,132는 몸체 없는 광선,134는 구체 앞의 실제색 몸체이다. 전체FX를 같은 유형으로 바꾸면 안 된다.',
  '135/136은 가슴 부근의 두 손과 상체 자세/명암이 달라 보인다. 원 번개를 뺀 현재 표시도 단순 평행이동과 일치하지 않는다.',
  '138/139 재킷은 한 픽셀 상승과 맞는다. 맨팔에서 남는 차이는 기록된 몸통/의상 영역 안에 있으며 새 양폼의 y-1 통일은 제작 정책으로 구분해야 한다.',
  '141은 현재 대기와 같은 몸 양옆에 작은 흰 먼지점이 있고142는 먼지가 없는 대기와 같다.140은 대기 실루엣과 양옆 번개이다.'
 ],
 'rules':[
  {'refs':[126,127,128,129,132],'decision':'기존 효과 전체 보존.132는131과 저장 stream을 공유하므로131 변경시 별도 표시/소비타일 보호.'},
  {'refs':[130],'decision':'역사 production14의133 알파/원광선 매핑으로 재현하되 현재 예외3셀도 보존. 새133으로 실루엣 교체시 옛 몸 지지는 역사 배경으로 복원하고 새 몸을9로 표시한다.',
   'exception_cells':[{'x':x,'y':23,'historical_background':14,'current':9} for x in (-1,0,1)],
   'exception_condition':'세 셀은 옛몸 밖의 기존수정이다. 새몸 영역에 들면 그 몸 실루엣9가 같은값을 내며, 밖이면 현재9를 그대로 유지한다.'},
  {'refs':[131],'decision':'현재 after133 알파를 색인9로 원광선 위 합성하면 exact. 새133 채택시 연동 필요.'},
  {'refs':[134],'decision':'각폼의 실제색133을 역사129구체 위에 얹으면 exact. 기본형의 밝은색 리맵을 PL02 복원 규칙이라고 쓰지 않는다.'},
  {'refs':[135,136],'decision':'현재 양폼 및 원US 모두 y-1 alias 아님. 수용한 새기본135를 새136에 전개하려면 신규 제작 정책으로 기록하고 몸체/손/다리 연속 미술 검토.',
   'current_differences_with_original_fx':{'before':346,'after':349}},
  {'refs':[136,137],'decision':'역사 logical tile7의 원번개46px씩과 두 파츠의 좌표/flip 보존.136은 y4,137은 y-8/flipY이며 손에서 발사되는 효과라고 추정하지 않는다.'},
  {'refs':[138,139],'decision':'현재 before는 y-1 exact,after는135px 차이. 원US는 양폼 exact 아님. 두폼새138 y-1은 허용된 기본형 아트 적용 정책으로 분리.',
   'after_difference_bbox_halfopen':[-10,-4,11,11]},
  {'refs':[140],'decision':'현재 대기0 알파9+역사 tile8 번개46px exact.133 파생이 아님. 대기 미변경이면 그대로 보존.'},
  {'refs':[141,142],'decision':'141=각폼 현재idle0+동일원먼지12px,142=idle0 모든5층 exact. 현재 연결은 보존 대상이며 새등장 몸으로 덮지 않는다.'}
 ],
 'storage_hazards':{
  'raw_groups':[[126,127],[131,132],[0,142]],
  'composition_overlap_note':'각 report.frames.layers.record_storage_overlap_owners는 실제 같은 레코드 주소를 소비하는 목록이다. 같은 그림이라는 뜻이 아니다. 빈6/7/8층의 별칭도 원레코드를 직접 수정하면 영향을 받을 수 있다.',
  'critical_nonarrival_owners':[
   {'refs':[135,136,137,142],'part_bank':0,'outside_owners':[0,87,92,97,119,206]},
   {'refs':[141,142],'part_bank':5,'outside_owners':[0]},
   {'refs':[141,142],'part_banks':[6,7,8],'outside_owners':[0,156]}
  ],
  'requirement':'새 파츠는 소유권을 확인한 레코드에만 기록/분리하고 외부 공유자 모든 소비 레코드/타일과 실제 표시를 보존한다.'
 },
 'sequence_dependency':{
  'source':r['animation_table'],
  'arrival2':[127,128,129,130,131,130,132,134,133,135,136,137,138,139,140,141,142,142],
  'special95':[138,139,96,95,96,96],
  'special96':[138,139,96,95,96],
  'note':'138/139는 등장 이외 원표95/96(프로스트타워/소울바디)에도 있다. 원 이벤트139/96와 시간은 보존. 이번에는 기존 원표 파일만 읽었으며 실제 호출/MIPS/게임을 새로 실행하지 않았다.'
 },
 'not_done':['새 원화 제작/등록/패킹','새 후보 GPU/MIPS 검사','게임 실기','사용자 미술 수용']
}
p=O/'conclusions.json';p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':rel(p),'sha256':sha(p),'viewed_sheets':len(viewed)},ensure_ascii=False))
