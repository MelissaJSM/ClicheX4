import ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess,load
from scripts.audit_sprite_consistency_coverage import unique_entry,sha,write
S=ROOT/'work/ver_rin_nana/emulator_sessions/20261105T110314659196Z'
rec,game,assets=load(S,'ver_rin_nana');p=ReadOnlyProcess(rec);k=p.k
class Region(ctypes.Structure):
 _fields_=[('base',ctypes.c_void_p),('allocation',ctypes.c_void_p),('allocation_protect',wintypes.DWORD),('size',ctypes.c_size_t),('state',wintypes.DWORD),('protect',wintypes.DWORD),('type',wintypes.DWORD)]
k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.VirtualQueryEx.restype=ctypes.c_size_t
exe=assets['SLUS_005.61'];needles=[]
for at in(0x1540c,0x233c8,0x23400,0xea20c):needles.append((f'code_{at:x}',exe[at-0x10000+2048:at-0x10000+2048+48],at))
needles.append(('original_native',bytes.fromhex('150001000c0001922a0001930c00019436000100'),0x11a2f8))
for name in('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
 for t in(2,3):needles.append((f'{name}_{t}',unique_entry(assets[name],t)[:160],None))
hits={name:[]for name,_,_ in needles};rams=set();errors=[]
try:
 address=0
 while address<0x100000000:
  rr=Region()
  if not k.VirtualQueryEx(p.h,address,ctypes.byref(rr),ctypes.sizeof(rr)):break
  lo=rr.base or 0;end=lo+rr.size
  if end<=address:break
  if rr.state==0x1000 and not rr.protect&0x100 and rr.protect&255 in(2,4,8,32,64,128):
   for at in range(lo,end,1048576):
    try:blob=p.read(at,min(end-at,1048736))
    except ValueError:continue
    for name,needle,adjust in needles:
     pos=blob.find(needle)
     while pos>=0:
      loc=at+pos;hits[name].append(loc)
      if adjust is not None and loc>adjust:rams.add(loc-adjust)
      pos=blob.find(needle,pos+1)
  address=end
 summaries=[]
 for base in sorted(rams):
  try:ram=p.read(base,0x200000)
  except ValueError:continue
  anchors={name:ram[adjust:adjust+len(needle)]==needle for name,needle,adjust in needles if adjust is not None}
  summaries.append({'base':base,'anchors':anchors,'engine':ram[0x1721c0:0x172224].hex(),'player_first96':ram[0x1418c8:0x141928].hex(),
   'counter':struct.unpack_from('<I',ram,0x141bd8)[0],'rgb24':ram[0x166c21],
   'assets':{n:{str(t):ram.find(unique_entry(assets[n],t))for t in(2,3,9)}for n in('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')}})
 user=ctypes.WinDLL('user32',use_last_error=True);user.GetForegroundWindow.restype=wintypes.HWND;user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
 hwnd=user.GetForegroundWindow();fg=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(fg))
 report={'pid':rec['pid'],'hits':hits,'ram_candidates':summaries,'foreground_hwnd':int(hwnd or 0),'foreground_pid':fg.value,
 'keys_sent':False,'process_written':False,'only_candidate_metadata_saved':True}
 write(ROOT/'work/sprite_consistency_20261105/coverage/nana_boot_readonly_40296/address_candidates.json',report)
 print(json.dumps({'ram_candidates':[{'base':r['base'],'anchors':r['anchors'],'counter':r['counter'],'rgb24':r['rgb24']}for r in summaries],'foreground_pid':fg.value,'hits':{n:len(h)for n,h in hits.items()}}))
finally:p.close()
