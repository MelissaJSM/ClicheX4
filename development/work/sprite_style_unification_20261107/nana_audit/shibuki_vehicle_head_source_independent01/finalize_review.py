from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
R=O.parents[3]
H=R/'work/sprite_style_unification_20261107/shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'visual_review.json').exists()
report=json.loads((O/'report.json').read_text('utf-8'))
primary=['vehicle_head_ultimate_inputs01/generated_v1.png','vehicle_head_ultimate_native01/comparison.png','vehicle_head_ultimate_native02/comparison.png']
supplemental=['vehicle_head_accessory_read01/four_forms_existing_head.png','prepared_vehicle_head_ultimate01/after_readback_00.png']
def item(s):
 p=H/s
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
v={
 'scope':'実際に読んだ画像の範囲を下記に限定する。',
 'scope_ko':'생성 원화와 고정등록2판 실제 열람. 이전 요청으로 본 기존4폼/후폼 재추출1판은 보조 관찰로 따로 구분한다.',
 'source_reconstruction_report_sha256':sha(O/'report.json'),
 'actually_viewed_primary':list(map(item,primary)),
 'actually_viewed_supplemental':list(map(item,supplemental)),
 'findings':[
  '새 고글 금색은 눈 위의 가로 장식으로 읽히며 아래 홍채와 구분된다. 작은 머리13×15 안에서 새 세로 머릿결의 밝고 어두운 면도 기존 중앙 단색면보다 분명하다.',
  'before의 측면 파랑8셀과 after의 보라색 면은 같은 눈·귀·얼굴 위치를 유지한다. 이 세 원화/등록판에서 새로운 큰 얼굴 왜곡이나 장식 단절은 못 찾았다.',
  '귀 사이1셀 추가/1셀 제거는 생성 원화에서 발생한 새 계단 윤곽이다. 전체크기와 불투명144셀 유지가 알파 전체동일을 뜻하지는 않는다.',
  '금색10표본 중5셀을 실제 팔레트7로 다시 해석한 결과는 최초최근접 등록과 별도로 기록했다. 새팔레트나 비출처 픽셀을 추가한 것은 아니다.',
  '보조 기존4폼판에서 기본·포스는 귀/홍채/옆장식이 읽히지만 중앙의 넓은 밝은 머리면은 국소 명암 보완 후보로 판단했다. 그 의견을 이번 Ultimate 출처검사 통과와 합쳐 기본·포스 완료로 세지 않는다.'
 ],
 'limits':['후보ARC를본감사에서직접디코딩하지않음:HUD의별도검사','보조after재추출1판을전체19위치독립시각전수로확대하지않음','실제조종석/좌우반전/탑승이벤트/실기는미실행','원화·부모·후보변경없음']}
v['scope']='생성 원화 및 등록 비교판의 실제 열람 범위를 명시한 정적 의견.'
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p,h in report['inputs'].items():assert sha(R/p)==h,p
files={p.relative_to(R).as_posix():sha(p)for p in O.iterdir()if p.is_file()and p.name!='READER_LOCK.json'}
lock={'scope':'원화 직접 재구성38층 및 실제원화/등록판 열람의 독립 근거. 제작 모듈 미호출.','inputs':report['inputs'],'outputs':files,'candidate_sha256':report['candidate_sha256']}
(O/'READER_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'lock':sha(O/'READER_LOCK.json')},ensure_ascii=False))
