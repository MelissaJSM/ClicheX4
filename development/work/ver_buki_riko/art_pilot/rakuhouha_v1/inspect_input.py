from pathlib import Path
import sys,ctypes,struct,json
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
D=Path(__file__).parent;pid=33180;base=22879776;checked_window(pid)
k=ctypes.WinDLL('kernel32');k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);r=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(r)) or r.value!=n:raise ValueError('Short read')
 return b.raw
try:
 p=read(base+0x1418c8,0xe4);mapping=read(base+0xee430,64)
 result={'pid':pid,'mapping_u16':list(struct.unpack('<32H',mapping)),'mapping_u32':list(struct.unpack('<16I',mapping)),'weapon_energy':list(p[0xa8:0xb8]),'boss_flags':p[0xb9],'input_held':struct.unpack_from('<H',p,0x7c)[0],'process_memory_written':False}
 (D/'input_baseline.local.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result))
finally:k.CloseHandle(h)
