"""명시 PID의 읽기 전용 부팅 관찰. 키/포커스/메모리 쓰기 API를 사용하지 않는다."""
import ctypes,json,struct,sys
import numpy as np
from PIL import Image
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.audit_sprite_consistency_coverage import read_assets,unique_entry,file_sha,sha,write
from src.epsxe_state import framebuffer
SESSION=ROOT/'work/ver_rin_nana/emulator_sessions/20261105T102945242982Z'
OUT=Path(__file__).resolve().parent/'nana_boot_readonly'
rec=json.loads((SESSION/'session.local.json').read_text('utf8'));assert rec['pid']==4880
build=Path(rec['cue']).with_suffix('.bin');assert file_sha(build)==rec['bin_sha256']=='de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679'
assets,_=read_assets(build,['SLUS_005.61','LOAD_U.ARC','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'])
exe=assets['SLUS_005.61'];font=unique_entry(assets['LOAD_U.ARC'],0x10001)
class Region(ctypes.Structure):
 _fields_=[('base',ctypes.c_void_p),('allocation',ctypes.c_void_p),('allocation_protect',wintypes.DWORD),('size',ctypes.c_size_t),('state',wintypes.DWORD),('protect',wintypes.DWORD),('type',wintypes.DWORD)]
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
k.VirtualQueryEx.restype=ctypes.c_size_t;k.CloseHandle.argtypes=[wintypes.HANDLE]
k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
h=k.OpenProcess(0x410,False,rec['pid']);assert h,'Read-only open failed'
def read(at,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
 return b.raw if k.ReadProcessMemory(h,at,b,n,ctypes.byref(got)) and got.value==n else b''
def ex(a,n):return exe[a-0x10000+2048:a-0x10000+2048+n]
try:
 code=wintypes.DWORD();assert k.GetExitCodeProcess(h,ctypes.byref(code)) and code.value==259,'Process already exited'
 name=ctypes.create_unicode_buffer(32768);length=wintypes.DWORD(len(name));assert k.QueryFullProcessImageNameW(h,0,name,ctypes.byref(length))
 assert Path(name.value).resolve()==Path(rec['executable']).resolve() and file_sha(Path(name.value))==rec['exe_sha256'],'PID image differs'
 rams=set();videos=set();address=0;scanbytes=0
 ra=0x233c8;rn=ex(ra,56);vn=font[3*128:4*128];va=259*2048+960*2
 while address<0x100000000:
  r=Region()
  if not k.VirtualQueryEx(h,address,ctypes.byref(r),ctypes.sizeof(r)):break
  lo=r.base or 0;end=lo+r.size
  if end<=address:break
  if r.state==0x1000 and not r.protect&0x100 and r.protect&255 in(2,4,8,32,64,128):
   for start in range(lo,end,1048576):
    blob=read(start,min(end-start,1048704));scanbytes+=len(blob)
    for needle,adjust,found in((rn,ra,rams),(vn,va,videos)):
     pos=blob.find(needle)
     while pos>=0:
      base=start+pos-adjust
      if base>0:found.add(base)
      pos=blob.find(needle,pos+1)
  address=end
 rams={b for b in rams if all(read(b+a,32)==ex(a,32)for a in(0x233c8,0x23400,0xea20c))}
 videos={b for b in videos if all(read(b+(256+y)*2048+960*2,128)==font[y*128:(y+1)*128]for y in(2,3,4,5))}
 result={'pid':4880,'session':str(SESSION.relative_to(ROOT)),'bin_sha256':rec['bin_sha256'],'process_image_validated':True,'ram_bases':sorted(rams),'vram_bases':sorted(videos),
 'process_memory_written':False,'keys_sent':False,'focus_changed':False,'scan_bytes_not_dumped':scanbytes,'runtime_scope':'부팅 상태 관찰만. 입력/스테이트 불러오기 없음.'}
 assert not OUT.exists(),'Output already exists';OUT.mkdir()
 if len(rams)==1:
  rb=next(iter(rams));ram=read(rb,0x200000);assert len(ram)==0x200000;(OUT/'ram.bin').write_bytes(ram)
  result['ram_sha256']=sha(ram);result['player_bytes']=ram[0x1418c8:0x1418c8+228].hex()
  result['player_fields']={'character':ram[0x1418ca],'frame':ram[0x14190f],'hp':ram[0x141924],'armor':ram[0x14196f],'ultimate':ram[0x1721f7]}
  result['resident_player_assets']={}
  for name in('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
   result['resident_player_assets'][name]={str(t):ram.find(unique_entry(assets[name],t)) for t in(2,3,9)}
  draws=[]
  for at in(0x166c10,0x166cb0):
   display=struct.unpack_from('<4h',ram,at);clip=struct.unpack_from('<4h',ram,at+20)
   if display[2:]==(320,240) and clip[2:]==(320,240) and 0<=clip[0]<=704 and 0<=clip[1]<=272:draws.append({'address':hex(at|0x80000000),'display':display,'clip':clip,'isrgb24':ram[at+17]})
  result['draw_buffers']=draws
  if len(videos)==1:
   vb=next(iter(videos));vram=read(vb,0x100000);assert len(vram)==0x100000;(OUT/'vram.bin').write_bytes(vram);result['vram_sha256']=sha(vram)
   for draw in draws:
    x,y,w,hh=draw['display']
    if draw['isrgb24']:
     rgb=np.ndarray((hh,w,3),dtype=np.uint8,buffer=vram,offset=y*2048+x*2,strides=(2048,3,1)).copy()
     draw['correct_framebuffer']=f'frame_{y}_rgb24.png';Image.fromarray(rgb).save(OUT/draw['correct_framebuffer'])
    else:
     draw['correct_framebuffer']=f'frame_{y}_rgb16.png';framebuffer(vram,x*2,y).save(OUT/draw['correct_framebuffer'])
 else:result['dump_skipped']='RAM missing or ambiguous; no unrelated process memory saved'
 k.GetExitCodeProcess(h,ctypes.byref(code));result['process_alive_after_read']=code.value==259
 write(OUT/'evidence.json',result)
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'ram':sorted(rams),'vram':sorted(videos),'alive':result['process_alive_after_read']}))
finally:k.CloseHandle(h)
