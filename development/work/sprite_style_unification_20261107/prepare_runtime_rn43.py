from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3';new='e751a82bc3d1e228d26389d911ca4b46efa12612dcea69b6c99fdeb3ba3ca637'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v43/rin_nana.bin')==new
files=[]
for name in('read_menu','record','open_continue','load_fourth','advance_hq'):
 src=R/f'{name}_rn41.py';dst=R/f'{name}_rn43.py';s=src.read_text('utf8');assert old in s or 'read_menu_rn41.py' in s;s=s.replace(old,new).replace('rn41','rn43').replace('checkpoint41','checkpoint43')
 if dst.exists():assert dst.read_text('utf8')==s
 else:dst.write_text(s,'utf8')
 files.append({'path':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
p=R/'tools_binding_rn43.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
