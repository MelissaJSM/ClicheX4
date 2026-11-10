"""실제 열람한 Ultimate85..92 네 비교판의 미술 의견을 별도로 기록한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];O=D/'shibuki_ultimate_fire8_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((O/'report.json').read_text('utf8'))
for q in r['readback_sheets']:assert sha(ROOT/q['path'])==q['sha256']
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),'actually_viewed_sheets':r['readback_sheets'],'observations':['85/86은 새 머리의 앞머리·안경과 재킷 커프/밑단이 이전 단순 면보다 구분되며, 양폼의 손~총과 신발 연결에 새로 확정할 단절은 보이지 않는다.','87/92는 별도 회복 자세를 유지하며 새 머리/상체와 하체가 이어진다. 맨팔 폼에 명백한 긴 흰 소매 잔류는 발견하지 못했다.','88의 푸른 원효과가 머리 앞을 가리는 모양과 폭은 유지된다. 이 그림은 새89 X−1로 만든 파생이며 옛몸체 동일성을 뜻하지 않는다.','90의 높이 든 맨팔은 어깨~팔꿈치가 이어지고, 앞서 검토한 보라 외곽2셀 때문에 떨어진 점이나 추가 팔이 생긴 모습은 없다. 91의 수평 팔과 총 연결도 현재 네 판에서 새 확정 결함을 찾지 못했다.'],'limits':['정적 재추출 네 판만 실제 열람했다. 연속 게임 모션/실제 발사점/전체실기는 이번 미술 의견에 포함하지 않았다.','검사 통과는 이 고정 후보의 등록·저장 보존 근거이며 전체폼/모션 완성 또는 사용자 최종수용이 아니다.'],'new_art_requiring_change_found':False,'runtime_verified':False}
p=O/'visual_review.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
lock={'reader':{'path':(D/'verify_shibuki_ultimate_fire8_independent.py').relative_to(ROOT).as_posix(),'sha256':sha(D/'verify_shibuki_ultimate_fire8_independent.py')},'read_only_core':{'path':(D/'verify_shibuki_ultimate_hurt13_independent.py').relative_to(ROOT).as_posix(),'sha256':sha(D/'verify_shibuki_ultimate_hurt13_independent.py')},'producer_input_hashes':r['inputs'],'outputs':{q.name:sha(q)for q in O.iterdir()if q.is_file()}}
f=O/'READER_LOCK.json';assert not f.exists();f.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'visual_sha256':sha(p),'lock_sha256':sha(f)}))
