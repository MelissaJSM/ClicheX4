"""현재 사용자 키 배정으로 일반 조작을 재생하고 X 몸의 RAM/VRAM/화면을 대조한다."""
import argparse,ctypes,json,struct,sys,time,winreg
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
from scripts.project import new_run,write_json,digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.epsxe_state import framebuffer,match_sprite

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko');p.add_argument('--evidence',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);args=p.parse_args();evidence=args.evidence.resolve()
 if not evidence.is_relative_to(ROOT/'work'/args.project/'live_poc'):raise ValueError('Unexpected evidence')
 if args.project=='ver_rin_nana':
  import scripts.emulator_session as session_control
  session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
 prior=json.loads(evidence.read_text());build=Path(prior['source_build']);manifest=json.loads((build/'manifest.json').read_text());ultimate=manifest['task'] in ('ultimate_armor_shibuki','ultimate_armor_nana');arcpath=build/('PL02_U.ARC' if ultimate else 'modified.arc');arc=arcpath.read_bytes()
 if manifest['task'] not in (('x_nana','ultimate_armor_nana') if args.project=='ver_rin_nana' else ('x_shibuki','ultimate_armor_shibuki')) or digest(arcpath)!=manifest['modified_archive_sha256'] or prior['modified_bin_sha256']!=manifest['modified_bin']['sha256']:raise ValueError('Baseline changed')
 es=psx_arc(arc);gfx,parts,palette=[arc[e['offset']:e['offset']+e['size']] for t in (2,3,9) for e in es if int(e['type'],16)==t];bank=graphics_bank(gfx,0,allow_bank_aliases=True)
 plan=json.loads(args.plan.read_text());duration=plan['seconds']
 if not .1<=duration<=30:raise ValueError('Duration outside 0.1..30')
 with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as key:pad=list(map(int,winreg.QueryValueEx(key,'Pad1')[0].split(',')))
 indices={'left':0,'right':1,'up':2,'down':3,'triangle':4,'dash':5,'jump':6,'fire':7,'previous':8,'next':9,'l2':10,'r2':11,'menu':12,'select':13}
 if len(pad)!=16 or any(k not in indices or not 0<=s<e<=duration for k,s,e in plan['keys']):raise ValueError('Invalid input plan')
 user,window=checked_window(prior['pid']);kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE;kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];kernel.CloseHandle.argtypes=[wintypes.HANDLE];handle=kernel.OpenProcess(0x410,False,prior['pid'])
 if not handle:raise OSError('Cannot open read-only process')
 def read(address,length):
  b=ctypes.create_string_buffer(length);n=ctypes.c_size_t()
  if not kernel.ReadProcessMemory(handle,address,b,length,ctypes.byref(n)) or n.value!=length:raise OSError('Short read')
  return b.raw
 def key(name,down):
  sc=pad[indices[name]];ev=Input();ev.type=1;ev.data.key=KeyInput(0,sc&127,8|int(bool(sc&128))|(0 if down else 2),0,0)
  if user.SendInput(1,ctypes.byref(ev),ctypes.sizeof(ev))!=1:raise OSError('Key input failed')
 base,video=prior['ram_host_address'],prior['vram_host_address'];out=new_run(ROOT,args.project,'nana_batch_runtime' if args.project=='ver_rin_nana' else 'shibuki_batch_runtime');held=set();trace=[];samples={};cached={};seen={};last_samples={};failure=None;bank_verified_at=None
 try:
  player=read(base+0x1418c8,0xe4);ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
  if ultimate and (player[0xa7]!=0 or read(base+0x1721f7,1)!=b'\x01'):raise ValueError('Expected unlocked pre-capsule Ultimate route')
  ready=player[2]==0 and ptr+bank['end']-bank['base']<=0x200000 and read(base+ptr,bank['end']-bank['base'])==gfx[bank['base']:bank['end']]
  if not ready and not plan.get('wait_for_graphics_bank',False):raise ValueError('Not the patched X graphics bank')
  if ready:bank_verified_at=0.0
  user.ShowWindowAsync(window,9);user.SetForegroundWindow(window);time.sleep(.15);start=time.monotonic()
  while time.monotonic()-start<duration:
   elapsed=time.monotonic()-start
   if user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed')
   wanted={k for k,s,e in plan['keys'] if s<=elapsed<e}
   for k in held-wanted:key(k,False)
   for k in wanted-held:key(k,True)
   held=wanted;player=read(base+0x1418c8,0xe4);n=player[0x47];aid=player[0x17];clut=struct.unpack_from('<H',player,0x42)[0];state=[player[2],aid,n,player[0x15],player[0x5c],player[0x93],clut,*struct.unpack_from('<ii',player,8),player[0xa7],player[0xb9]]
   if not trace or trace[-1][1:]!=state:trace.append([round(elapsed,5),*state])
   if not ready:
    ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
    ready=player[2]==0 and ptr+bank['end']-bank['base']<=0x200000 and read(base+ptr,bank['end']-bank['base'])==gfx[bank['base']:bank['end']]
    if ready:bank_verified_at=round(elapsed,5)
   if ready and player[2]==0 and n<237:
    tag=(n,aid,player[0x15]&64,clut,player[0x93])
    if seen.get(tag,0)<8 and elapsed-last_samples.get(tag,-1)>=.020:
     if n not in cached:
      f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
      try:indices0,size,_,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))
      except ValueError:time.sleep(.003);continue
      cached[n]=(raw,indices0,size)
     raw,indices0,size=cached[n];decoded=read(base+0x16dea8,len(raw));vram=read(video,1048576);after=read(base+0x1418c8,0xe4)
     if (after[2],after[0x17],after[0x47])==(0,aid,n):samples.setdefault(tag,[]).append((elapsed,player,decoded,vram));seen[tag]=seen.get(tag,0)+1;last_samples[tag]=elapsed
   time.sleep(.003)
 except Exception as e:failure=repr(e)
 finally:
  for k in held:key(k,False)
  kernel.CloseHandle(handle)
  write_json(out/'trace.json',{'columns':['seconds','character','animation','frame','flags15','hp','weapon','clut','x_fixed16','y_fixed16','armor','boss_flags'],'rows':trace,'failure':failure,'pad1':pad,'plan':plan})
 results=[]
 for tag,group in samples.items():
  n,aid,facing,clut,weapon=tag;raw,indices0,size=cached[n];rec={'frame':n,'animation':aid,'weapon':weapon,'flags15_bit6':facing,'clut':clut,'ram_equal':False,'vram_equal':False,'render_matches':[],'palette_hex':[],'screen_comparison_skipped_samples':0};screens=[]
  for i,(elapsed,player,decoded,vram) in enumerate(group):
   count=bank['frames'][n]['tile_count'];cursor=0;upload=True
   for first in range(0,count,16):
    width=min(16,count-first)*8
    for y in range(16):
     pos=(first//16*16+y)*2048+640;upload&=vram[pos:pos+width]==raw[cursor:cursor+width];cursor+=width
   rec['ram_equal']|=decoded==raw;rec['vram_equal']|=upload;actual_clut=0x7840 if clut&0x8000 else clut;pos=(actual_clut>>6)*2048+(actual_clut&63)*32;colors=vram[pos:pos+32];hexpal=colors.hex()
   if hexpal not in rec['palette_hex']:rec['palette_hex'].append(hexpal)
   words=struct.unpack('<16H',colors)
   # A menu transition can clear both the player and CLUT. A black silhouette
   # matching a black loading screen is not evidence of the requested sprite.
   if (decoded!=raw and not upload) or not any(w&0x7fff for w in words):
    rec['screen_comparison_skipped_samples']+=1;continue
   target=save_image(indices0,size,words,out/f'expected_{n:03}_{aid:03}_{facing}_w{weapon}_{i}.png')
   for page in (0,240,256):
    screen=framebuffer(vram,0,page);matches=match_sprite(screen,target)
    if matches:
     path=f'actual_{n:03}_{aid:03}_{facing}_w{weapon}_{page}.png';screen.save(out/path);rec['render_matches'].extend([{'seconds':elapsed,'page':page,'image':path,**m} for m in matches])
    if i==0:
     path=f'observed_{n:03}_{aid:03}_{facing}_w{weapon}_{page}.png';screen.save(out/path);screens.append(path)
  rec.update(observed_screens=screens,base_palette_observed=palette[:32].hex() in rec['palette_hex']);results.append(rec)
 report={'source_build':str(build),'modified_bin_sha256':manifest['modified_bin']['sha256'],'pid':prior['pid'],'process_memory_written':False,'whole_bank_verified_at_seconds':bank_verified_at,'failure':failure,'capture_completed':failure is None,'plan':plan,'pad1':pad,'results':results,'observed_frames':sorted({r['frame'] for r in results}),'ram_vram_verified_frames':sorted({r['frame'] for r in results if r['ram_equal'] and r['vram_equal']}),'render_matched_frames':sorted({r['frame'] for r in results if r['render_matches']}),'base_palette':palette[:32].hex()};write_json(out/'verification.local.json',report);print(json.dumps({'output':str(out),'observed':report['observed_frames'],'ram_vram':report['ram_vram_verified_frames'],'render':report['render_matched_frames'],'capture_completed':failure is None}))
 if failure:raise RuntimeError('Capture stopped; partial evidence saved: '+failure)
if __name__=='__main__':main()
