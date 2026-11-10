from pathlib import Path
import hashlib,json
D=Path(__file__).parent;O=D/'nana_base_settle2_independent01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='bc5269ec1e23fb2823b254303da1a83b4b21724d33fa48c989c1e060d621489c'
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),
 'actually_viewed':r['readback_sheets'],
 'observations':[
 '최종 ARC에서 별도 재추출한138/139 전체비교1판과 부분조합1판을 실제 열람했다.',
 '기본 새 뒷머리의 분홍 명암층과 포스 베일의 검정/회색 접힘이 기존보다 구분된다. 새 머릿결 표본으로 외곽 부피나 눈 위치가 갑자기 바뀐 인상은 보이지 않는다.',
 '위로 든 권총과 손 피부·손목 연결이 두폼에서 이어진다. 원화 무기와 정본 모듈이 따로 떠 있는 확정 분리를 찾지 못했다.',
 '포스 무릎·정강이·신발 연결과 기본 부츠가 각 재질로 읽힌다. 부분 body-only에는 뒤쪽 베일 조각이 따로 남지 않고 legs/body+legs에서 연결된 베일이 함께 표시된다.',
 '139는138에서 전체가 한픽셀 위로 이동하는 동일형상이며 이 두 정적 행 사이에 새로운 머리/권총/의상 교체 흔들림을 찾지 못했다.'
 ],'new_confirmed_visual_defects':[],'runtime_verified':False,'native_MIPS_executed_here':False,'user_accepted':False,
 'limits':['원표2/95/96 실제 연속재생이나 게임장면은 이번 정적 열람에 포함하지 않는다.','이미 실행된 원MIPS는 후보와 두decoded 해시를 결속했으며 독립 재실행했다고 쓰지 않는다.','전체 미술 완료 또는 사용자 수용을 의미하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'inputs':r['locked_inputs']}))
