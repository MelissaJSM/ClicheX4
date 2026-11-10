from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];old=W/'root_nana_special'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=D/'packed_standing03/PL00_U.ARC'
assert sha(candidate)=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e'
def save(name,text):
 p=D/name;assert not p.exists();p.write_text(text,'utf8')
plan=json.loads((old/'special_components.json').read_text('utf8'))
plan['resources']['PL00_U.ARC'].update(path=candidate.relative_to(ROOT).as_posix(),after=sha(candidate))
save('standing_components.json',json.dumps(plan,indent=2)+'\n')
s=(old/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_special','pack_standing'),('packed_special02','packed_standing03'),('joint_layers04','joint_layers06'),('verify_special_','verify_standing_'),('layer0_095','layer0_088')]:
 assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(old/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('special-pose','standing-pose'),('packed_special02','packed_standing03'),('f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648',sha(candidate)),('staging_rn_v23','staging_rn_v25'),('in (95,96,97,104,105)','in (91,104,105)'),("'id:95'","'id:91'"),('특수 자세 원순서','사격 준비 원순서'),('특수 자세4 원표','사격 준비3 원표'),('표95/96/97/104/105','표91/104/105'),('95/98의 새 그림과96/99의 원래X+1 관계를 보존합니다. 다른 연결 자세는 부모 그림입니다.','89/97의 새 그림과88의 원래X-1 및83개 광선 픽셀을 보존합니다.85 및90..92는 부모 그림이며 다른 연결 자세는 이전 검증본입니다.')]:
 assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(old/'check_sequence_review.py').read_text('utf8')
for a,b in [('counts={95:50,96:35,97:5,104:35,105:85}','counts={91:130,104:35,105:85}'),('review.reset(95)','review.reset(91)'),('browser_special','browser_standing')]:
 assert a in s,a;s=s.replace(a,b)
save('check_sequence_review.py',s)
print('standing validation prepared')
