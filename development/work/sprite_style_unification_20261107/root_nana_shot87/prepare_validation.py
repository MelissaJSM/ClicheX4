from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_shot85';candidate='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10';out=D/'packed_settle01'
assert hashlib.sha256((out/'PL00_U.ARC').read_bytes()).hexdigest()==candidate
def save(name,s):
 p=D/name;assert not p.exists();p.write_text(s,'utf8')
s=(S/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_shot','pack_settle'),('packed_shot01','packed_settle01'),('joint_targets03','joint_targets02'),('verify_shot_','verify_settle_'),('layer0_085.png','layer0_087.png'),('range(2)','range(1)')]:assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(S/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('packed_shot01','packed_settle01'),('d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61',candidate),('staging_rn_v35','staging_rn_v36'),('사격85/86','사격 연결87/92'),('85/86은 대기 기준으로 새로 그린 몸체와 고정된 사랑이를 조합합니다. 원래 총구·홍채·발 높이를 보존하며 다른 연결 자세는 부모 그림입니다.','87/92는 사격 후 손을 내리고 준비 자세로 돌아오는 새 몸체입니다. 홍채·전체높이·발 위치를 보존하고,85/86 및88..91은 앞서 검토한 부모 그림입니다.')]:assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s);save('check_sequence_review.py',(S/'check_sequence_review.py').read_text('utf8'))
p=json.loads((S/'shot_components.json').read_text('utf8'));p['resources']['PL00_U.ARC'].update(path=(out/'PL00_U.ARC').relative_to(D.parents[2]).as_posix(),after=candidate);save('settle_components.json',json.dumps(p,indent=2)+'\n')
print(candidate)
