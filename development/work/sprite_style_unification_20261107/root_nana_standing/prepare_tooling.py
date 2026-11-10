from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;W=D.parent;src=W/'root_nana_special/pack_special.py';text=src.read_text('utf8')
for a,b in [('special-pose','standing-pose'),('ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16','f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648'),('refs==(95,96,98,99)','refs==(88,89,97)'),('packed_special01','packed_standing01'),('joint_layers03','joint_layers05'),("f'special {n}'","f'standing {n}'")]:
 assert a in text,a;text=text.replace(a,b)
p=D/'pack_standing.py';assert not p.exists();p.write_text(text,'utf8')
(D/'tooling_provenance.json').write_text(json.dumps({'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scope':'검증된 특수4 패커에서 입력/참조/출력만 분리. 보호된 이전 스크립트를 수정하지 않는다.'},ensure_ascii=False,indent=2)+'\n','utf8')
