from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='9ea0cc759b2884d026a305b45ce21a2d97f78aa2682f27b6349b864039784f58';new='2701578993e0e5db5f0c6285026622066a49d9d9e080b42270bc329f436a9a79'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v30/rin_nana.bin')==new
files=[]
for name in ('read_menu','observe','record','play_watch','open_continue','load_fourth','load_base','advance_hq'):
 src=R/f'{name}_rn28.py';dest=R/f'{name}_rn30.py';assert src.exists()and not dest.exists()
 t=src.read_text('utf8').replace(old,new).replace('rn28','rn30').replace('checkpoint28','checkpoint30')
 dest.write_text(t,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
p=R/'tools_binding_rn30.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
print(new)
