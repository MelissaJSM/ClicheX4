from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='8a7ee9c47d170c8869f5415e18dc23e920157e28e9d49d7762a7acebc416a01e';new='e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v41/rin_nana.bin')==new
files=[]
for name in('read_menu','record','open_continue','load_fourth','advance_hq'):
 src=R/f'{name}_rn37.py';dst=R/f'{name}_rn41.py';assert not dst.exists();s=src.read_text('utf8').replace(old,new).replace('rn37','rn41').replace('checkpoint37','checkpoint41');dst.write_text(s,'utf8');files.append({'path':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
p=R/'tools_binding_rn41.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
