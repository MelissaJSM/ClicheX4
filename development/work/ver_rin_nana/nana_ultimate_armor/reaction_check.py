import json,sys,subprocess,time
from pathlib import Path
R=Path.cwd();D=R/'work/ver_rin_nana/nana_ultimate_armor';sys.path.insert(0,str(D));import reaction_progress as live
saved=json.loads((D/'reaction_saved_progress.json').read_text('utf8'));p=live.player();assert all(p[k]==saved[k] for k in('world','hp','armor','ultimate')) and p['animation']==5,'Progress changed, test cancelled';live.k.CloseHandle(live.h)
d=json.loads((R/'work/ver_rin_nana/live_poc/20261104T095737793675Z/discovery.local.json').read_text('utf8'));v=json.loads((R/'work/ver_rin_nana/armor_capture/20261104T095746409678Z/verification.local.json').read_text('utf8'));d['vram_candidates']=sorted({q['vram_host_address']for q in v['results']});e=D/'reaction_discovery_narrowed.json';e.write_text(json.dumps(d,indent=2),encoding='utf8')
plan=D/'reaction_input_v1.json';plan.write_text(json.dumps(dict(bin_sha256=d['modified_bin_sha256'],seconds=7.2,keys=[['right',.05,1.0]]),indent=2),encoding='utf8')
ready=D/'reaction_ready_v1.json';assert not ready.exists()
proc=subprocess.Popen([sys.executable,'scripts/capture_shibuki_armor.py','--project','ver_rin_nana','--evidence',str(e),'--frames','106,107,108,110,111,120,121,122,123,124,125,233,234,235,236','--seconds','8','--both-directions','--ready-file',str(ready)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 deadline=time.monotonic()+10
 while not ready.exists():
  assert proc.poll() is None and time.monotonic()<deadline,'Capture not ready';time.sleep(.05)
 subprocess.run([sys.executable,'scripts/nana_armor_input_plan.py','--session',live.c['current_session'],'--plan',str(plan)],check=True)
 out,err=proc.communicate(timeout=15);print(out);print(err);assert proc.returncode==0
finally:
 if proc.poll() is None:proc.terminate();proc.communicate()
 subprocess.run([sys.executable,'scripts/emulator_session.py','--project','ver_rin_nana','key','--session',live.c['current_session'],'--scan','0x3d'],check=True)
