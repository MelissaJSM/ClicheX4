from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77';new='753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252'
assert sha(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.bin')==new
files=[]
for name in('read_menu','record','open_continue','load_ultimate','advance_hq'):
    src=R/f'{name}_br28.py';dst=R/f'{name}_br29.py';assert not dst.exists();s=src.read_text('utf8').replace(old,new).replace('br28','br29').replace('checkpoint28','checkpoint29');dst.write_text(s,'utf8');files.append({'path':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
p=R/'tools_binding_br29.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
