from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
ROOT=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=O/'report.json'
assert sha(report)=='46d17599e8581c1563457902db3d8dd3762c0787a9824501c36fa6600426f378'
d=json.loads(report.read_text('utf-8'))
pic=ROOT/d['sheet']['path']; assert sha(pic)==d['sheet']['sha256']
v={
 'scope':'初期·현재 등장133/135/136/137와 옛 손 보호창 비교1판12표시를 view_image로 실제 열람한 후속 소견.',
 'independent_report_sha256':sha(report),
 'viewed':{'path':d['sheet']['path'],'sha256':sha(pic)},
 'observations':[
   '최초 기본형 등록에는 작은 분홍 권총이133하향·135가슴 앞·136턱 옆·137머리 위에 남는다. 현재 Ultimate의 대응 손은 피부/검정 외곽으로 읽히며 구분 가능한 같은 권총 총열을 확인하지 못했다.',
   '133 첫 손창은 낮춘 맨손을 포함하지만 둘째 창은 현재 신발을 가리킨다.135 첫 창은 대부분 투명이며 검정3픽셀만 있고 피부 인덱스는 없다. 과거 손창 전체가 현재 손접점 좌표라는 해석은 잘못이다.',
   '136/137 첫 창에는 손과 머리/머리띠가 함께 겹치므로 그 사각형의 검정색 전체를 총으로 복사하면 안 된다.',
   '현재136/137의 흰 선은 다리·허리 아래쪽의 원래 별도 효과로 보인다. 새로운 총구 위치로 이동하지 않는다.'
 ],
 'conclusion':'권총의 정확한 보호창을 현재 자료에서 재사용하는 대신 최초 권총 방향과 새 실제 손 좌표를 근거로 수용 정본 모듈을 의미영역에 국소 등록해야 한다.',
 'limits':['새 권총 위치/방향의 최종 미술 및 실제 게임 수용은 별도다.','기존 독립 디자인의 몸체/원화 자체를 수정하지 않았다.'],
 'runtime_verified':False,
 'user_final_accepted':False
}
v['scope']=v['scope'].replace('初期','초기')
out=O/'visual_review.json'; assert not out.exists()
out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
print(sha(out))
