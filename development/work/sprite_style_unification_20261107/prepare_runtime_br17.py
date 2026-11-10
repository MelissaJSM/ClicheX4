from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='dfd1b9d09e8fad846aebfd51a89aecc46bff98bc6281619bb21abf1c8dbf27fc';new='963ccbd41c71819bec1c594b0314683273972c08d85db3925a75b9599f060ea1'
assert sha(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v17/shibuki_riko.bin')==new
files=[]
for name in ('read_menu','observe','record','play_watch','open_continue','load_fourth','load_base','advance_hq'):
 src=R/f'{name}_br15.py';dest=R/f'{name}_br17.py';assert src.exists() and not dest.exists()
 text=src.read_text('utf8').replace(old,new).replace('br15','br17').replace('checkpoint15','checkpoint17')
 if name=='load_fourth':
  key="assert tuple(slot[i] for i in (0,1,2,3,4,41))==(0,48,2,15,255,0),'Unexpected full-armor record'";assert key in text
  text=text.replace(key,"selected=tuple(slot[i] for i in (0,1,2,3,4,41))\n                    if selected!=(0,48,2,15,255,0):\n                        trace.append({'seconds':now,'record_not_ready':selected,'cursor':t[7]})\n                        last=now;time.sleep(.05);continue")
 dest.write_text(text,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
 p=R/'tools_binding_br17.json'
assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
