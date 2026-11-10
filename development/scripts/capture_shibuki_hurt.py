"""실제 피격을 RAM/VRAM/화면에서 읽기 전용 관찰한다. 키 입력·메모리 쓰기 없음."""
import argparse,ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from scripts.emulator_session import checked_window
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.epsxe_state import framebuffer,match_sprite

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--seconds',type=float,default=15);p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');args=p.parse_args();project=args.project;character='nana' if project=='ver_rin_nana' else 'shibuki'
 if character=='nana':
  import scripts.emulator_session as session_control
  session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
 if not 1<=args.seconds<=30:raise ValueError('Observation limited to 30 seconds')
 path=args.baseline.resolve()
 if not path.is_relative_to(ROOT/'work'/project/'live_poc'):raise ValueError('Unexpected baseline')
 prior=json.loads(path.read_text());build=Path(prior['source_build']);m=json.loads((build/'manifest.json').read_text());arc=(build/'modified.arc').read_bytes()
 if m['task']!='x_'+character or prior['modified_bin_sha256']!=m['modified_bin']['sha256'] or digest(build/'modified.arc')!=m['modified_archive_sha256']:raise ValueError('Build mismatch')
 entries=psx_arc(arc)
 def entry(t):
  e=next(e for e in entries if int(e['type'],16)==t);return arc[e['offset']:e['offset']+e['size']]
 gfx,parts,pal=entry(2),entry(3),entry(9)[:96];bank=graphics_bank(gfx,0,allow_bank_aliases=True);expected={};rasters={};out=new_run(ROOT,project,character+'_hurt_runtime')
 for n in range(106,115):
  f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;expected[n]=raw;indices,size,_,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n),allowed_cluts={0,2});rasters[n]=(indices,size);save_image(indices,size,struct.unpack('<48H',pal),out/f'expected_{n:03d}.png')
 checked_window(prior['pid']);k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x410,False,prior['pid'])
 if not h:raise OSError('Read-only process unavailable')
 def read(addr,size):
  b=ctypes.create_string_buffer(size);count=ctypes.c_size_t()
  if not k.ReadProcessMemory(h,addr,b,size,ctypes.byref(count)) or count.value!=size:raise OSError('Short read')
  return b.raw
 base=prior['ram_host_address'];video=prior['vram_host_address'];samples={n:[] for n in expected};trace=[]
 try:
  player=read(base+0x1418c8,0xe4);ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
  if player[2]!=0 or read(base+ptr,bank['end']-bank['base'])!=gfx[bank['base']:bank['end']]:raise ValueError('Current RAM differs from patched X')
  start=time.monotonic()
  while time.monotonic()-start<args.seconds:
   player=read(base+0x1418c8,0xe4);aid=player[0x17];n=player[0x47];row=[aid,n,player[0x5c],bool(player[0x15]&64),*[(struct.unpack_from('<i',player,o)[0]/65536) for o in (8,12)]]
   if not trace or trace[-1][1:]!=row:trace.append([round(time.monotonic()-start,5),*row])
   if player[2]==0 and aid in (33,34,36,37) and n in expected and len(samples[n])<64:
    ram=read(base+0x16dea8,len(expected[n]));vram=read(video,1048576);after=read(base+0x1418c8,0xe4)
    if (after[2],after[0x17],after[0x47])==(0,aid,n):samples[n].append((player,ram,vram))
   time.sleep(.003)
 finally:k.CloseHandle(h)
 results={}
 for n,group in samples.items():
  diagnostics=[];matches=[]
  for i,(player,ram,vram) in enumerate(group):
   f=bank['frames'][n];upload=bytearray()
   for first in range(0,f['tile_count'],16):
    width=min(16,f['tile_count']-first)*8
    for row in range(16):start=(first//16*16+row)*2048+640;upload.extend(vram[start:start+width])
   live= vram[480*2048:480*2048+96];ok=ram==expected[n] and bytes(upload)==expected[n]
   diagnostic={'sample':i,'ram_equal':ram==expected[n],'vram_equal':bytes(upload)==expected[n],'base_palette_equal':live==pal,'facing_right':bool(player[0x15]&64)};diagnostics.append(diagnostic)
   if not ok:continue
   picture=save_image(*rasters[n],struct.unpack('<48H',live),out/f'live_expected_{n:03d}.png')
   for page in (0,256):
    screen=framebuffer(vram,0,page);found=match_sprite(screen,picture)
    if not found:continue
    matches.extend([{'sample':i,'page_y':page,**r} for r in found]);screen.save(out/f'actual_{n:03d}_{page}.png');(out/f'player_{n:03d}.bin').write_bytes(player);(out/f'vram_{n:03d}.bin').write_bytes(vram)
   if matches:break
  results[str(n)]={'observed':bool(group),'verified':bool(matches),'samples':diagnostics,'matches':matches}
 report={'source_build':str(build),'modified_bin_sha256':m['modified_bin']['sha256'],'pid':prior['pid'],'baseline':str(path),'frames':results,'verified_frames':[int(n) for n,r in results.items() if r['verified']],'unverified_frames':[int(n) for n,r in results.items() if not r['verified']],'input_sent':False,'process_memory_written':False}
 write_json(out/'trace.json',{'columns':['seconds','animation','frame','hp','facing_right','x','y'],'rows':trace});write_json(out/'verification.local.json',report);print(json.dumps({'output':str(out),'verified':report['verified_frames'],'unverified':report['unverified_frames']}))
if __name__=='__main__':main()
