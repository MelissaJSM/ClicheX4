from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;H=W/'shibuki_audit'
files=[H/'standing_fire_contacts_review01'/f'{f}_contacts.png' for f in ('base','fourth')]
files += [H/'prepared_standing_fire_base01'/f'{f}_readback_{i:02}.png' for f in ('base','fourth') for i in range(3)]
files += [H/'standing_fire_sequence01'/f'{f}_id{n}_ordered.png' for f,n in [('base',88),('fourth',88),('base',91),('fourth',91)]]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(files)==12 and all(p.is_file() for p in files)
r={'reviewer':'root','candidate_sha256':'4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','actually_viewed_files':[{'path':p.relative_to(W.parents[1]).as_posix(),'sha256':sha(p),'actually_viewed':True} for p in files], 'findings':['기본·포스 85~92의 머리카락, 옷 주름, 외곽선이 대기 기준의 명암과 세부를 이어간다.','85의 한 발이 1픽셀 들리고 반대 지지발은 원래 바닥에 놓이는 차이는 자세 변화로 수용한다. 90/91의 바닥 및 뒷발 폭은 판독 가능한 범위다.','원래 88·91 시간표에 배열한 자세에서 확정된 추가 신체 단절이나 큰 크기 도약을 찾지 못했다.'],'runtime_verified':False,'independent_review':'zero_audit/shibuki_standing_fire8_independent01/report.json','whole_project_complete':False}
p=W/'root_review_checkpoint135.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(sha(p))
