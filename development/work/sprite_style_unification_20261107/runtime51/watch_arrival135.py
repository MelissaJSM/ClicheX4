"""일반 결정 키 후 짧은135의 RAM/VRAM을 빠르게 읽는다. 메모리 쓰기 없음."""
from pathlib import Path
import argparse,ctypes,hashlib,json,struct,sys,time
from PIL import Image,ImageDraw
import numpy as np
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
from scripts.emulator_session import checked_window,Input,KeyInput
import scripts.emulator_session as control
# Use the authenticated first-mode emulator from its existing module.
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import framebuffer

p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--vram',type=int,required=True);p.add_argument('--name',required=True);p.add_argument('--skip-nonstage-start',action='store_true');a=p.parse_args()
assert a.name.isidentifier();out=O/a.name;assert not out.exists();out.mkdir()
rec=json.loads((a.session/'session.local.json').read_text('utf8'));assert rec['bin_sha256']=='677cb525c64e4684ff1daf22d7d52905c9e9f1a0967e015363e038ecc9f60e6d'
plan=json.loads((W/'staging_br_v32.json').read_text('utf8'));src=plan['resources']['PL02_U.ARC'];arc=(ROOT/src['path']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==src['after']
es={k:entry(arc,k)for k in(2,3,9)};f=graphics_bank(es[2],0,allow_bank_aliases=True)['frames'][135];decoded=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data
proc=ReadOnlyProcess(rec);user,hwnd=checked_window(rec['pid']);user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.15);assert user.GetForegroundWindow()==hwnd
trace=[];samples=[];stored=[];start=time.monotonic();held=set();events=[];last=None;first_hit=None;last_skip=start
def key(scan,down):
    e=Input();e.type=1;e.data.key=KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0)
    assert user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
    (held.add if down else held.discard)(scan);events.append({'t':round(time.monotonic()-start,5),'scan':scan,'down':down})
try:
    key(45,True);time.sleep(.08);key(45,False)
    while time.monotonic()-start<25:
        assert user.GetForegroundWindow()==hwnd,'Game lost focus'
        player=proc.read(a.ram+0x1418c8,228);engine=proc.read(a.ram+0x1721c0,0x64)
        frame=player[0x47];state=(engine[0],engine[1],player[0x17],frame,player[0xa7])
        if state!=last:trace.append({'t':round(time.monotonic()-start,5),'engine':list(engine[:4]),'character':player[2],'animation':player[0x17],'frame':frame,'armor':player[0xa7],'hp':player[0x5c]});last=state
        if a.skip_nonstage_start and tuple(engine[:2])==(3,9) and time.monotonic()-last_skip>1:
            key(45,True);time.sleep(.06);key(45,False);last_skip=time.monotonic()
        if a.skip_nonstage_start and engine[0]!=6 and time.monotonic()-last_skip>3:
            key(53,True);time.sleep(.06);key(53,False);last_skip=time.monotonic()
        if engine[0]==6 and player[2]==0 and frame==135 and len(stored)<10:
            ram=proc.read(a.ram,2097152);video=proc.read(a.vram,1048576)
            if first_hit is None:first_hit=time.monotonic()
            stamp={'t':round(time.monotonic()-start,5),'frame_before':frame,'frame_after':proc.read(a.ram+0x1418c8+0x47,1)[0],'armor':player[0xa7]}
            if not stored or sha(video)!=sha(stored[-1][2]):stored.append((stamp,ram,video))
        if first_hit is not None and time.monotonic()-first_hit>.4:
            key(53,True);time.sleep(.08);key(53,False);break
        time.sleep(.002)
finally:
    for scan in list(held):key(scan,False)
    proc.close()

for i,(stamp,ram,video)in enumerate(stored):
    addrs={k:ram.find(data)for k,data in es.items()}
    assert all(at>=0 and ram.find(es[k],at+1)<0 for k,at in addrs.items()),'Current resident assets differ'
    raw=bytearray()
    for first in range(0,f['tile_count'],16):
        width=min(16,f['tile_count']-first)*8
        for y in range(16):
            pos=(first//16*16+y)*2048+640;raw.extend(video[pos:pos+width])
    stamp.update(resident_entries={str(k):{'address':hex(at|0x80000000),'size':len(es[k]),'sha256':sha(es[k])}for k,at in addrs.items()},active_decode_matches=ram[0x16dea8:0x16dea8+len(decoded)]==decoded,gpu_upload_matches=bytes(raw)==decoded,ram_sha256=sha(ram),vram_sha256=sha(video),display_environment=ram[0x166c10:0x166c10+32].hex())
    for py in(0,240):framebuffer(video,0,py).resize((640,480),Image.Resampling.NEAREST).save(out/f'capture{i:02}_page{py}.png')
    if i==0:(out/'ram.bin').write_bytes(ram)
    (out/f'vram{i:02}.bin').write_bytes(video);samples.append(stamp)
report={'session':a.session.as_posix(),'bin_sha256':rec['bin_sha256'],'events':events,'trace':trace,'samples':samples,'flash135_observed':bool(samples),'memory_written':False,'F1_F3_sent':False,'max_seconds':25,'read_poll_interval_seconds':.002,'actually_viewed':False}
(out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'output':str(out),'samples':len(samples),'decoded_matches':sum(x['active_decode_matches']for x in samples),'GPU_matches':sum(x['gpu_upload_matches']for x in samples),'last_state':trace[-1]if trace else None}))
