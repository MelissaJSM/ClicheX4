"""최신 두 CUE의 실제 상주 자원/활성 프레임 디코드/GPU 업로드 읽기 전용 검사.

키·포커스·프로세스 상태·메모리·세이브 쓰기 없음. root가 PID/주소/조작을 관리한다.
"""
import argparse,ctypes,json,struct,sys,time
from datetime import datetime,timezone
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.audit_sprite_consistency_coverage import read_assets,unique_entry,file_sha,sha,write
from src.psx_player import bank_offsets,graphics_bank,decode_stream
from src.epsxe_state import framebuffer
from scripts.ultimate_costume_renderer import emit,off,START,END
import numpy as np
from PIL import Image

EXPECTED={'ver_buki_riko':'5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d',
          'ver_rin_nana':'de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679'}
PLAYER=0x1418c8;BUF=0x16dea8

def need(v,message):
 if not v:raise ValueError(message)

class ReadOnlyProcess:
 def __init__(self,rec):
  self.k=ctypes.WinDLL('kernel32',use_last_error=True);k=self.k
  k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
  k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
  k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
  k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.CloseHandle.argtypes=[wintypes.HANDLE]
  self.h=k.OpenProcess(0x410,False,rec['pid']);need(self.h,'Read-only OpenProcess failed')
  code=wintypes.DWORD();need(k.GetExitCodeProcess(self.h,ctypes.byref(code)) and code.value==259,'Process exited')
  name=ctypes.create_unicode_buffer(32768);count=wintypes.DWORD(len(name))
  need(k.QueryFullProcessImageNameW(self.h,0,name,ctypes.byref(count)),'Process identity unavailable')
  need(Path(name.value).resolve()==Path(rec['executable']).resolve() and file_sha(Path(name.value))==rec['exe_sha256'],'PID executable identity differs')
 def read(self,at,n):
  b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
  need(self.k.ReadProcessMemory(self.h,at,b,n,ctypes.byref(got)) and got.value==n,'ReadProcessMemory failed')
  return b.raw
 def close(self):self.k.CloseHandle(self.h)

def load(session,project):
 need(session.resolve().is_relative_to(ROOT/'work'/project/'emulator_sessions'),'Session outside project')
 rec=json.loads((session/'session.local.json').read_text('utf8'));cue=Path(rec['cue'])
 import re
 match=re.match(r'FILE "([^"\r\n]+)" BINARY',cue.read_text('ascii'))
 need(match and Path(match[1]).name==match[1],'Unsupported CUE');game=cue.parent/match[1]
 pointer=json.loads((ROOT/'projects'/project/'current_build.json').read_text('utf8'))
 manifest=json.loads((game.parent/'manifest.json').read_text('utf8'))
 need(file_sha(game)==rec['bin_sha256']=={'ver_buki_riko': '0000000000000000000000000000000000000000000000000000000000000000', 'ver_rin_nana': 'bfedca226e27bb34fcef3520faf62ee60a53357d007db08cf2cca46456dd5532'}[project]==manifest['modified_bin']['sha256'],'Unexpected current disc')
 assets,records=read_assets(game,['SLUS_005.61','LOAD_U.ARC','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'])
 return rec,game,assets

def identify(ram,assets):
 found=[]
 for name in('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
  es={t:unique_entry(assets[name],t)for t in(2,3,9)};addresses={t:ram.find(es[t])for t in es}
  if any(v<0 for v in addresses.values()):continue
  need(all(ram.find(es[t],addresses[t]+1)<0 for t in es),'Resident asset ambiguous')
  gb=bank_offsets(es[2],allow_aliases=True);cb=bank_offsets(es[3]);ptrs=struct.unpack_from('<II',ram,PLAYER+0x38)
  candidates=[];matched=[]
  for bank,partsbank in(((0,0),(1,5))if name=='PL01_U.ARC'else((0,0),)):
   gp=0x80000000+addresses[2]+gb[bank];cp=0x80000000+addresses[3]+cb[partsbank]
   candidates.append((bank,partsbank,gp,cp))
   if ptrs==(gp,cp):matched.append((bank,partsbank,gp,cp))
  found.append((name,es,addresses,candidates,matched))
 return found

def screen_dump(ram,vram,out):
 draws=[]
 for at in(0x166c10,0x166cb0):
  x,y,w,h=struct.unpack_from('<4h',ram,at);rgb24=ram[at+17]
  if (w,h)!=(320,240)or not(0<=x<=704 and 0<=y<=272):continue
  filename=f'frame_{y}_rgb{24 if rgb24 else 16}.png'
  if rgb24:
   im=Image.fromarray(np.ndarray((h,w,3),np.uint8,buffer=vram,offset=y*2048+x*2,strides=(2048,3,1)).copy())
  else:im=framebuffer(vram,x*2,y)
  im.save(out/filename);draws.append({'display_address':hex(at|0x80000000),'x':x,'y':y,'rgb24':bool(rgb24),'path':filename})
 return draws

def main(a):
 need(0<=a.seconds<=30,'0..30 seconds only');out=a.output.resolve()
 need(any(out.is_relative_to(ROOT/p) for p in ('work/sprite_consistency_20261105','work/sprite_reaudit_20261106/runtime','work/sprite_style_unification_20261107/runtime')) and not out.exists(),'Fresh task evidence directory required')
 session=a.session.resolve();rec,game,assets=load(session,a.project);proc=ReadOnlyProcess(rec)
 try:
  read=proc.read;ram=read(a.ram_base,0x200000);vram=read(a.vram_base,0x100000);exe=assets['SLUS_005.61']
  for address in(0x1540c,0x15ecc,0x233c8,0x23400,0xea20c):
   need(ram[address:address+48]==exe[address-0x10000+2048:address-0x10000+2096],'Native EXE anchor mismatch')
  font=unique_entry(assets['LOAD_U.ARC'],0x10001)
  need(all(vram[(256+y)*2048+1920:(256+y)*2048+2048]==font[y*128:(y+1)*128]for y in(2,3,4,5)),'VRAM font anchors differ')
  need(exe[off(START):off(END)]==emit() and ram[START&0x1fffffff:END&0x1fffffff]==emit(),'Display-policy code differs')
  found=identify(ram,assets);active=[r for r in found if r[4]]
  if a.seconds:need(len(active)==1,'Start watch only after one authenticated active player archive is loaded')
  out.mkdir(parents=True);(out/'ram_start.bin').write_bytes(ram);(out/'vram_start.bin').write_bytes(vram)
  report={'project':a.project,'session':session.relative_to(ROOT).as_posix(),'pid':rec['pid'],'disc':game.relative_to(ROOT).as_posix(),
   'disc_sha256':rec['bin_sha256'],'ram_base':a.ram_base,'vram_base':a.vram_base,'keys_sent':False,'focus_changed':False,'process_memory_written':False,
   'cards_or_states_modified':False,'ram_start_sha256':sha(ram),'vram_start_sha256':sha(vram),'framebuffers':screen_dump(ram,vram,out),
   'engine_state':ram[0x1721c0],'stage':ram[0x1721cc],'area':ram[0x1721cd],'character':ram[PLAYER+2],'hp':ram[PLAYER+0x5c],
   'player_armor':ram[PLAYER+0xa7],'engine_armor':ram[0x172207],'ultimate_or_black':ram[0x1721f7],'weapon':ram[PLAYER+0x93],
   'resident_assets':[{ 'archive':n,'archive_sha256':sha(assets[n]),'entries':{str(t):{'ram_offset':addr[t],'size':len(es[t]),'sha256':sha(es[t])}for t in es},'active_banks':matched}for n,es,addr,cand,matched in found],
   'renderer_code_ram_matches_disc':True,'renderer_policy_source':'scripts/verify_ultimate_costume_runtime.py::visual_mask; actual 208B renderer identical to reviewed emit()'}
  report['runtime_scope']='실제 상주 자원·관측된 활성 프레임의 디코드/VRAM 업로드. 최종 화면 전체 합성·미관측 모션·과거 F3 재사용은 검증 대상 밖.'
  events=[];valid=set();misses=0;errors=[];polls=0
  ready_utc=datetime.now(timezone.utc).isoformat();ready_monotonic_ns=time.monotonic_ns()
  report['ready_utc']=ready_utc;report['ready_monotonic_ns']=str(ready_monotonic_ns)
  print(json.dumps({'ready':True,'pid':rec['pid'],'seconds':a.seconds,'output':out.relative_to(ROOT).as_posix(),'active_assets':[r[0]for r in active],
   'ready_utc':ready_utc,'ready_monotonic_ns':str(ready_monotonic_ns)}),flush=True)
  start=time.monotonic();report['watch_start_utc']=datetime.now(timezone.utc).isoformat();report['watch_start_monotonic_ns']=str(time.monotonic_ns())
  key=None;current=None;cache={};attempt_cycles=0;counter_start=struct.unpack('<I',read(a.ram_base+0x141bd8,4))[0]
  while active and(time.monotonic()-start<a.seconds or attempt_cycles==0):
   attempt_cycles+=1
   name,es,addresses,candidates,matched=active[0];p=read(a.ram_base+PLAYER,228);gp,cp=struct.unpack_from('<II',p,0x38)
   engine=read(a.ram_base+0x1721c0,100)
   matching=[v for v in candidates if (gp,cp)==v[2:]]
   if not matching:misses+=1;time.sleep(.004);continue
   bank,partsbank,_,_=matching[0];n=p[0x47];idx=(bank,n)
   if idx not in cache:
    frames=graphics_bank(es[2],bank,allow_bank_aliases=True)['frames']
    if n>=len(frames):misses+=1;time.sleep(.004);continue
    f=frames[n];need(f['tile_count']<=32,'Unsupported native player upload >32 tiles')
    cache[idx]=(f,decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
   f,expected=cache[idx];statekey=(bank,n,p[0x17],p[0x15],p[0xa7],p[0x93],engine[0x37],engine[0x47])
   if statekey!=key:
    current={'bank':bank,'parts_bank':partsbank,'frame':n,'animation':p[0x17],'facing_raw':p[0x15],'armor':p[0xa7],'weapon':p[0x93],
     'tiles':f['tile_count'],'first_seen_seconds':time.monotonic()-start,'attempts':0,'stable_samples':0,'ram_mismatches':0,'gpu_mismatches':0,'verified':False,
     'partial_upload_only':name=='PL01_U.ARC' and bank==1 and n in range(42,50),
     'engine_owned_armor':engine[0x47],'ultimate_or_black':engine[0x37],
     'derived_renderer_visual_mask':None if p[2] else p[0xa7] if not engine[0x37] else 15 if engine[0x47]==0 or 217<=n<=230 else 0,
     'display_policy_class':('zero_shared_bitmap_black_palette' if p[2] else 'ultimate_before_jacket' if engine[0x37] and engine[0x47]==0 else 'ultimate_after_swim_special_fx' if engine[0x37] and 217<=n<=230 else 'ultimate_after_swim' if engine[0x37] else 'base_or_fourth_native_mask')}
    events.append(current);key=statekey
   decoded=read(a.ram_base+BUF,len(expected));gpu=bytearray()
   for first in range(0,f['tile_count'],16):
    width=min(f['tile_count']-first,16)*8
    for y in range(16):gpu+=read(a.vram_base+(first//16*16+y)*2048+640,width)
   again=read(a.ram_base+PLAYER,228);current['attempts']+=1;polls+=1
   if p[0x38:0x4a]==again[0x38:0x4a]:
    current['stable_samples']+=1
    if decoded!=expected:current['ram_mismatches']+=1
    if bytes(gpu)!=expected:current['gpu_mismatches']+=1
    if decoded==expected and bytes(gpu)==expected:current['verified']=True;valid.add(idx)
   time.sleep(.003)
  report['watch_end_utc']=datetime.now(timezone.utc).isoformat();report['watch_end_monotonic_ns']=str(time.monotonic_ns())
  report['events']=events;report['verified_bank_frames']=[list(x)for x in sorted(valid)];report['skipped_samples']=misses;report['polls']=polls;report['duration_seconds']=time.monotonic()-start
  report['observed_uploads_verified']=bool(valid);report['unverified_events']=[i for i,e in enumerate(events)if not e['verified']]
  report['non_atomic_transition_warning']='전환 도중 불일치가 생길 수 있음. 해당 프레임의 안정 표본이 일치했을 때만 관측 성공으로 기록.'
  report['resident_assets_still_exact']={n:{str(t):read(a.ram_base+addr[t],len(es[t]))==es[t]for t in es}for n,es,addr,cand,matched in found}
  counter_end=struct.unpack('<I',read(a.ram_base+0x141bd8,4))[0]
  report['native_main_loop_counter']={'start':counter_start,'end':counter_end,'address':'0x80141BD8','ticks_per_second':(counter_end-counter_start)/max(report['duration_seconds'],.00001),
   'is_display_fps':False,'limitation':'FMV/CD waits or replay restore can pause/reset this native main-loop counter.'}
  write(out/'evidence.json',report);print(json.dumps({'done':True,'verified':report['verified_bank_frames'],'events':len(events),'unverified':report['unverified_events']}))
 finally:proc.close()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',choices=EXPECTED,required=True);p.add_argument('--session',type=Path,required=True)
 p.add_argument('--ram-base',type=int,required=True);p.add_argument('--vram-base',type=int,required=True);p.add_argument('--seconds',type=float,default=0);p.add_argument('--output',type=Path,required=True)
 main(p.parse_args())
