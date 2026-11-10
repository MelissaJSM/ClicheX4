"""Observe native pad bits during bounded keyboard input in a verified session."""
import ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
s=Path(sys.argv[1]);r=json.loads((s/'session.local.json').read_text());u,hw=checked_window(r['pid'])
base=int(sys.argv[2]);k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,r['pid'])
def read(a,n):
    b=ctypes.create_string_buffer(n);g=ctypes.c_size_t()
    if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(g)) or g.value!=n:raise OSError('Read failed')
    return b.raw
exe=(Path(r['cue']).parent/'SLUS_005.61').read_bytes()
if read(base+0x233c8,56)!=exe[0x233c8-0x10000+2048:0x233c8-0x10000+2104]:raise ValueError('RAM identity mismatch')
rows=[]
try:
    for sc in (0x35,0x39,0x2d,0x2f):
        if u.GetForegroundWindow()!=hw:raise RuntimeError('Focus changed')
        e=Input();e.type=1;e.data.key=KeyInput(0,sc,8,0,0)
        if u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))!=1:raise OSError('Key down')
        values=[]
        try:
            for _ in range(12):
                time.sleep(.025);values.append(struct.unpack('<3H',read(base+0x166c08,6)))
        finally:
            e.data.key.flags|=2;u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))
        rows.append({'scan':sc,'pad_samples':values});time.sleep(.3)
finally:k.CloseHandle(h)
(s/'input_probe.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
