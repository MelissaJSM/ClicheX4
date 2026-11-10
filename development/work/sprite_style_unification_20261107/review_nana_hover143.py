from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_hover_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arc=D/'packed_hover_candidate_v1/PL02_U.ARC';assert sha(arc)=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
ids=list(range(21,27))+list(range(133,139));images=[D/'native_cycle_v1'/f'timeline_{n}.png'for n in ids]
r={'checkpoint':143,'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in images],'count':12,'observations':['원순서21..26/133..138의12판을 직접 보았다. 앞선45..48 마스크0와 호버221..230 실제마스크15를 구분했다.','새 머리·몸·손·권총·추진 부츠가 전환마다 다른 크기의 캐릭터로 바뀌는 확정 사례나 추가 확정 분리는 찾지 못했다.'],'limitations':['정적 순서판과 미리보기 호출수 검증이며 실제 게임/외부탄환/추진효과의 동적 검증은 아니다.'],'runtime_verified':False,'whole_project_complete':False}
p=W/'root_review_checkpoint143.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
