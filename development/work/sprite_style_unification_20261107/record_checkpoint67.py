from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pages=[W/'nana_audit/rising_repaint'/folder/f'comparison_{i}.png' for folder in ('ultimate_air_registered_v1','ultimate_charge_registered_v3') for i in (1,2)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
   'findings':['나나 Ultimate103/104·100/101 전후 의상4판을 열람했다. 새 머릿결과 재킷 앞섶/맨팔 구분, 다리 명암 방향이 기존보다 선명하다. 대기 기준 세부 묘사 방향을 수용한다.'],
   'limits':['정본 권총·손목·공통몸체·발 접점의 최종 정합 전 후보이다.','100/101 높이 차이 보완, 패킹·재추출·실기는 별도이며 최종 수용으로 표시하지 않는다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint67.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
