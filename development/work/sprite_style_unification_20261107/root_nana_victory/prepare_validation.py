from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_arrival';out=D/'packed_victory02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=sha(out/'PL00_U.ARC')
def save(name,text):
 p=D/name;assert not p.exists(),p;p.write_text(text,'utf8')
s=(S/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_arrival','pack_victory'),('packed_arrival01','packed_victory02'),('verify_arrival_','verify_victory_'),('layer0_133.png','layer0_204.png')]:
 assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(S/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('packed_arrival01','packed_victory02'),('9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91',candidate),('staging_rn_v28','staging_rn_v31'),('(2,)','(39,)'),('id:2','id:39'),('나나 등장 원순서 검토','나나 승리 원순서 검토'),('나나 기본·포스 등장7 원표 검토','나나 기본·포스 승리4 원표 검토'),('실제 EXE 표2','실제 EXE 표39'),('133/135/136/137은 새 몸체이며130/131/134는 원래 빛 효과와 새 실루엣을 조합했습니다.132와 다른 연결 자세는 부모 그림입니다.','204/205/206/207은 새 몸체입니다. 대기 체형과 원래 자세의 발바닥을 맞췄으며81 연결 자세는 부모 그림입니다.')]:
 assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(S/'check_sequence_review.py').read_text('utf8')
for a,b in [('{2:200}','{39:160}'),('review.reset(2)','review.reset(39)'),('browser_arrival.png','browser_victory.png')]:
 assert a in s,a;s=s.replace(a,b)
save('check_sequence_review.py',s)
p=json.loads((S/'arrival_components.json').read_text('utf8'))
p['resources']['PL00_U.ARC'].update(path=(out/'PL00_U.ARC').relative_to(D.parents[2]).as_posix(),after=candidate)
save('victory_components.json',json.dumps(p,indent=2)+'\n')
print(candidate)
