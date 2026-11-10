from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=W/'nana_audit/rising_repaint/native_cycle_v1'
pages=[d/f'timeline_{i}.png' for i in range(99,104)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
   'findings':['나나 라이징 기본/포스 원래 순서99..103의 정적 연속판5개를 열람했다. 도약/회전 시 머리와 의상 명암의 통일 방향을 유지하며 추가 확정 단절은 찾지 못했다.'],
   'limits':['타임라인 정적 열람이며 실제 실시간 게임 플레이 검증이 아니다.','한 프레임의 원래 반복 유지와 자세별 원점 이동은 게임 동작으로 구분한다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint66.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
