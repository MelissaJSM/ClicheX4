import ctypes,json,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
from src.epsxe_state import framebuffer
pid=44380;checked_window(pid);k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t();return b.raw if k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) and got.value==n else b''
out=Path(__file__).parent/'selection_live';out.mkdir(exist_ok=True)
try:
 for name,base,size in [('ram',22879776,2097152),('vram',91635744,1048576)]:
  raw=read(base,size)
  if len(raw)!=size:raise ValueError('Memory read failed')
  (out/(name+'.bin')).write_bytes(raw)
  if name=='vram':
   for page in [0,256]:framebuffer(raw,0,page).save(out/f'page{page}.png')
 (out/'capture.json').write_text(json.dumps({'pid':pid,'ram_base':22879776,'vram_base':91635744,'keys_sent':False,'process_memory_written':False}))
finally:k.CloseHandle(h)
