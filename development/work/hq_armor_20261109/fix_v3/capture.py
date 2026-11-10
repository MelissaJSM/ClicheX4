"""Read-only crash RAM capture from the user-selected ePSXe instance."""
import ctypes,json,struct,sys,hashlib
from ctypes import wintypes as w
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.capture_poc_memory import Region
OUT=Path(__file__).resolve().parent;PID=51628
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.VirtualQueryEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
h=k.OpenProcess(0x410,False,PID);assert h
def read(a,n):
 buf=ctypes.create_string_buffer(n);got=ctypes.c_size_t();return buf.raw if k.ReadProcessMemory(h,a,buf,n,ctypes.byref(got))and got.value==n else b''
try:
 path=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(path));assert k.QueryFullProcessImageNameW(h,0,path,ctypes.byref(n));assert Path(path.value).resolve()==(ROOT/'ePSXe2018/ePSXe.exe').resolve()
 exe=(ROOT/'work/hq_armor_20261109/ver_rin_nana/prepared/SLUS_005.61').read_bytes();rel=0xc9fe8;needle=exe[rel-0x10000+2048:rel-0x10000+2048+64]
 address=0;candidates=set()
 while address<0x100000000:
  r=Region()
  if not k.VirtualQueryEx(h,address,ctypes.byref(r),ctypes.sizeof(r)):break
  start=r.base or 0;end=start+r.size
  if end<=address:break
  if r.state==0x1000 and not r.protect&0x100 and r.protect&255 in(2,4,8,0x20,0x40,0x80):
   for off in range(start,end,1024*1024):
    b=read(off,min(1024*1024+64,end-off));pos=b.find(needle)
    while pos>=0:
     if off+pos>=rel:candidates.add(off+pos-rel)
     pos=b.find(needle,pos+1)
  address=end
 results=[]
 for a in sorted(candidates):
  ram=read(a,0x200000)
  if not ram or ram[0xc9ee8:0xc9ee8+28]!=exe[0xc9ee8-0x10000+2048:0xc9ee8-0x10000+2048+28]:continue
  name=f'ram_{a:x}.bin';(OUT/name).write_bytes(ram)
  q={'host_ram_base':a,'file':name,'sha256':hashlib.sha256(ram).hexdigest(),'stage':ram[0x1721cc],'substage':ram[0x1721cd],'character':ram[0x172203],'special':ram[0x1721f7],'armor':ram[0x172207],'pointers':{hex(p):hex(struct.unpack_from('<I',ram,p)[0])for p in[0x137dc4,0x15d9c8,0x1406a8]}}
  results.append(q)
 print(json.dumps(results,indent=2));(OUT/'capture.json').write_text(json.dumps({'pid':PID,'exe':path.value,'results':results,'keys_sent':False,'process_memory_written':False},indent=2))
finally:k.CloseHandle(h)
