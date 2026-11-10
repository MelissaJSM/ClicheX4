import ctypes,json,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
d=Path(__file__).parent;dis=json.loads((ROOT/'work/ver_rin_nana/live_poc/20261029T062412647411Z/discovery.local.json').read_text('utf8'));base=dis['ram_candidates'][0]
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x410,False,dis['pid'])
def read(addr,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,addr,b,n,ctypes.byref(got)) or got.value!=n:raise OSError('Short read')
 return b.raw
try:
 ram=read(base,2097152);rows=[]
 for n in range(64):
  p=ram[0x173ca0+n*96:0x173ca0+(n+1)*96]
  if not p[0]:continue
  rows.append({'index':n,'header':list(p[:8]),'xy':list(struct.unpack_from('<ii',p,8)),'clut':hex(struct.unpack_from('<H',p,0x42)[0]),'frame':p[0x47],'parts_pointer':hex(struct.unpack_from('<I',p,0x3c)[0]),'tpage':hex(struct.unpack_from('<H',p,0x40)[0])})
 packets=[]
 for off in range(0,len(ram)-16,4):
  if ram[off+3]&0xfc!=0x64:continue
  x,y=struct.unpack_from('<hh',ram,off+4);w,ht=struct.unpack_from('<HH',ram,off+12)
  if x==36 and 0<=y<=40 and w==16 and ht==16:packets.append({'offset':hex(off),'xy':[x,y],'uv':list(ram[off+8:off+10]),'clut':hex(struct.unpack_from('<H',ram,off+10)[0])})
 (d/'pause_objects.json').write_text(json.dumps({'objects':rows,'buster_packets':packets},indent=2),'utf8');print(json.dumps({'objects':rows,'buster_packets':packets}))
 for i,addr in enumerate(dis['vram_candidates']):
  v=read(addr,1048576);(d/f'pause_vram_{i}.bin').write_bytes(v)
finally:k.CloseHandle(h)
