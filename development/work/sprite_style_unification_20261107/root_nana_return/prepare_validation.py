from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_victory';out=D/'packed_return03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();candidate=sha(out/'PL00_U.ARC')
assert candidate=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9'
def save(name,text):
 p=D/name;assert not p.exists();p.write_text(text,'utf8')
s=(S/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_victory','pack_return'),('packed_victory02','packed_return03'),('joint_targets01','joint_targets03'),('verify_victory_','verify_return_'),('layer0_204.png','layer0_156.png')]:assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(S/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('packed_victory02','packed_return03'),('90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239',candidate),('staging_rn_v31','staging_rn_v33'),('(39,)','(3,40)'),('id:39','id:3'),('나나 승리 원순서 검토','나나 귀환 원순서 검토'),('나나 기본·포스 승리4 원표 검토','나나 기본·포스 귀환3 원표 검토'),('실제 EXE 표39','실제 EXE 표3/40'),('204/205/206/207은 새 몸체입니다. 대기 체형과 원래 자세의 발바닥을 맞췄으며81 연결 자세는 부모 그림입니다.','156은 새 몸체이고157은 원래 흰색 안쪽·분홍색 바깥쪽 빛 윤곽,158은 새 몸체의 상승과 기존159 빛을 조합했습니다. 다른 연결 자세는 부모 그림입니다.')]:assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(S/'check_sequence_review.py').read_text('utf8')
for a,b in [('{39:160}','{3:180,40:180}'),('review.reset(39)','review.reset(3)'),('browser_victory.png','browser_return.png')]:assert a in s,a;s=s.replace(a,b)
save('check_sequence_review.py',s)
p=json.loads((S/'victory_components.json').read_text('utf8'));p['resources']['PL00_U.ARC'].update(path=(out/'PL00_U.ARC').relative_to(D.parents[2]).as_posix(),after=candidate);save('return_components.json',json.dumps(p,indent=2)+'\n')
print(candidate)
