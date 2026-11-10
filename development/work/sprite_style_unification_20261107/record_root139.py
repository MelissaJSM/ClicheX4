from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;D=W/'shibuki_audit/prepared_selection_standing01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[D/f'copy_{n:02}.png'for n in range(1,9)];assert all(p.is_file()for p in files)
r={'reviewer':'root','candidate_sha256':sha(D/'ST0E_U1.ARC'),'actually_viewed_files':[{'path':p.relative_to(W.parents[1]).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'findings':['선택1..8의 새 그림을 게임85..92와 나란히 비교했다. 머리·얼굴·옷 주름·버스터·발이 새 본체의 세부와 일치한다.','선택화면의 원래 Y 오프셋을 유지하며, 그림을 화면 사본에서 따로 확대하거나 이동하지 않았다. 새 확정 잘림이나 누락 파츠를 찾지 못했다.'],'builder_scope_check':{'path':(W/'selection_standing_v4_checks.json').relative_to(W.parents[1]).as_posix(),'sha256':sha(W/'selection_standing_v4_checks.json')},'runtime_verified':False,'whole_project_complete':False}
p=W/'root_review_checkpoint139.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
