from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='2701578993e0e5db5f0c6285026622066a49d9d9e080b42270bc329f436a9a79';new='8a7ee9c47d170c8869f5415e18dc23e920157e28e9d49d7762a7acebc416a01e'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v37/rin_nana.bin')==new
files=[]
for name in ('read_menu','record','open_continue','load_fourth','advance_hq'):
 src=R/f'{name}_rn30.py';dest=R/f'{name}_rn37.py';assert not dest.exists();s=src.read_text('utf8').replace(old,new).replace('rn30','rn37').replace('checkpoint30','checkpoint37');dest.write_text(s,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
p=R/'tools_binding_rn37.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
