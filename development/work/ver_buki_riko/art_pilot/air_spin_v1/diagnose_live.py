from pathlib import Path
import ctypes,json,struct,sys
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank
from scripts.emulator_session import checked_window
D=Path(__file__).parent;pid=50440;base=22879776;checked_window(pid)
k=ctypes.WinDLL('kernel32');k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);r=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(r)) or r.value!=n:raise ValueError('Short read')
 return b.raw
try:
 ram=read(base,2097152);p=ram[0x1418c8:0x1418c8+0xe4];ptr=struct.unpack_from('<I',p,0x38)[0]&0x1fffff;checks=[]
 for name,path in [('spin','out/ver_buki_riko/riko_bank1_20261025T093925764170Z/modified.arc'),('hurt','out/ver_buki_riko/riko_bank1_20261025T090314908139Z/modified.arc'),('original','work/ver_buki_riko/zero_extract/20261023T062408235550Z/original.arc')]:
  a=(ROOT/path).read_bytes();gm=next(e for e in psx_arc(a) if e['type']=='0x2');gfx=a[gm['offset']:gm['offset']+gm['size']]
  for bi in (0,1):
   b=graphics_bank(gfx,bi);want=gfx[b['base']:b['end']];actual=ram[ptr:ptr+len(want)]
   checks.append({'build':name,'bank':bi,'equal':actual==want,'different_bytes':sum(x!=y for x,y in zip(actual,want)),'loaded_at':ram.find(want)})
 result={'pid':pid,'character':p[2],'animation':p[0x17],'frame':p[0x47],'hp':p[0x5c],'flags':p[0xb9],'pointer':hex(ptr),'checks':checks}
 (D/'live_provenance.local.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result))
finally:k.CloseHandle(h)
