"""Bounded dialogue advance for the authenticated red-Rin v15 test session."""
from pathlib import Path
import json, sys, subprocess, time
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261107T132706808542Z'
rec=json.loads((session/'session.local.json').read_text('utf8'))
check=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).with_name('read_menu_rn15.py')),'--session',str(session),'--pid',str(rec['pid']),'--ram-base','17374752'],text=True,encoding='utf8'))
assert check['passed'] and check['engine']['character']==1 and check['engine']['ultimate_black']==1
dest=Path(__file__).with_name('red_rin15_intro_advance.json'); assert not dest.exists()
p=ReadOnlyProcess(rec);trace=[]
try:
 for i in range(20):
  e=p.read(17374752+0x1721c0,100)
  trace.append({'state':e[0],'substate':e[1],'character':e[0x43],'black':e[0x37]})
  if e[0]!=3: break
  assert e[0x43]==1 and e[0x37]==1
  cmd=[sys.executable,'scripts/korean_runtime_control.py','--project','ver_rin_nana','key','--scan','0x2d','--session',str(session)]
  r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=5)
  trace[-1]['key_result']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
  if r.returncode: break
  time.sleep(.65)
finally:
 p.close()
 dest.write_text(json.dumps({'trace':trace,'memory_written':False,'save_keys_sent':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'observations':len(trace),'last':trace[-1]}))
