from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];old=W/'root_nana_lowhp';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=D/'packed_special02/PL00_U.ARC';assert sha(candidate)=='f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648'
plan=json.loads((old/'lowhp_components.json').read_text('utf8'));plan['resources']['PL00_U.ARC'].update(path=candidate.relative_to(ROOT).as_posix(),after=sha(candidate))
p=D/'special_components.json';assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n','utf8')
p=D/'verify_candidate.py';v=p.read_text('utf8').replace('packed_special01','packed_special02').replace('joint_layers03','joint_layers04');p.write_text(v,'utf8')
s=(old/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('low-HP','special-pose'),('packed_lowhp01','packed_special02'),('ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16',sha(candidate)),('staging_rn_v19','staging_rn_v23'),('in (6,)','in (95,96,97,104,105)'),("'id:6'","'id:95'"),('나나 체력 부족 원순서 검토','나나 특수 자세 원순서 검토'),('나나 기본·포스 체력 부족6 원표 검토','나나 기본·포스 특수 자세4 원표 검토'),('실제 EXE 표6의 순서','실제 EXE 표95/96/97/104/105의 순서'),('체력 부족 물리 이동','호버/특수 기술 물리 이동'),('120..125는 한 몸에 원래 접지 호흡과1픽셀 입을 적용했습니다. 발바닥은 고정입니다.','95/98의 새 그림과96/99의 원래X+1 관계를 보존합니다. 다른 연결 자세는 부모 그림입니다.')]:
 assert a in s,a;s=s.replace(a,b)
p=D/'prepare_sequence_review.py';assert not p.exists();p.write_text(s,'utf8')
s=(old/'check_sequence_review.py').read_text('utf8').replace('counts={6:160}','counts={95:50,96:35,97:5,104:35,105:85}').replace('(aid in (92,93))','True').replace('review.reset(6)','review.reset(95)').replace('browser_lowhp6.png','browser_special.png')
p=D/'check_sequence_review.py';assert not p.exists();p.write_text(s,'utf8')
print('prepared native, sequence and reproduction checks')
