"""Read HP and stop ordinary gameplay at low health; never write game memory."""
from pathlib import Path
import sys,json,ctypes,time,struct
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
D=Path(__file__).parent;S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T074619623607Z'
record=json.loads((S/'session.local.json').read_text());prior=json.loads((ROOT/'work/ver_buki_riko/live_poc/20261024T074944605716Z/verification.local.json').read_text())
if prior['pid']!=record['pid'] or prior['modified_bin_sha256']!=record['bin_sha256']:raise ValueError('Session mismatch')
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
def tap(scan):send(scan,False,True);time.sleep(.12);send(scan,False,False)
def player():
 b=ctypes.create_string_buffer(0xe4);n=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,prior['ram_host_address']+0x1418c8,b,0xe4,ctypes.byref(n)) or n.value!=0xe4:raise OSError('Short read')
 return b.raw
reached=False
try:
 if player()[2]!=1:raise ValueError('Expected Zero')
 tap(0x2f);time.sleep(.8);send(0x4d,True,True);time.sleep(.55);send(0x4d,True,False)
 while time.monotonic()-start<50:
  p=player();row=[p[0x5c],p[0x17],p[0x47],*[struct.unpack_from('<i',p,o)[0]/65536 for o in (8,12)]]
  if not trace or trace[-1][1:]!=row:trace.append([round(time.monotonic()-start,4),*row])
  if 0<p[0x5c]<=8:reached=True;break
  if not p[0x5c]:break
  time.sleep(.02)
 tap(0x2f)
finally:
 for scan,ext in list(held):send(scan,ext,False)
 k.CloseHandle(h)
 (D/'reach_low_hp.json').write_text(json.dumps({'reached':reached,'rows':trace,'input_events':inputs,'process_memory_written':False},indent=2))
print(json.dumps({'reached':reached,'last':trace[-1] if trace else None}))
