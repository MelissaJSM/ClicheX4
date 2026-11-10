from pathlib import Path
import json,hashlib
O=Path(__file__).parent;ROOT=O.parents[3];D=O.parent.parent/'nana_audit/ultimate_run_repaint/packed_run_candidate_v1'
q=json.loads((O/'report.json').read_text('utf8'));assert q['passed'] and q['candidate_sha256']=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
q['visual_review_pending']=False
q['visual_review']={'actually_opened':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [D/f'readback_{i}.png'for i in range(1,5)]],'observations':'최종 재독출4판, 이동/사격32×전후 두 의상 전체를 실제 열람했다. 새 머리·커프·재킷 주름과 맨팔 명암이 이어지며, 이 판 범위에서 새 팔꿈치/손목 단절이나 추가 팔다리를 발견하지 못했다. 4/8의 팔이 상대적으로 가는 점은 정적 그림만으로 전 동작 자연스러움을 확정하지 않으며, 원표 영상/게임실기는 이 감사에서 수행하지 않았다.','runtime_verified':False,'user_accepted':False}
(O/'report.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8')
print(hashlib.sha256((O/'report.json').read_bytes()).hexdigest())
