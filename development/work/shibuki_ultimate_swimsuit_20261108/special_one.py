"""정상 키 조작과 읽기 전용 RAM/VRAM으로 수정 모션을 검증한다."""
from pathlib import Path
import sys,json,time,ctypes,struct,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import sha,write
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess,identify
import scripts.emulator_session as control
from scripts.c01_audio_build import read_disc
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import framebuffer
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--vram',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
rec=json.loads((a.session/'session.local.json').read_text('utf8'));mode='ver_rin_nana' if 'ver_rin_nana' in a.session.as_posix() else 'ver_buki_riko';assert rec['bin_sha256']==json.loads((H/'build.json').read_text('utf8'))['sha256']
if mode=='ver_rin_nana':control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
assets,_=read_disc(Path(rec['cue']).with_suffix('.bin'),['SLUS_005.61','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'])
proc=ReadOnlyProcess(rec);out=a.output;assert not out.exists();out.mkdir(parents=True)
for at in (0x1540c,0x15ecc,0x233c8):assert proc.read(a.ram+at,48)==assets['SLUS_005.61'][at-0x10000+2048:at-0x10000+2096]
deadline=time.monotonic()+20
while proc.read(a.ram+0x1721c0,1)[0]!=6:
 assert time.monotonic()<deadline,'Gameplay not ready';time.sleep(.1)
while proc.read(a.ram+0x1418c8+0x47,1)[0] not in (0,115,116,117,118,119):
 assert time.monotonic()<deadline,'Arrival not finished';time.sleep(.04)
ram=proc.read(a.ram,0x200000);found=[r for r in identify(ram,assets) if r[4]];assert len(found)==1
name,es,addresses,candidates,matched=found[0];character=ram[0x1418ca];assert character in (0,1)
assert name=='PL02_U.ARC' and ram[0x1721f7]==1
owned_armor=ram[0x172207];visual_mask=15 if owned_armor==0 else 0
user,hwnd=control.checked_window(rec['pid']);user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.1);assert user.GetForegroundWindow()==hwnd
plan=[(46,.3,.5),(46,1.2,4.5)]

events=[];held={};seen={};cache={};captures=[];start=time.monotonic();frames=[];last_capture=-1
def setkey(scan,down):
 e=control.Input();e.type=1;e.data.key=control.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0);assert user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
try:
 while time.monotonic()-start<6.0:
  now=time.monotonic()-start;assert user.GetForegroundWindow()==hwnd,'Focus changed; release keys'
  keys={scan for scan,s,e in plan if s<=now<e}
  for scan in set(held)-keys:setkey(scan,False);del held[scan];events.append([now,scan,'up'])
  for scan in keys-set(held):setkey(scan,True);held[scan]=True;events.append([now,scan,'down'])
  pl=proc.read(a.ram+0x1418c8,228);ptr=struct.unpack_from('<II',pl,0x38);match=[v for v in candidates if ptr==v[2:]]
  if not match:time.sleep(.006);continue
  gb,pb,_,_=match[0];n=pl[0x47];tag=(gb,n,pl[0x15]&64)
  if tag not in seen:seen[tag]={'bank':gb,'frame':n,'facing':tag[2],'weapon':pl[0x93],'verified':False,'samples':0}
  if not seen[tag]['verified']:
   if (gb,n) not in cache:
    f=graphics_bank(es[2],gb,allow_bank_aliases=True)['frames'][n];cache[gb,n]=(f,decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
   f,want=cache[gb,n];buf=proc.read(a.ram+0x16dea8,len(want));gpu=bytearray()
   for first in range(0,f['tile_count'],16):
    for y in range(16):gpu+=proc.read(a.vram+(first//16*16+y)*2048+640,min(16,f['tile_count']-first)*8)
   again=proc.read(a.ram+0x1418c8,228);seen[tag]['samples']+=1
   if again[0x38:0x4a]==pl[0x38:0x4a] and buf==want and bytes(gpu)==want:
    seen[tag]['verified']=True;v=proc.read(a.vram,1048576)
    for y in (0,240):framebuffer(v,0,y).save(out/f'b{gb}_{n:03}_{tag[2]}_page{y}.png')
    captures.append(tag)
  if now-last_capture>.08:
   v=proc.read(a.vram,1048576);frames.append(framebuffer(v,0,0).resize((640,480),Image.Resampling.NEAREST));last_capture=now
  time.sleep(.006)
finally:
 for scan in held:setkey(scan,False)
 proc.close()
report={'project':mode,'bin_sha256':rec['bin_sha256'],'session':a.session.as_posix(),'archive':name,'archive_sha256':sha(assets[name]),'character':character,'engine_owned_armor':owned_armor,'ultimate':1,'visual_mask':visual_mask,'resident_entries_exact':True,'events':events,'frames':list(seen.values()),'memory_written':False,'saves_written':False,'scope':'관측 프레임의 실제 디코드 RAM 및 VRAM 업로드 검증. 실기 GIF는 페이지0 표본이며 모든 60Hz 프레임 녹화가 아님.'}
write(out/'report.json',report)
if frames:frames[0].save(out/'live.gif',save_all=True,append_images=frames[1:],duration=80,loop=0)
print(json.dumps({'archive':name,'verified':[(r['bank'],r['frame'],r['facing']) for r in seen.values() if r['verified']],'unverified':[(r['bank'],r['frame']) for r in seen.values() if not r['verified']]}))
