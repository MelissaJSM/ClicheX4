"""갱신 저장에서 전체 X 은행과 현재 프레임을 읽기 전용 대조. 사다리 발동 검사는 아님."""
import ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from scripts.project import digest
from scripts.emulator_session import checked_window
import scripts.emulator_session as session_control
session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
discovery=ROOT/'work/ver_rin_nana/live_poc/20261029T232946297413Z/discovery.local.json';p=json.loads(discovery.read_text());build=Path(p['source_build']);m=json.loads((build/'manifest.json').read_text());assert p['modified_bin_sha256']==m['modified_bin']['sha256'];arc=(build/'modified.arc').read_bytes();assert sha256(arc)==m['modified_archive_sha256'];es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True);checked_window(p['pid'])
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x410,False,p['pid'])
if not h:raise OSError('Read-only process unavailable')
def read(addr,size):
 b=ctypes.create_string_buffer(size);n=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,addr,b,size,ctypes.byref(n))or n.value!=size:raise OSError('Short read')
 return b.raw
report=None
try:
 base=p['ram_candidates'][0];ram=read(base,0x200000);player=ram[0x1418c8:0x1418c8+0xe4];ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
 if player[2]!=0 or ram[ptr:ptr+bank['end']-bank['base']]!=es[2][bank['base']:bank['end']]:raise ValueError('Whole patched base bank differs')
 for attempt in range(40):
  player=read(base+0x1418c8,0xe4);n=player[0x47];f=bank['frames'][n];raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data
  if read(base+0x16dea8,len(raw))!=raw:time.sleep(.01);continue
  for video in p['vram_candidates']:
   vram=read(video,1048576);upload=bytearray()
   for first in range(0,f['tile_count'],16):
    width=min(16,f['tile_count']-first)*8
    for row in range(16):start=(first//16*16+row)*2048+640;upload.extend(vram[start:start+width])
   after=read(base+0x1418c8,0xe4)
   if bytes(upload)==raw and vram[480*2048:480*2048+32]==es[9][:32] and (after[2],after[0x17],after[0x47])==(0,player[0x17],n):
    report={'pid':p['pid'],'build':build.relative_to(ROOT).as_posix(),'build_sha256':m['modified_bin']['sha256'],'whole_base_graphics_bank_equal':True,'active_frame':n,'active_animation':player[0x17],'active_ram_texture_equal':True,'active_vram_texture_equal':True,'active_palette_equal':True,'ram_host_address':base,'vram_host_address':video,'input_sent':False,'process_memory_written':False,'ladder_animation_observed':False,'full_framebuffer_verified':False,'evidence_kind':'graphics-refreshed checkpoint'};break
  if report:break
  time.sleep(.01)
finally:k.CloseHandle(h)
if not report:raise RuntimeError('No stable active RAM/VRAM comparison')
(build/'live_bank_audit.local.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report))
