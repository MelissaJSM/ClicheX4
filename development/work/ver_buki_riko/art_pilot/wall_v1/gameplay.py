from pathlib import Path
import sys,json,time,ctypes,subprocess
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
from scripts.project import write_json
from datetime import datetime,timezone
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T012142905863Z'
pid=json.loads((S/'session.local.json').read_text())['pid']
user,window=checked_window(pid);user.ShowWindowAsync(window,9);user.SetForegroundWindow(window);time.sleep(.15)
action=sys.argv[1];plans={
 'right_jump':[(0,1.98,0x4d,True),(.04,.7,0x2c,False),(1,1.7,0x2c,False),(.1,.2,0x1f,False),(.45,.55,0x1f,False),(1.05,1.15,0x1f,False),(1.45,1.55,0x1f,False)],
 'right_dash':[(0,1.8,0x4d,True),(.04,1.7,0x2d,False),(.1,.2,0x1f,False),(.45,.55,0x1f,False),(1,1.1,0x1f,False)],
 'wall_right':[(0,1.8,0x4d,True),(.02,.45,0x2c,False),(.85,1.05,0x2c,False),(1.35,1.55,0x2c,False)],
 'wall_left':[(0,1.8,0x4b,True),(.02,.45,0x2c,False),(.85,1.05,0x2c,False),(1.35,1.55,0x2c,False)]}
events=plans[action];held=set();trace=[];start=time.monotonic()
def send(scan,extended,down):
 event=Input();event.type=1;event.data.key=KeyInput(0,scan,8|int(extended)|(0 if down else 2),0,0)
 if user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))!=1:raise OSError('Input failed')
 trace.append([round(time.monotonic()-start,4),scan,extended,down])
try:
 while time.monotonic()-start<2:
  if user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed')
  elapsed=time.monotonic()-start;wanted={(s,e) for t0,t1,s,e in events if t0<=elapsed<t1}
  for key in held-wanted:send(*key,False)
  for key in wanted-held:send(*key,True)
  held=wanted;time.sleep(.005)
finally:
 for key in held:send(*key,False)
 write_json(S/('input_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.local.json'),{'action':action,'events':trace,'game_memory_written':False})
subprocess.run([sys.executable,str(ROOT/'scripts/emulator_session.py'),'capture','--session',str(S)],check=True)
