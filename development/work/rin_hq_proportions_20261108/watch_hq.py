"""Fresh-disc full-body pixel comparison during normal HQ controls; read-only memory."""
from pathlib import Path
import argparse,json,sys,time,ctypes,hashlib
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.epsxe_state import framebuffer,match_sprite
import scripts.emulator_session as ctl
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--vram',type=int,required=True);p.add_argument('--seconds',type=float,default=40);p.add_argument('--action',choices=['watch','advance','depart'],default='watch');p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert 1<=a.seconds<=55 and not a.output.exists()
rec=json.loads((a.session/'session.local.json').read_text('utf8'));build=json.loads((W/'build.json').read_text('utf8'));assert rec['bin_sha256']==build['sha256'];proc=ReadOnlyProcess(rec)
assets,_=read_disc(Path(rec['cue']).with_suffix('.bin'),['SLUS_005.61','ST0D_0Z.ARC','COL0D_0Z.ARC']);exe=assets['SLUS_005.61'];g=entry(assets['ST0D_0Z.ARC'],0x10102)[63488:81920];parts=entry(assets['ST0D_0Z.ARC'],10);pal=entry(assets['COL0D_0Z.ARC'],5)[35*32:36*32]
ram=proc.read(a.ram,2097152);video=proc.read(a.vram,1048576)
for at in(0x1540c,0x15ecc,0x233c8):assert ram[at:at+48]==exe[at-0x10000+2048:at-0x10000+2096]
assert parts in ram,'Updated composition not resident';assert video[482*2048+96:482*2048+128]==pal
for r in range(144):
 off=(144+r)*2048+1024 if r<32 else (r-32)*2048+1152
 assert video[off:off+128]==g[r*128:(r+1)*128],f'GPU texture row {r} differs'
ctl.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';u,hw=ctl.checked_window(rec['pid'])
if a.action!='watch':u.ShowWindowAsync(hw,9);u.SetForegroundWindow(hw);time.sleep(.15);assert u.GetForegroundWindow()==hw
a.output.mkdir(parents=True);groups={}
for n in range(14):
 im=Image.open(W/'candidate02'/f'frame_{n:02d}.png').convert('RGBA');im=im.crop(im.getchannel('A').getbbox());key=(im.size,im.tobytes())
 if key not in groups:groups[key]={'frames':[],'image':im}
 groups[key]['frames'].append(n)
seen={};events=[];states=[];start=time.monotonic();lastkey=-10;samples=0;departed=False;trace=[];last_trace=None
def tap(scan):
 assert u.GetForegroundWindow()==hw,'Foreground changed'
 e=ctl.Input();e.type=1;e.data.key=ctl.KeyInput(0,scan&127,8|int(bool(scan&128)),0,0);assert u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
 try:time.sleep(.06)
 finally:e.data.key.flags|=2;u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))
 events.append({'scan':scan,'seconds':time.monotonic()-start})
try:
 while time.monotonic()-start<a.seconds:
  t=time.monotonic()-start;en=list(proc.read(a.ram+0x1721c0,4));tr=proc.read(a.ram+0x141bdc,1)[0]
  state={'engine':en,'transition':tr}
  if not states or state!=states[-1]['state']:states.append({'time':t,'state':state})
  v=proc.read(a.vram,1048576)
  for page in(0,240):
   screen=framebuffer(v,0,page)
   if a.action=='depart' and t<7:
    key=hashlib.sha256(screen.tobytes()).hexdigest()
    if page==0 and key!=last_trace:
     filename=f'trace_{len(trace):03d}.png';screen.save(a.output/filename);trace.append({'time':t,'file':filename,'state':state});last_trace=key
   for group in groups.values():
    key=','.join(map(str,group['frames']))
    if key in seen:continue
    hits=match_sprite(screen,group['image'])
    if hits:
     label='_'.join(map(str,group['frames']));screen.save(a.output/f'frames_{label}.png');screen.resize((960,720),Image.Resampling.NEAREST).save(a.output/f'frames_{label}_3x.png');(a.output/f'frames_{label}_vram.bin').write_bytes(v)
     seen[key]={'frames':group['frames'],'seconds':t,'hits':hits,'page':page};print(json.dumps({'observed':group['frames'],'hits':hits}),flush=True)
  if a.action=='advance'and t>=8 and t-lastkey>=1.1 and en[:2]==[3,9]and tr==0 and len(seen)<7:tap(45);lastkey=t
  if a.action=='depart'and not departed and t>2:
   assert en[0]==3 and en[1]==4 and tr==0, 'Stage selection not ready'
   tap(45);lastkey=t;departed=True
  samples+=1;time.sleep(.015)
finally:proc.close()
report={'session':str(a.session),'bin_sha256':rec['bin_sha256'],'fresh_boot_from_memory_card':True,'F1_F3_used':False,'process_memory_written':False,'composition_resident':True,'texture_rows_verified':144,'palette_verified':True,'samples':samples,'seconds':time.monotonic()-start,'observed_appearances':list(seen.values()),'events':events,'states':states,'trace':trace,'scope':'entire opaque body exact native framebuffer match; identical frames grouped'}
(a.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'output':str(a.output),'groups_seen':list(seen),'states':states[-3:]}))
