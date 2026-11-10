from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=W/'nana_audit/rising_repaint/ultimate_costume_pair_probe_v4'
pages=[d/f'comparison_{i}.png' for i in (1,2,3)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
   'findings':['나나 Ultimate 여섯 키의 전후 의상/공통몸체3판을 열람했다. 새 머릿결과 손·다리의 세부 묘사 방향은 대기와 어울리며 101의 불필요한 재킷 끝 잔여가 제거된 공통몸체를 확인했다.'],
   'limits':['231 접지와104 손 가림의 최종확인 및 원화층 패킹 전 후보다.','사용자 최종수용이나 실기 완료가 아니다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint70.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
