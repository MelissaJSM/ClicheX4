from pathlib import Path
import json, hashlib
D=Path(__file__).resolve().parent
S=D.parent/'root_nana_recoil'
candidate='9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91'
def save(name,text):
 p=D/name
 assert not p.exists(),p
 p.write_text(text,'utf8')
s=(S/'verify_candidate.py').read_text('utf8')
for a,b in [('pack_recoil','pack_arrival'),('packed_recoil03','packed_arrival01'),('joint_layers02','joint_targets01'),('verify_recoil_','verify_arrival_'),('layer0_090.png','layer0_133.png')]:
 assert a in s,a
 s=s.replace(a,b)
save('verify_candidate.py',s)
s=(S/'prepare_sequence_review.py').read_text('utf8')
for a,b in [('packed_recoil03','packed_arrival01'),('ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4',candidate),('staging_rn_v27','staging_rn_v28'),('(91,)','(2,)'),('id:91','id:2'),('나나 사격 후속 원순서 검토','나나 등장 원순서 검토'),('나나 기본·포스 사격 후속2 원표 검토','나나 기본·포스 등장7 원표 검토'),('실제 EXE 표91','실제 EXE 표2'),('90/91의 새 머릿결·옷 주름을 적용합니다.91의 권총은85와 동일한8px 모듈이고 다른 연결 자세는 부모 그림입니다.','133/135/136/137은 새 몸체이며130/131/134는 원래 빛 효과와 새 실루엣을 조합했습니다.132와 다른 연결 자세는 부모 그림입니다.')]:
 assert a in s,a
 s=s.replace(a,b)
save('prepare_sequence_review.py',s)
s=(S/'check_sequence_review.py').read_text('utf8')
for a,b in [('{91:130}','{2:200}'),('review.reset(91)','review.reset(2)'),('browser_recoil.png','browser_arrival.png')]:
 assert a in s,a
 s=s.replace(a,b)
save('check_sequence_review.py',s)
p=json.loads((S/'recoil_components.json').read_text('utf8'))
p['resources']['PL00_U.ARC'].update(path=(D/'packed_arrival01/PL00_U.ARC').relative_to(D.parents[2]).as_posix(),after=candidate)
save('arrival_components.json',json.dumps(p,indent=2)+'\n')
print('arrival validation scripts prepared')
