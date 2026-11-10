"""Bounded, ordinary key input selected from authenticated read-only menu state."""
import json, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess

session=Path('work/ver_rin_nana/emulator_sessions/20261107T064815899941Z')
base=17374752
command=[sys.executable,'work/sprite_style_unification_20261107/runtime/read_menu9.py','--session',str(session),'--pid','49168','--ram-base',str(base)]
check=json.loads(subprocess.check_output(command,text=True,encoding='utf8'))
assert check['passed']
record=json.loads((session/'session.local.json').read_text('utf8'))
proc=ReadOnlyProcess(record)
events=[];start=time.monotonic();previous=None;last_action=-10
try:
 while time.monotonic()-start<35:
  g=proc.read(base+0x173c70,16);t=proc.read(base+0x141bd8,12)
  state=(g[0],g[1],g[2],g[13],t[4])
  now=time.monotonic()-start
  if state!=previous:events.append({'seconds':round(now,3),'state':state});previous=state
  if g[0] in (7,9):break
  scan=None;extended=False
  if now-last_action>1.2:
   if (g[0]==1 and g[13]==0) or (g[0] in (0,2,3) and g[13]==0):scan='0x35'
   elif g[0]==1 and g[13]==1 and g[1]<12:scan='0x35'
   elif g[0]==6 and g[1]==1 and t[4]==0:
    if g[2]==0:scan='0x50';extended=True
    elif g[2]==1:scan='0x2d'
    else:break
  if scan:
   cmd=[sys.executable,'scripts/korean_runtime_control.py','--project','ver_rin_nana','key','--scan',scan,'--session',str(session)]
   if extended:cmd.append('--extended')
   r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=5)
   events.append({'seconds':round(now,3),'scan':scan,'extended':extended,'exit':r.returncode,'output':r.stdout,'error':r.stderr})
   if r.returncode:break
   last_action=time.monotonic()-start
  time.sleep(.03)
finally:proc.close()
out=Path('work/sprite_style_unification_20261107/runtime/nana_title_navigation9.json')
out.write_text(json.dumps({'session':str(session),'events':events,'memory_written':False,'save_keys_sent':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'trace':str(out),'final_state':previous,'events':len(events)}))
