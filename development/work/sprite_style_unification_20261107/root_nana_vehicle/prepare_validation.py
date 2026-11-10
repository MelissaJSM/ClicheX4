from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_return';out=D/'packed_vehicle03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();candidate=sha(out/'PL00_U.ARC')
assert candidate=='29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db'
def save(name,text):
 p=D/name;assert not p.exists();p.write_text(text,'utf8')
s=(S/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_return','pack_vehicle'),('packed_return03','packed_vehicle03'),('verify_return_','verify_vehicle_'),('layer0_156.png','layer0_162.png')]:assert a in s,a;s=s.replace(a,b)
save('verify_candidate.py',s)
s=(S/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('packed_return03','packed_vehicle03'),('6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9',candidate),('staging_rn_v33','staging_rn_v34'),('(3,40)','tuple(range(65,77))'),('id:3','id:65'),('나나 귀환 원순서 검토','나나 라이드 체이서 원순서 검토'),('나나 기본·포스 귀환3 원표 검토','나나 기본·포스 차량13 원표 검토'),('실제 EXE 표3/40','실제 EXE 표65..76'),('156은 새 몸체이고157은 원래 흰색 안쪽·분홍색 바깥쪽 빛 윤곽,158은 새 몸체의 상승과 기존159 빛을 조합했습니다. 다른 연결 자세는 부모 그림입니다.','162/166/170/174는 새 몸체이며 나머지9참조는 확인된 원래 상하 위치 파생입니다. 차량 자체·물리이동과 접점은 이 단독 표시 시뮬레이션에 포함되지 않습니다.')]:assert a in s,a;s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(S/'check_sequence_review.py').read_text('utf8')
for a,b in [('{3:180,40:180}','{i:80 for i in range(65,77)}'),('review.reset(3)','review.reset(66)'),('browser_return.png','browser_vehicle.png')]:assert a in s,a;s=s.replace(a,b)
save('check_sequence_review.py',s)
p=json.loads((S/'return_components.json').read_text('utf8'));p['resources']['PL00_U.ARC'].update(path=(out/'PL00_U.ARC').relative_to(D.parents[2]).as_posix(),after=candidate);save('vehicle_components.json',json.dumps(p,indent=2)+'\n')
print(candidate)
