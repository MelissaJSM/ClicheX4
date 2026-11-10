from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=W/'nana_audit/hurt_repaint/first_registered_v1'
pages=[D/f'comparison_{i}.png' for i in (1,2)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
 'findings':['기본/포스106·110의 새 머리결·소매·베일 명암이 대기 기준의 분할 표현에 가까워졌다. 이전 머리/옷 단색 덩어리의 세부를 다시 살렸다.',
 '열린 눈만으로 잘못된 도트라고 판정하지 않는다. 통증·충격 표정은 원래 순서와 지속시간의 피격 전환에서 검토할 사항으로 남긴다.'],
 'limits':['초기 고정 셀 등록안2판이며 공통 몸체/손·효과·게임 패킹과 실제 피격 검증은 아직 수행하지 않았다.'],
 'final_user_accepted':False}
p=W/'root_review_checkpoint77.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
