from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();new='21696e9bae002ef6c9f95fed683e7cd531fd6cdfc6c0fdae97529c3b28a09636'
assert sha(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v25/shibuki_riko.bin')==new
files=[]
for name,oldver in [('read_menu','br24'),('record','br24'),('open_continue','rn37'),('load_ultimate','rn19'),('advance_hq','rn37')]:
 src=R/f'{name}_{oldver}.py';dest=R/f'{name}_br25.py';assert not dest.exists();s=src.read_text('utf8').replace(oldver,'br25')
 if name in ('read_menu','record'):s=s.replace('45b5e019396f37aaa623e2c23bd4b91ceff344826ef95b6496c41e3d55b91644',new).replace('checkpoint24','checkpoint25')
 elif name!='open_continue':s=s.replace('ver_rin_nana','ver_buki_riko')
 dest.write_text(s,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
 p=R/'tools_binding_br25.json'
assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
