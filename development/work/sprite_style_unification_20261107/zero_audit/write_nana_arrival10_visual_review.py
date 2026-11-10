from pathlib import Path
import hashlib, json
D=Path('work/sprite_style_unification_20261107/zero_audit/nana_ultimate_arrival10_independent01')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((D/'report.json').read_text('utf8'))
viewed=[]
for i in range(5):
 p=D/f'readback_{i:02}.png';assert sha(p)==r['readback_sheets'][i]['sha256'];viewed.append({'path':p.as_posix(),'sha256':sha(p)})
report={
 'scope':'독립 실제ARC 전후5판,10참조×구/신×양폼40표시를view_image로모두실제열람.',
 'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(D/'report.json'),'actually_viewed':viewed,
 'observations':[
  '133/135~138 새 머릿결과 재킷/맨팔 경계, 무릎·종아리 명암이 이전 큰 색면보다 나뉜다. 정본 권총은 하향→가슴→턱→머리 위로 손과 연결돼 읽힌다.',
  '138/139의 보완된 종아리와 발목·신발 연결이 실제패킹에서도 유지되며, 새로운 확정 절단이나 지나치게 굵은 검정선은 이 판에서 찾지 못했다.',
  '136/137의 원흰선은 새몸과 별도 효과로 표시된다. 원46픽셀 위치 보존은 기술근거이며 총구에 직접붙는 발사선이라고 주장하지 않는다.',
  '130/131 밝은실루엣은 새133의 머리·무기·몸 외곽을 따른다.130 윗부분이 더 드러나는 것은 새실루엣으로 바뀐 결과이며 원반복shell창과 원구체의 보호는 수치검사 근거다.',
  '134는 새133과구체가 이어지고141은 현재대기몸체와입증된12먼지만남는다. 후폼의 구형 의상조각은 이 최종판에서 보이지 않는다.'
 ],
 'new_confirmed_art_defects':[],
 'limitations':['정적40표시만실제열람했으며320부분조합전부를육안으로본것은아니다.','139 y−1과정본권총90도배치는새제작정책으로원US완전동일주장과구분한다.','원순서재생/실제게임/최종루트·사용자수용은별도다.'],
 'runtime_verified':False,'user_final_accepted':False}
p=D/'visual_review.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(p.as_posix(),sha(p))
