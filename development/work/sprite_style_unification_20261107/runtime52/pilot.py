"""최신 RN44의 일반 입력과 사다리 표본. 프로세스 메모리는 읽기만 한다."""
from pathlib import Path
import argparse,ctypes,json,struct,sys,time,hashlib
from PIL import ImageGrab,Image
from ctypes import wintypes
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
import scripts.emulator_session as ctl
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import framebuffer
ctl.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--vram',type=int,required=True);p.add_argument('--name',required=True);p.add_argument('--keys',nargs='*',default=[]);p.add_argument('--seconds',type=float,default=.5);p.add_argument('--pulse-jump',action='store_true');a=p.parse_args()
assert a.name.isidentifier()and 0<a.seconds<=15;out=O/a.name;assert not out.exists();out.mkdir();rec=json.loads((a.session/'session.local.json').read_text('utf8'));assert rec['bin_sha256']=='3c05824c27f9d78822aa88d3c1c231768a986ab631d6c1e4ed7c3b725bd2f3c1';proc=ReadOnlyProcess(rec)
src=json.loads((W/'staging_rn_v44.json').read_text('utf8'))['resources']['PL02_U.ARC'];arc=(ROOT/src['path']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==src['after'];entries={k:entry(arc,k)for k in(2,3,9)};bank=graphics_bank(entries[2],0,allow_bank_aliases=True)
keys={'left':203,'right':205,'up':200,'down':208,'jump':45,'dash':44,'fire':46};assert all(k in keys for k in a.keys)
u,hw=ctl.checked_window(rec['pid']);u.ShowWindowAsync(hw,9);u.SetForegroundWindow(hw);time.sleep(.15);assert u.GetForegroundWindow()==hw
held=set();trace=[];samples=[];buffers=[];start=time.monotonic();last=None;counts={};resident=None;last_sample={}
def press(scan,down):
 e=ctl.Input();e.type=1;e.data.key=ctl.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0);assert u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1;(held.add if down else held.discard)(scan)
def tap(scan):press(scan,True);time.sleep(.06);press(scan,False)
def state():
 pl=proc.read(a.ram+0x1418c8,228);en=proc.read(a.ram+0x1721c0,100)
 return pl,en,{'engine':list(en[:4]),'stage':en[12],'area':en[13],'frame':pl[0x47],'animation':pl[0x17],'hp':pl[0x5c],'world':[struct.unpack_from('<i',pl,x)[0]/65536 for x in(8,12)],'armor':pl[0xa7],'ultimate':en[0x37]}
try:
 pl,en,initial=state();assert en[0]==6,'Require ordinary stage'
 if en[1]==2:
  time.sleep(.6);tap(53);deadline=time.monotonic()+4
  while state()[1][1]!=0 and time.monotonic()<deadline:time.sleep(.03)
 assert state()[1][1]==0,'Require unpaused play'
 for k in a.keys:press(keys[k],True)
 start=time.monotonic()
 while time.monotonic()-start<a.seconds:
  assert u.GetForegroundWindow()==hw
  if a.pulse_jump and 'jump'in a.keys:
   wanted=(time.monotonic()-start)%.3<.16
   if wanted!=(45 in held):press(45,wanted)
  pl,en,s=state();n=s['frame'];sig=(n,s['animation'],s['hp'],s['engine'][1]);t=time.monotonic()-start
  if sig!=last:trace.append({'time':round(t,4),**s});last=sig
  if en[0]!=6 or s['hp']==0:break
  if n in(*range(143,156),183)and counts.get(n,0)<4 and t-last_sample.get(n,-1)>.03:
   ram=proc.read(a.ram,2097152)if resident is None else None;v=proc.read(a.vram,1048576);f=bank['frames'][n];expected=decode_stream(entries[2],f['offset'],f['limit'],f['tile_count']*128).data;raw=bytearray()
   for first in range(0,f['tile_count'],16):
    width=min(16,f['tile_count']-first)*8
    for y in range(16):pos=(first//16*16+y)*2048+640;raw.extend(v[pos:pos+width])
   if resident is None:
    resident={str(k):{'offset':ram.find(data),'full_match':ram.find(data)>=0,'sha256':sha(data)}for k,data in entries.items()};assert all(x['full_match']for x in resident.values());(out/'ram.bin').write_bytes(ram)
   post=proc.read(a.ram+0x1418c8+0x47,1)[0];sample={'index':len(samples),'time':round(t,4),**s,'frame_after':post,'player':pl.hex(),'native_decode_exact':proc.read(a.ram+0x16dea8,len(expected))==expected,'gpu_exact':bytes(raw)==expected,'vram_sha256':sha(v),'display_env':proc.read(a.ram+0x166c10,32).hex()};samples.append(sample);buffers.append(v);counts[n]=counts.get(n,0)+1;last_sample[n]=t
  time.sleep(.004)
 for k in list(held):press(k,False)
 time.sleep(.12);pl,en,final=state();video=proc.read(a.vram,1048576)
 for page in(0,240):framebuffer(video,0,page).resize((640,480),Image.Resampling.NEAREST).save(out/f'last_{page}.png')
 if en[0]==6 and en[1]==0:tap(53);time.sleep(.15)
 paused=state()[1][1]==2
finally:
 for k in list(held):press(k,False)
 proc.close()
for q,v in zip(samples,buffers):(out/f'vram{q["index"]:02}.bin').write_bytes(v)
report={'session':a.session.as_posix(),'bin_sha256':rec['bin_sha256'],'source_arc':src,'keys':a.keys,'seconds':a.seconds,'initial':initial,'final':final,'paused':bool(paused),'resident':resident,'samples':samples,'trace':trace,'memory_written':False,'F1_F3_sent':False};(out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'final':final,'samples':len(samples),'refs':sorted(counts),'paused':bool(paused)}))
