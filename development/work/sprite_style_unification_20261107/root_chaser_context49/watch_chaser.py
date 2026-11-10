"""Bounded ordinary stage entry and read-only bike/rider capture."""
from pathlib import Path
import argparse,ctypes,hashlib,json,struct,sys,time
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
import scripts.emulator_session as control
from scripts.prepare_riko_ui import entry
from src.epsxe_state import framebuffer
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--vram',type=int,required=True);p.add_argument('--name',required=True);p.add_argument('--character',choices=['nana','rin','shibuki','riko'],default='nana');a=p.parse_args()
assert a.name.isidentifier();out=O/a.name;assert not out.exists();out.mkdir()
rec=json.loads((a.session/'session.local.json').read_text('utf8'));is_br=a.character in ('shibuki','riko');assert rec['bin_sha256']==('ad4f2ceab100098e88977f383d314efd0337379feb70999989eaa53926332516'if is_br else 'e751a82bc3d1e228d26389d911ca4b46efa12612dcea69b6c99fdeb3ba3ca637')
if not is_br:control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
is_zero=a.character in ('rin','riko');src=json.loads((W/('staging_br_v31.json'if is_br else 'staging_rn_v43.json')).read_text('utf8'))['resources']['PL01_U.ARC' if is_zero else 'PL00_U.ARC'];arc=(ROOT/src['path']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==src['after'];es={k:entry(arc,k)for k in(2,3,9)}
proc=ReadOnlyProcess(rec);assert proc.read(a.ram+0x1721c0,4)==bytes([3,4,0,4]),'Require Marine Base selected'
user,hwnd=control.checked_window(rec['pid']);user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.1)
held=set();events=[];trace=[];samples=[];counts={};start=time.monotonic();first=None;last=None;lastshot=0;error=None;paused=False;ramfirst=None
def tap(scan):
    assert user.GetForegroundWindow()==hwnd
    e=control.Input();e.type=1;e.data.key=control.KeyInput(0,scan&127,8|int(bool(scan&128)),0,0);assert user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1;held.add(scan)
    try:time.sleep(.07)
    finally:e.data.key.flags|=2;user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e));held.discard(scan)
    events.append({'seconds':time.monotonic()-start,'scan':scan})
try:
    tap(45)
    while time.monotonic()-start<25:
        assert user.GetForegroundWindow()==hwnd
        en=proc.read(a.ram+0x1721c0,100);pl=proc.read(a.ram+0x1418c8,228);bike=proc.read(a.ram+0x173a30,228);state=(en[0],en[1],pl[0x17],pl[0x47],bike[0x47]);now=time.monotonic()
        if state!=last:trace.append({'t':now-start,'state':state,'stage':en[12],'hp':pl[0x5c]});last=state
        if en[0]==6 and en[12]==5 and pl[2]==int(is_zero) and (0<=pl[0x47]<=38 if is_zero else 162<=pl[0x47]<=174):
            if first is None:first=now
            key=(pl[0x47],bike[0x47])
            if now-first>2.2 and counts.get(key,0)<3 and now-lastshot>.04 and len(samples)<32:
                ram=proc.read(a.ram,2097152);video=proc.read(a.vram,1048576);idx=len(samples)
                if ramfirst is None:
                    ramfirst=ram;assert all(ram.find(v)>=0 for v in es.values()),'Current resources not resident';(out/'ram.bin').write_bytes(ram)
                (out/f'vram{idx:02}.bin').write_bytes(video)
                samples.append({'t':now-start,'player_hex':ram[0x1418c8:0x1418c8+228].hex(),'bike_hex':ram[0x173a30:0x173a30+228].hex(),'frame_before':key,'frame_after':proc.read(a.ram+0x1418c8+0x47,1)[0],'vram_sha256':sha(video)})
                counts[key]=counts.get(key,0)+1;lastshot=now
            if now-first>2.5 and len(events)==1:tap(46)
            if now-first>3.3 and len(events)==2:tap(45)
            if now-first>5:break
        if en[0]==6 and first is not None and (pl[0x5c]&127)==0:raise RuntimeError('HP exhausted')
        time.sleep(.005)
    if proc.read(a.ram+0x1721c0,2)==bytes([6,0]):
        tap(53);time.sleep(.6);paused=proc.read(a.ram+0x1721c0,2)==bytes([6,2])
except Exception as e:error=str(e)
finally:
    proc.close()
report={'session':a.session.as_posix(),'character':a.character,'script_sha256':sha(Path(__file__).read_bytes()),'bin_sha256':rec['bin_sha256'],'events':events,'trace':trace,'samples':samples,'paused_after':paused,'error':error,'memory_written':False,'F1_F3_sent':False,'actually_viewed':False}
(out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'output':str(out),'samples':len(samples),'pairs':list(counts),'paused':paused,'error':error}))
if error:raise RuntimeError(error)
