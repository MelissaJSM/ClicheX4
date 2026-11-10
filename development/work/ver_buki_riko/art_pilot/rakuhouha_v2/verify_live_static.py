from pathlib import Path
import sys,json,ctypes,struct
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
from scripts.discover_inputs import psx_arc
from scripts.project import digest
D=Path(__file__).parent;P=Path(sys.argv[1]);b=json.loads(P.read_text());checked_window(b['pid'])
B=Path(b['source_build']);m=json.loads((B/'manifest.json').read_text());assert digest(B/'modified.arc')==m['modified_archive_sha256'];arc=(B/'modified.arc').read_bytes();em=next(e for e in psx_arc(arc) if e['type']=='0x10206');tex=arc[em['offset']:em['offset']+em['size']]
k=ctypes.WinDLL('kernel32');k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,b['pid'])
def read(a,n):
 buf=ctypes.create_string_buffer(n);r=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,a,buf,n,ctypes.byref(r)) or r.value!=n:raise ValueError('Short read')
 return buf.raw
def from_vram(v):
 out=bytearray(len(tex))
 for n in range(len(tex)//128):
  t=n//80*256+n%80+0x5b0;tx=(t>>8&15)*64+(t&15)*4;ty=(t>>12&1)*256+(t&240)
  for y in range(16):
   dest=(n//16*16+y)*128+n%16*8;src=(ty+y)*2048+tx*2;out[dest:dest+8]=v[src:src+8]
 return bytes(out)
try:
 p=read(b['ram_host_address']+0x1418c8,0xe4);v=read(b['vram_host_address'],1048576);actual=from_vram(v)
 result={'pid':b['pid'],'build':str(B),'baseline':str(P),'static_texture_bytes':len(tex),'full_static_texture_equal':actual==tex,'different_bytes':sum(a!=b for a,b in zip(tex,actual)),'character':p[2],'animation':p[0x17],'frame':p[0x47],'hp':p[0x5c],'energy':p[0xa8],'x':struct.unpack_from('<i',p,8)[0]/65536,'y':struct.unpack_from('<i',p,12)[0]/65536,'process_memory_written':False}
 (D/'live_static.local.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result));assert actual==tex
finally:k.CloseHandle(h)
