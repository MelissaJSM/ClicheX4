from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_return';out=D/'packed_shot01'
candidate=hashlib.sha256((out/'PL00_U.ARC').read_bytes()).hexdigest()
assert candidate=='d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61'
def save(name,text):
 p=D/name;assert not p.exists();p.write_text(text,encoding='utf8')
s=(S/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_return','pack_shot'),('packed_return03','packed_shot01'),('verify_return_','verify_shot_'),('layer0_156.png','layer0_085.png')]:
 assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(S/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('packed_return03','packed_shot01'),('6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9',candidate),('staging_rn_v33','staging_rn_v35'),('(3,40)','(88,89,90,91,94)'),('id:3','id:88'),('나나 귀환 원순서 검토','나나 사격 원순서 검토'),('나나 기본·포스 귀환3 원표 검토','나나 기본·포스 사격85/86 원표 검토'),('실제 EXE 표3/40','실제 EXE 표88/89/90/91/94'),('156은 새 몸체이고157은 원래 흰색 안쪽·분홍색 바깥쪽 빛 윤곽,158은 새 몸체의 상승과 기존159 빛을 조합했습니다. 다른 연결 자세는 부모 그림입니다.','85/86은 대기 기준으로 새로 그린 몸체와 고정된 사랑이를 조합합니다. 원래 총구·홍채·발 높이를 보존하며 다른 연결 자세는 부모 그림입니다.')]:
 assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(S/'check_sequence_review.py').read_text('utf8')
for a,b in [('{3:180,40:180}','{88:100,89:100,90:100,91:180,94:140}'),('review.reset(3)','review.reset(91)'),('browser_return.png','browser_shot.png')]:
 assert a in s,a;s=s.replace(a,b)
save('check_sequence_review.py',s)
p=json.loads((S/'return_components.json').read_text('utf8'));p['resources']['PL00_U.ARC'].update(path=(out/'PL00_U.ARC').relative_to(D.parents[2]).as_posix(),after=candidate)
save('shot_components.json',json.dumps(p,indent=2)+'\n')
print(candidate)
