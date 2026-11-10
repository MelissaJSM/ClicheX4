from pathlib import Path
import json,hashlib
D=Path(__file__).parent;O=D/'shibuki_ultimate_arrival8_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='8f8cbdfcc553be67209d41cdf49c180866256479b708164ba75890d4bbbe8cb4'
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),
 'actually_viewed':r['readback_sheets'],'observations':[
 '최종 ARC를 독립 재추출한 전체4판과 부분4판을 직접 열람했다. 전체는 구/신 두 의상, 부분은133/136/138/139의0/1/2/4/8/15 마스크다.',
 '133의 머릿결·재킷·맨팔·부츠 명암이 선명해졌으며 바닥 손과 무릎에 새 확정 단절을 찾지 못했다.',
 '136/137의 팔·몸체와 원래 흰 번개가 함께 표시되고 손·머리 경계에 새 확정 절단을 찾지 못했다. 번개는 몸체를 그린 다음 위에 그리는 원래 순서를 실제 조립에서도 확인했다.',
 '138/139의 새 위로 든 맨팔은 손 모임까지 이어지고, 후폼의 잘못된 흰 긴 소매 잔재는 이 최종판에서 찾지 못했다. 두 자세는 별도 원화로 유지된다.',
 '130/131 새 실루엣과134 새 몸체의 바깥 광선·구체 형상은 유지된다. 부분판은 기존 Ultimate의 layer5 의상 교대 구조이며 비어 있는6/7/8로 새 조각이 떠 보이는 문제는 찾지 못했다.'
 ],'new_confirmed_visual_defects':[],'new_runtime_or_native_execution':False,'user_accepted':False,
 'limits':['보류135는 이번 신규 미술 대상이 아니며 부모 그대로 유지된다. 전체 등장 동작의 미술 완료를 뜻하지 않는다.',
 '이 열람은 정적8판에 한정한다. 원순서6판의 루트 직접 열람 및 실제 게임 검증과 별도다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'technical':sha(O/'report.json'),'visual':sha(O/'visual_review.json')}))
