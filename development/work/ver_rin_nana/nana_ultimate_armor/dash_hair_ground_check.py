import json,sys,subprocess,time
from pathlib import Path
R=Path.cwd();D=R/'work/ver_rin_nana/nana_ultimate_armor';sys.path.insert(0,str(D));import dash_hair_progress as live
saved=json.loads((D/'dash_hair_saved_progress.json').read_text('utf8'));p=live.player();assert all(p[k]==saved[k] for k in('world','hp','armor','ultimate')) and p['animation']==5,'Progress changed, test cancelled';live.k.CloseHandle(live.h)
d=json.loads((R/'work/ver_rin_nana/live_poc/20261104T093150752089Z/discovery.local.json').read_text('utf8'));d['vram_candidates']=[87171104];e=D/'dash_hair_discovery_narrowed.json';e.write_text(json.dumps(d,indent=2),encoding='utf8')
plan=D/'dash_hair_ground_input_v1.json';plan.write_text(json.dumps(dict(bin_sha256=d['modified_bin_sha256'],seconds=3.2,keys=[['right',.05,.42],['dash',.15,.35],['left',1.1,1.65],['dash',1.2,1.55],['fire',1.3,1.46],['right',2.1,2.55],['dash',2.2,2.45]]),indent=2),encoding='utf8')
ready=D/'dash_hair_ground_ready_v1.json';assert not ready.exists()
proc=subprocess.Popen([sys.executable,'scripts/capture_shibuki_armor.py','--project','ver_rin_nana','--evidence',str(e),'--frames',','.join(map(str,range(67,85))),'--seconds','5','--both-directions','--ready-file',str(ready)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 deadline=time.monotonic()+10
 while not ready.exists():
  assert proc.poll() is None and time.monotonic()<deadline,'Capture not ready';time.sleep(.05)
 subprocess.run([sys.executable,'scripts/nana_armor_input_plan.py','--session',live.c['current_session'],'--plan',str(plan)],check=True)
 out,err=proc.communicate(timeout=15);print(out);print(err);assert proc.returncode==0
finally:
 if proc.poll() is None:proc.terminate();proc.communicate()
 subprocess.run([sys.executable,'scripts/emulator_session.py','--project','ver_rin_nana','key','--session',live.c['current_session'],'--scan','0x3d'],check=True)
