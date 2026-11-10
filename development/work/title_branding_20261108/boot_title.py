"""Fresh title-menu entry using normal keys and verified read-only RAM."""
from pathlib import Path
import argparse,ctypes,json,sys,time
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
from scripts.c01_audio_build import read_disc
import scripts.emulator_session as ctl
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
r=json.loads((a.session/'session.local.json').read_text('utf8'));exe=read_disc(Path(r['cue']).with_suffix('.bin'),['SLUS_005.61'])[0]['SLUS_005.61'];proc=ReadOnlyProcess(r)
if'ver_rin_nana'in str(a.session):ctl.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
for at in(0x1540c,0x15ecc,0x233c8):assert proc.read(a.ram+at,48)==exe[at-0x10000+2048:at-0x10000+2096]
u,hw=ctl.checked_window(r['pid']);u.ShowWindowAsync(hw,9);u.SetForegroundWindow(hw);time.sleep(.15)
events=[];states=[];start=time.monotonic();last=-9
def tap(scan):
 assert u.GetForegroundWindow()==hw
 e=ctl.Input();e.type=1;e.data.key=ctl.KeyInput(0,scan,8,0,0);u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))
 try:time.sleep(.07)
 finally:e.data.key.flags|=2;u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))
 events.append({'scan':scan,'time':time.monotonic()-start})
try:
 while time.monotonic()-start<40:
  g=proc.read(a.ram+0x173c70,16);e=proc.read(a.ram+0x1721c0,4);tr=proc.read(a.ram+0x141bdc,1)[0];s={'route':g[0],'mode':g[1],'cursor':g[2],'input_phase':g[13],'transition':tr,'engine':list(e)}
  if not states or states[-1]!=s:states.append(s)
  if g[0]==6 and g[1]==1 and tr==0:time.sleep(.7);break
  if time.monotonic()-last>1.5 and(g[0]==0 or g[0]==1 and g[13]==0 and tr==0):tap(53);last=time.monotonic()
  assert e[0]==0,'Refuse input outside boot/title'
  time.sleep(.03)
 else:raise TimeoutError('Title not ready')
finally:proc.close()
a.output.write_text(json.dumps({'session':str(a.session),'bin_sha256':r['bin_sha256'],'states':states,'events':events,'memory_written':False,'F1_F3_sent':False},indent=2)+'\n','utf8');print(json.dumps(states[-1]))
