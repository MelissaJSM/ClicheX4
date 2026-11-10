from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
D=W/'nana_audit/ultimate_ladder_repaint/packed_first7_diagnostic_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=W/'root_review_checkpoint124.json';assert not out.exists()
assert sha(D/'PL02_U.ARC')=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
r={'root_actually_viewed':[{'path':(D/f'readback_{i}.png').relative_to(ROOT).as_posix(),'sha256':sha(D/f'readback_{i}.png')} for i in (1,2,3)],'candidate_sha256':sha(D/'PL02_U.ARC'),'refs':[143,144,145,146,147,154,183],'findings':['얼티밋 전후의 새 머리카락 갈래·얼굴·손발 윤곽이 기존보다 명확하다.','재킷 전과 수영복 후의 의상 구분이 유지되고 새 확정 잘림·몸체 분리를 찾지 못했다.'],'withheld_refs':[148,149,150,151,152,153,155],'limits':['직접 본 것은 재삽입 해독 정지 비교판3장이다. 실제 게임·연속 시청 검증이 아니다.','보류7은 기존 그림이며 전체 사다리 미술·전체 캐릭터 완료가 아니다.'],'runtime_verified':False,'final_user_accepted':False}
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
