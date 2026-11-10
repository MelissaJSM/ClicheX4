from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];old=W/'root_nana_standing'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=D/'packed_recoil03/PL00_U.ARC';assert sha(candidate)=='ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4'
def save(name,text):
 p=D/name;assert not p.exists();p.write_text(text,'utf8')
plan=json.loads((old/'standing_components.json').read_text('utf8'));plan['resources']['PL00_U.ARC'].update(path=candidate.relative_to(ROOT).as_posix(),after=sha(candidate));save('recoil_components.json',json.dumps(plan,indent=2)+'\n')
s=(old/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_standing','pack_recoil'),('packed_standing03','packed_recoil03'),('joint_layers06','joint_layers02'),('verify_standing_','verify_recoil_'),('layer0_088','layer0_090')]:
 assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(old/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('standing-pose','recoil-pose'),('packed_standing03','packed_recoil03'),('87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e',sha(candidate)),('staging_rn_v25','staging_rn_v27'),('in (91,104,105)','in (91,)'),('사격 준비 원순서','사격 후속 원순서'),('사격 준비3 원표','사격 후속2 원표'),('표91/104/105','표91'),('89/97의 새 그림과88의 원래X-1 및83개 광선 픽셀을 보존합니다.85 및90..92는 부모 그림이며 다른 연결 자세는 이전 검증본입니다.','90/91의 새 머릿결·옷 주름을 적용합니다.91의 권총은85와 동일한8px 모듈이고 다른 연결 자세는 부모 그림입니다.')]:
 assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(old/'check_sequence_review.py').read_text('utf8')
for a,b in [('counts={91:130,104:35,105:85}','counts={91:130}'),('browser_standing','browser_recoil')]:
 assert a in s,a;s=s.replace(a,b)
save('check_sequence_review.py',s)
print('recoil validations prepared')
