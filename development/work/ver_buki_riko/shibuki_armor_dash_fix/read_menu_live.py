import ctypes,json,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.capture_poc_memory import Region
from scripts.emulator_session import checked_window
from src.epsxe_state import framebuffer
pid=63920;checked_window(pid)
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t();return b.raw if k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) and got.value==n else b''
out=Path(__file__).parent/'menu_live';out.mkdir(exist_ok=True)
menu=(ROOT/'work/ver_buki_riko/shibuki_ui_v1/candidate17/MOJIPAT.ARC').read_bytes();off=struct.unpack_from('<I',menu,4)[0];palette=menu[off+256:off+288]
anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100');ram=set();palhits=set();menuset=set();address=0
try:
 while address<0x100000000:
  region=Region()
  if not k.VirtualQueryEx(h,address,ctypes.byref(region),ctypes.sizeof(region)):break
  start=region.base or 0;end=start+region.size
  if end<=address:break
  if region.state==0x1000 and not region.protect&0x100 and region.protect&0xff in (2,4,8,0x20,0x40,0x80):
   for pos in range(start,end,1048576):
    blob=read(pos,min(1048576+len(menu),end-pos))
    for pattern,dst,adjust in [(anchor,ram,0x11a2f8),(palette,palhits,0),(menu,menuset,0)]:
     q=0
     while (q:=blob.find(pattern,q))>=0:dst.add(pos+q-adjust);q+=1
  address=end
 for base in ram:
  raw=read(base,2097152)
  if len(raw)==2097152:(out/f'ram_{base}.bin').write_bytes(raw)
 for p in palhits:
  # Menu sprite palette lives at x=0..240, y=480..481. Check both.
  for delta in [480*2048+256,481*2048+256,480*2048+0,481*2048+0]:
   base=p-delta;v=read(base,1048576)
   if len(v)==1048576:
    (out/f'vram_{base}.bin').write_bytes(v);framebuffer(v,0,0).save(out/f'screen_{base}.png')
 report={'pid':pid,'ram_candidates':sorted(ram),'palette_hits':sorted(palhits),'menu_hits':sorted(menuset),'keys_sent':False,'memory_written':False};(out/'scan.json').write_text(json.dumps(report,indent=2));print(report)
finally:k.CloseHandle(h)
