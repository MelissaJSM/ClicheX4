from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='2701578993e0e5db5f0c6285026622066a49d9d9e080b42270bc329f436a9a79';new='d000e91019a02ec0fee18d6b6a76a2460cd886eb4fe3df7cefe8a51a9fb0c560'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v35/rin_nana.bin')==new
files=[]
for name in ('read_menu','record'):
 src=R/f'{name}_rn30.py';dest=R/f'{name}_rn35.py';assert not dest.exists();s=src.read_text('utf8').replace(old,new).replace('rn30','rn35').replace('checkpoint30','checkpoint35');dest.write_text(s,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
src=R/'open_selection_rn15.py';dest=R/'open_selection_rn35.py';assert not dest.exists();dest.write_text(src.read_text('utf8').replace('read_menu_rn15','read_menu_rn35'),'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
p=R/'tools_binding_rn35.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
print(new)
