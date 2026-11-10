from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/rising_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'ultimate_native_cycle_v1'/f'timeline_{i}.png' for i in range(99,104)]
paths += [D/'ultimate_effect_contact_v1'/f'comparison_{i}.png' for i in (1,2)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
   'findings':['원래 순서를 펼친5판에서 차지 시작의몸숙임→상승→내려오는자세가 이어지고 두의상에서 새디테일을 유지하는 것을 확인했다.',
               '양방향104/232의 권총·원초기불꽃 점유 합성2판에서 총열과효과 시작이 연결되는 방향을 확인했다.'],
   'limits':['2차원 정적 순서판이며 실제 속도로 전체 애니메이션을 보거나 새 게임을 실행한 증거가 아니다.',
             '청록색 효과는 점유 확인용 합성이다. 실제불꽃팔레트·혼합·전 시간표 검증을 주장하지 않는다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint74.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
