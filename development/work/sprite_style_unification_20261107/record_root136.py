from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;D=W/'nana_audit/ultimate_vehicle_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[D/'common_probe_v2'/f'comparison_{n}.png' for n in (1,2)]
files += [D/'packed_vehicle_candidate_v1'/f'readback_{n}.png' for n in range(1,6)]
files += [D/'native_cycle_v1'/f'timeline_{n}.png' for n in (66,68,70,75)]
assert len(files)==11 and all(p.is_file()for p in files)
r={'reviewer':'root','candidate_sha256':sha(D/'packed_vehicle_candidate_v1/PL02_U.ARC'),'actually_viewed_files':[{'path':p.relative_to(W.parents[1]).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'findings':['162/166/170/174의 새 머리·옷·팔다리는 대기 기준의 세부를 유지하며 기존의 뭉친 명암을 정리한다.','재킷 전후 팔·다리의 접점과 신체 실루엣을 비교했다. 이번 판에서 추가 확정 신체 단절을 찾지 못했다.','원래 세 상하 이동 순서66/68/70와 자세전환75에 연결했을 때 동일 몸체가 원래 높이 변화로 이어진다.'],'runtime_verified':False,'whole_project_complete':False}
p=W/'root_review_checkpoint136.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':r['candidate_sha256'],'review':sha(p)}))
