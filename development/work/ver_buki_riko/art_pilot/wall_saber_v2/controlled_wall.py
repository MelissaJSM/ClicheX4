"""Time normal jump/saber input from observed wall contact, without RAM writes."""
from pathlib import Path
import sys,json,ctypes,time,struct,subprocess
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
D=Path(__file__).parent;S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T074619623607Z';B=ROOT/'out/ver_buki_riko/riko_bank1_20261024T074353134413Z'
BASE=ROOT/'work/ver_buki_riko/live_poc/20261024T074944605716Z/verification.local.json'
direction=sys.argv[1];name=sys.argv[2];record=json.loads((S/'session.local.json').read_text());prior=json.loads(BASE.read_text())
if direction not in ('right','left') or prior['pid']!=record['pid'] or prior['modified_bin_sha256']!=record['bin_sha256']:raise ValueError('Session mismatch')
user,window=checked_window(prior['pid']);user.ShowWindowAsync(window,9);user.SetForegroundWindow(window);time.sleep(.2)
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,prior['pid']);held=set();trace=[];inputs=[];start=time.monotonic()
def send(scan,ext,down):
 if down and user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed')
 e=Input();e.type=1;e.data.key=KeyInput(0,scan,8|int(ext)|(0 if down else 2),0,0)
 if user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))!=1:raise OSError('Input failed')
 inputs.append([round(time.monotonic()-start,4),scan,ext,down])
 if down:held.add((scan,ext))
 else:held.discard((scan,ext))
def tap(scan,duration=.12):send(scan,False,True);time.sleep(duration);send(scan,False,False)
def player():
 b=ctypes.create_string_buffer(0xe4);n=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,prior['ram_host_address']+0x1418c8,b,0xe4,ctypes.byref(n)) or n.value!=0xe4:raise OSError('Short read')
 return b.raw
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
logfile=D/(name+'_runtime.log');log=logfile.open('x',encoding='utf8')
observer=subprocess.Popen([sys.executable,'scripts/capture_jump_cycle.py','--build',str(B),'--baseline',str(BASE),'--wall-saber','--observe'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,startupinfo=startup)
last_jump=-10;last_attack=-10;attack_count=0;prepare_left=direction=='left'
try:
 if player()[2]!=1:raise ValueError('Expected Zero')
 time.sleep(.6)
 if '--active' not in sys.argv:tap(0x2f);time.sleep(.6)
 while time.monotonic()-start<12:
  if user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed')
  p=player();now=time.monotonic()-start;x,y=[struct.unpack_from('<i',p,o)[0]/65536 for o in (8,12)];aid=p[0x17]
  row=[p[0x5c],aid,p[0x47],x,y,p[0x4a],p[0x89]]
  if not trace or trace[-1][1:]!=row:trace.append([round(now,4),*row])
  if not p[0x5c]:break
  if prepare_left and x>=1810:prepare_left=False
  scan=0x4d if direction=='right' or prepare_left else 0x4b
  for key in list(held):
   if key!=(scan,True):send(*key,False)
  if (scan,True) not in held:send(scan,True,True)
  near=(x>1620 if direction=='right' else not prepare_left and x<1840)
  if near and p[0x89]&8 and now-last_jump>1.2:
   tap(0x2c,.35);last_jump=now
  elif p[0x4a] and aid in (13,15) and y<380 and now-last_attack>.8:
   tap(0x1f);last_attack=now;attack_count+=1
  time.sleep(.008)
 for scan,ext in list(held):send(scan,ext,False)
 tap(0x2f)
finally:
 for scan,ext in list(held):send(scan,ext,False)
 k.CloseHandle(h)
 (D/(name+'_inputs.json')).write_text(json.dumps({'direction':direction,'attacks':attack_count,'rows':trace,'input_events':inputs,'process_memory_written':False},indent=2))
status=observer.wait(timeout=60);log.close();print(json.dumps({'attacks':attack_count,'last':trace[-1] if trace else None}));print(logfile.read_text('utf8'))
if status:raise SystemExit(status)
