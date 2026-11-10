from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='21696e9bae002ef6c9f95fed683e7cd531fd6cdfc6c0fdae97529c3b28a09636';new='13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77'
assert sha(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v28/shibuki_riko.bin')==new
files=[]
for name in('read_menu','record','open_continue','load_ultimate','advance_hq'):
 src=R/f'{name}_br25.py';dst=R/f'{name}_br28.py';assert not dst.exists();s=src.read_text('utf8').replace(old,new).replace('br25','br28').replace('checkpoint25','checkpoint28');dst.write_text(s,'utf8');files.append({'path':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
p=R/'tools_binding_br28.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
