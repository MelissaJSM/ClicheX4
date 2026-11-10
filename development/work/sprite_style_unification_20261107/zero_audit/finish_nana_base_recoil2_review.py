from pathlib import Path
import json,hashlib
D=Path(__file__).parent/'nana_base_recoil2_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((D/'report.json').read_text('utf8'))
v={'scope':'나나 기본/포스90·91 후보 독립 재추출 정적 미술 검토','candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(D/'report.json'),'actually_viewed':[{'file':n,'sha256':sha(D/n)}for n in('full_090.png','full_091.png','partial_090.png','partial_091.png')],'observations':['90·91의 새 머릿결, 베일, 의상·부츠 명암이 구형보다 세분화되어 있다.','90 사선 권총과 올린 팔,91 수평 정본 권총과 손목은 이 네 정적판에서 새로 분리되어 뜨는 모습이 보이지 않는다.','포스 양다리의 무릎·발목 연결을 확인했고, 상단 베일의 머리 소유 및 하단 베일의 다리 소유 부분판에서 새 고립 조각을 찾지 못했다.','기존9번의 조립 레코드만 빌려 쓴 새 머리이며, 원화 재양자화부터 최종10층까지 동일함은 별도 기술보고로 확인했다.'],'conclusion':'이 네 판 범위에서 새로 확정할 미술 결함을 찾지 못함.','runtime_verified':False,'original_MIPS_executed_here':False,'browser_sequence_executed_here':False,'user_accepted':False,'whole_project_complete':False}
(D/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'technical':sha(D/'report.json'),'visual':sha(D/'visual_review.json')}))
