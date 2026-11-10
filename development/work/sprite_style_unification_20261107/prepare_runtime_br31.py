from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875';new='ad4f2ceab100098e88977f383d314efd0337379feb70999989eaa53926332516'
assert sha(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v31/shibuki_riko.bin')==new
files=[]
for name in('read_menu','record','open_continue','load_ultimate','advance_hq'):
    src=R/f'{name}_br30.py';dst=R/f'{name}_br31.py';assert not dst.exists();s=src.read_text('utf8').replace(old,new).replace('br30','br31').replace('checkpoint30','checkpoint31');dst.write_text(s,'utf8');files.append({'path':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
p=R/'tools_binding_br31.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
