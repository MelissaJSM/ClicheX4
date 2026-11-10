from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
new='45b5e019396f37aaa623e2c23bd4b91ceff344826ef95b6496c41e3d55b91644';old='d000e91019a02ec0fee18d6b6a76a2460cd886eb4fe3df7cefe8a51a9fb0c560'
assert sha(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v24/shibuki_riko.bin')==new
files=[]
for name in ('read_menu','record','open_selection'):
 src=R/f'{name}_rn35.py';dest=R/f'{name}_br24.py';assert not dest.exists();s=src.read_text('utf8')
 if name!='open_selection':
  assert '0'*64 in s and old in s;s=s.replace('0'*64,new).replace(old,'0'*64)
 s=s.replace('rn35','br24').replace('RN checkpoint35','BR checkpoint24');dest.write_text(s,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
p=R/'tools_binding_br24.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
print(new)
