from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;D=W/'root_nana_shot85';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[D/'packed_shot01/readback_1.png',D/'joint_targets03/partial_85.png',D/'joint_targets03/partial_86.png']
files += [D/'native_sequence01'/f'{f}_id{n}_ordered.png'for f,n in [('base',88),('fourth',88),('base',91),('fourth',91)]]
assert len(files)==7 and all(p.is_file()for p in files)
r={'reviewer':'root','candidate_sha256':sha(D/'packed_shot01/PL00_U.ARC'),'actually_viewed_files':[{'path':p.relative_to(W.parents[1]).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'findings':['85/86의 새 머리카락·소매·치마 끝과 다리의 윤곽이 승인된 대기/최근 자세의 세부 표현을 따른다.','머리/몸통/팔/다리 부분 아머 판에서 떠 있던 베일 조각이 연결됨을 확인했다. 총의 정본 크기와 손 접점도 유지된다.','원표88/91로 앞뒤 자세를 함께 비교했다. 새85/86에서 추가 확정 잘림·큰 크기 도약을 찾지 못했다. 87/92는 부모 그림이므로 별도 재작업 대상으로 남긴다.'],'runtime_verified':False,'whole_project_complete':False}
p=W/'root_review_checkpoint137.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
