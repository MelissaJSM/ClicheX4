from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;D=W/'root_nana_shot87';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[D/'packed_settle01/readback_1.png',D/'joint_targets02/partial_87.png',D/'joint_targets02/partial_92.png']
files += [D/'native_sequence01'/f'{f}_id{n}_ordered.png'for f,n in [('base',88),('fourth',88),('base',91),('fourth',91)]]
assert len(files)==7 and all(p.is_file()for p in files)
r={'reviewer':'root','candidate_sha256':sha(D/'packed_settle01/PL00_U.ARC'),'actually_viewed_files':[{'path':p.relative_to(W.parents[1]).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'findings':['87/92의 머리카락과 옷 주름, 모자와 베일 테두리, 다리의 밝기 구분이 대기 기준과 최근 사격85/86의 세부를 따른다.','부분 아머에서 떠 있던92의 베일 끝1셀은 머리층에 포함돼 연결됐다. 몸체·손·다리 크기에서 새 확정 결함을 찾지 못했다.','원표88의85→86→85→87→92 및91의특수후92 연결을 기본/포스 각각 비교했다. 새로운 자세87/92의 크기나 도트 밀도가 크게 도약하지 않는다.'],'runtime_verified':False,'whole_project_complete':False}
p=W/'root_review_checkpoint138.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
