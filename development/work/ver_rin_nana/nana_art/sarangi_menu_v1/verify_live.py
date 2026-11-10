"""현재 ePSXe의 읽기 전용 VRAM에서 사랑이 메뉴 아이콘을 대조한다."""
import argparse, ctypes, json, sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from PIL import Image
from src.epsxe_state import framebuffer,match_sprite
from scripts.emulator_session import checked_window
import scripts.emulator_session as session_control
session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
from scripts.project import digest

p=argparse.ArgumentParser();p.add_argument('--discovery',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
d=json.loads(args.discovery.read_text('utf8'))
checked_window(d['pid'])
out=args.output.resolve()
if not out.is_relative_to(ROOT/'work/ver_rin_nana') or out.exists():raise ValueError('Fresh isolated output required')
out.mkdir()
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,d['pid'])
if not h:raise OSError('Read-only process open failed')
icons=Path(__file__).parent/'candidate01';results=[]
try:
 for i,addr in enumerate(d['vram_candidates']):
  buf=ctypes.create_string_buffer(1048576);got=ctypes.c_size_t()
  if not k.ReadProcessMemory(h,addr,buf,len(buf),ctypes.byref(got)) or got.value!=len(buf):raise OSError('Short VRAM read')
  for y in (0,256):
   screen=framebuffer(buf.raw,0,y)
   for name in ('icon.png','icon_dim.png'):
    matches=match_sprite(screen,Image.open(icons/name))
    if matches:
     file=f'actual_{i}_{y}_{name}';screen.save(out/file)
     results.append({'vram_host_address':addr,'page_y':y,'icon':name,'icon_sha256':digest(icons/name),'matches':matches,'screen':file})
finally:k.CloseHandle(h)
r={'pid':d['pid'],'discovery':str(args.discovery),'process_memory_written':False,'results':results,'matched':bool(results)}
(out/'verification.json').write_text(json.dumps(r,indent=2),'utf8')
print(json.dumps(r))
if not results:sys.exit(1)
