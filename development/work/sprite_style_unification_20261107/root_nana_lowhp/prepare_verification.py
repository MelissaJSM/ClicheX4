from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;L=W/'root_nana_ladder'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,replacements in {
 'verify_candidate.py':[("import pack_ladder as pack","import pack_lowhp as pack"),("packed_ladder07","packed_lowhp01"),("joint_layers05","joint_layers03"),("verify_ladder_","verify_lowhp_"),("layer0_143","layer0_120")],
 'prepare_sequence_review.py':[("ladder","low-HP"),("packed_low-HP07","packed_lowhp01"),("509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce","ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16"),("(27,28,29,30,31,32,92,93)","(6,)"),("(27,28,29,31,32,92)","(6,)"),("id:27","id:6"),("사다리14","체력 부족6"),("사다리","체력 부족"),("표27..32/92/93","표6"),("150/155의 총구와 정본 권총 픽셀은 보존했습니다. 표93의 첫96호출은 원표의 기본값이며 실제 충전시간의 동적 덮어쓰기는 재현하지 않습니다.","120..125는 한 몸에 원래 접지 호흡과1픽셀 입을 적용했습니다. 발바닥은 고정입니다.")],
 'check_sequence_review.py':[("counts={27:115,28:125,29:120,30:110,31:75,32:75,92:25,93:110}","counts={6:160}"),("review.reset(31)","review.reset(6)"),("browser_ladder31","browser_lowhp6")]
}.items():
 t=(L/name).read_text('utf8')
 for old,new in replacements:
  assert old in t,(name,old);t=t.replace(old,new)
 if name=='prepare_sequence_review.py':t=t.replace('Original executable frame order with the newly packed low-HP pictures.','Original executable frame order with the newly packed low-HP pictures.')
 p=D/name;assert not p.exists();p.write_text(t,'utf8')
plan=json.loads((L/'ladder_components.json').read_text('utf8'))
plan['resources']['PL00_U.ARC'].update(path=(D/'packed_lowhp01/PL00_U.ARC').relative_to(W.parents[1]).as_posix(),after=sha(D/'packed_lowhp01/PL00_U.ARC'))
p=D/'lowhp_components.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
print('prepared verification')
