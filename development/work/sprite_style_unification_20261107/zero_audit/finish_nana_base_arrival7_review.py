from pathlib import Path
import hashlib,json
D=Path(__file__).parent; O=D/'nana_base_arrival7_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='be6dad6568f350ccb5ea69084afaebb256e8ffc69d79f4e2616d11c2c3034993'
names=['readback_130.png','readback_133.png','readback_135.png','readback_137.png','partial_133.png','partial_136.png']
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),
 'actually_viewed':[{'path':str(O/n),'sha256':sha(O/n)} for n in names],
 'observations':[
 '실제 후보 ARC를 독립 재추출한 구/신 전체4판과 부분2판을 직접 열람했다. 부분판은133/135/136/137의 head/body/arms/legs/body+legs 다섯 조합이다.',
 '133/134의 낮은 자세와135..137의 선 자세에서 새 머릿결·검정 의상·부츠 명암이 선명해졌고 손목·무릎·발목에 새 확정 단절을 찾지 못했다.',
 '130/131의 구체·광선과134의 구체가 새 몸체와 함께 보인다.136/137의 원 흰46픽셀은 허리 아래를 가로지르는 위치로 남으며 발사 총구와 직접 연결된 효과라고 해석하지 않았다.',
 '부분판에서 베일은 머리 교대와 이어지고, legs 단독 및 body+legs에서 맨다리·붉은 구두가 연결된다. 이번 여섯 판에서 따로 뜬 베일 조각이나 부츠 잔재의 새 확정 결함을 찾지 못했다.',
 '137의 위로 든 손·권총과 얼굴/머리 경계가 연결되어 보인다. 이 정적 관찰은 실제 탄환 발원점 검증을 대신하지 않는다.'
 ],'new_confirmed_visual_defects':[], 'producer_functions_called':False,
 'new_runtime_or_native_execution':False,'user_accepted':False,
 'limits':['정적 여섯 판과 독립 기술 대조의 범위다. 루트 원순서 열람·원MIPS·재현 검사는 별도 근거다.',
 '인접138/139와140..142의 신규 제작 완료 또는 전체 등장 동작 완료를 뜻하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'technical':sha(O/'report.json'),'visual':sha(O/'visual_review.json')}))
