from pathlib import Path
import sys, json, re, hashlib,struct
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from src.steam_arc import SteamArc
W=R/'work/steam_port_20261109';O=W/'original'
def sha(b):return hashlib.sha256(b).hexdigest()
def sbkr(b):
 n=struct.unpack_from('<I',b,12)[0];rows=[]
 for m in re.finditer(rb'X4\\sound[^\x00]+\x00',b):
  off=m.end();end=off+84
  rows.append({'name':m.group()[:-1].decode(),'path_offset':m.start(),'record_offset':off,'bytes':b[off:end].hex()})
 if len(rows)!=n:raise ValueError((n,len(rows)))
 return rows
rows=[]
for p in sorted((O/'nativeDX10/X4/romPC').glob('*.arc')):
 a=SteamArc(p.read_bytes());sounds=[]
 for e in a.entries:
  if '\\sound\\' not in e.name:continue
  row={'name':e.name,'kind':e.kind,'magic':e.payload[:4].decode(errors='replace'),'size':len(e.payload),'sha256':sha(e.payload)}
  if e.payload[:4]==b'SBKR':row['tones']=sbkr(e.payload)
  if e.payload[:4]==b'SRQR':
   b=e.payload;n=struct.unpack_from('<I',b,8)[0];row['events']=[{'id':struct.unpack_from('<H',b,48+128*i)[0],'first_bytes':b[48+128*i:48+128*i+32].hex()} for i in range(n)]
  sounds.append(row)
 if sounds:rows.append({'arc':p.name,'sounds':sounds})
(W/'audio').mkdir(exist_ok=True)
(W/'audio/inventory.json').write_text(json.dumps(rows,indent=2)+'\n')
print([(r['arc'],len(r['sounds'])) for r in rows])
for name in ['pl00.arc','pl01.arc','pl02.arc','onpare1_eng.arc','st1_1_1_eng.arc']:
 found=[r for r in rows if r['arc']==name]
 if found:
  print(name,[(r['name'],r.get('events',[])) for r in found[0]['sounds'] if r['magic']=='SRQR'])
