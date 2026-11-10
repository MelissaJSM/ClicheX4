"""인트로의 안전한 바닥 구간에서 일반 입력으로 저체력을 얻고 즉시 후퇴한다."""
from pathlib import Path
import argparse,ctypes,hashlib,json,struct,sys,time
from PIL import Image
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
import scripts.emulator_session as control
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import framebuffer
control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261108T031908550454Z';rec=json.loads((session/'session.local.json').read_text('utf8'));assert rec['bin_sha256']=='e751a82bc3d1e228d26389d911ca4b46efa12612dcea69b6c99fdeb3ba3ca637'
parser=argparse.ArgumentParser();parser.add_argument('--observe-only',action='store_true');args=parser.parse_args()
out=O/('rn43_lowhp_actual02' if args.observe_only else 'rn43_lowhp_actual01');assert not out.exists();out.mkdir();ram_base=17374752;vram_base=86265888
plan=json.loads((W/'staging_rn_v43.json').read_text('utf8'));src=plan['resources']['PL00_U.ARC'];arc=(ROOT/src['path']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==src['after'];es={k:entry(arc,k)for k in(2,3,9)}
frames=graphics_bank(es[2],0,allow_bank_aliases=True)['frames'];decoded={n:decode_stream(es[2],frames[n]['offset'],frames[n]['limit'],frames[n]['tile_count']*128).data for n in range(120,126)}
proc=ReadOnlyProcess(rec);user,hwnd=control.checked_window(rec['pid']);user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.15);assert user.GetForegroundWindow()==hwnd
events=[];trace=[];samples={};held=set();start=time.monotonic();phase='observe' if args.observe_only else 'approach';last=None;reason='timeout';idle_since=start if args.observe_only else None;initial_lives=proc.read(ram_base+0x172204,1)[0];last_ref=None;ref_since=start
def key(scan,down):
    e=control.Input();e.type=1;e.data.key=control.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0);assert user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
    (held.add if down else held.discard)(scan);events.append({'t':round(time.monotonic()-start,4),'scan':scan,'down':down})
def direction(want):
    for sc in(203,205):
        if sc in held and sc!=want:key(sc,False)
    if want is not None and want not in held:key(want,True)
def press(sc):key(sc,True);time.sleep(.06);key(sc,False)
try:
    eng=proc.read(ram_base+0x1721c0,0x64);assert tuple(eng[:2])==(6,2)and eng[12]==0
    press(53)
    while time.monotonic()-start<40:
        assert user.GetForegroundWindow()==hwnd,'Focus changed'
        p=proc.read(ram_base+0x1418c8,228);e=proc.read(ram_base+0x1721c0,0x64);x,y=(struct.unpack_from('<i',p,i)[0]/65536 for i in(8,12));hp=p[0x5c]&127;n=p[0x47]
        if n!=last_ref:last_ref=n;ref_since=time.monotonic()
        state=(phase,hp,p[0x17],n,int(x)//16,int(y)//16)
        if state!=last:trace.append({'t':round(time.monotonic()-start,4),'phase':phase,'hp':hp,'hp_raw':p[0x5c],'animation':p[0x17],'frame':n,'x':x,'y':y,'lives':e[0x44]});last=state
        if tuple(e[:2])!=(6,0):time.sleep(.004);continue
        if hp==0 or hp>32 or e[0x44]!=initial_lives or not(0<=x<=470 and 370<=y<=460):reason='safety_stop';break
        if phase in ('approach','wait')and hp<=9:phase='retreat'
        if phase=='approach':
            if x<408:direction(205)
            else:direction(None);phase='wait'
        elif phase=='wait':
            direction(205 if x<390 else None)
        elif phase=='retreat':
            if x>180:direction(203)
            else:direction(None);phase='observe';idle_since=time.monotonic()
        elif phase=='observe':
            direction(None)
            if n in decoded and n not in samples and time.monotonic()-ref_since>.025:
                rb=proc.read(ram_base,2097152);vb=proc.read(vram_base,1048576)
                raw=bytearray();tiles=frames[n]['tile_count']
                for first in range(0,tiles,16):
                    width=min(16,tiles-first)*8
                    for row in range(16):
                        pos=(first//16*16+row)*2048+640;raw.extend(vb[pos:pos+width])
                if rb[0x16dea8:0x16dea8+len(decoded[n])]==decoded[n]and bytes(raw)==decoded[n]:samples[n]=(rb,vb,{'hp':hp,'x':x,'y':y,'t':time.monotonic()-start})
            if len(samples)==6:reason='all_six_current_frames_observed';break
            if time.monotonic()-idle_since>8:reason='observation_limit';break
        time.sleep(.003)
finally:
    direction(None)
    if tuple(proc.read(ram_base+0x1721c0,2))==(6,0):press(53)
    for sc in list(held):key(sc,False)
    proc.close()
results=[]
for n,(rb,vb,meta)in sorted(samples.items()):
    addrs={k:rb.find(data)for k,data in es.items()};assert all(at>=0 and rb.find(es[k],at+1)<0 for k,at in addrs.items())
    for py in(0,256):framebuffer(vb,0,py).resize((640,480),Image.Resampling.NEAREST).save(out/f'ref{n:03}_page{py}.png')
    (out/f'vram_{n:03}.bin').write_bytes(vb)
    if not results:(out/'ram.bin').write_bytes(rb)
    results.append({'ref':n,**meta,'decode_equal':True,'gpu_upload_equal':True,'whole_current_entries_equal':{str(k):{'address':hex(at|0x80000000),'sha256':sha(es[k])}for k,at in addrs.items()},'ram_sha256':sha(rb),'vram_sha256':sha(vb)})
report={'session':session.relative_to(ROOT).as_posix(),'bin_sha256':rec['bin_sha256'],'stop_reason':reason,'events':events,'trace':trace,'samples':results,'F1_F3_sent':False,'memory_written':False,'user_save_modified':False,'max_seconds':40,'live_gameplay_observed':True,'actually_viewed':False}
(out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'stop_reason':reason,'frames':[q['ref']for q in results],'last':trace[-1]}))
