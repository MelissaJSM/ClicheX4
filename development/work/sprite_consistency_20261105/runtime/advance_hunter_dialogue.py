"""Bounded ordinary Cross taps; stop before stage selection becomes interactive."""
import ctypes,json,sys,time,winreg
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess,load
import scripts.emulator_session as c
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261105T113936662598Z'
rec,game,assets=load(session,'ver_rin_nana');p=ReadOnlyProcess(rec);base=17374752
c.EMULATOR=Path(rec['executable'])
exe=assets['SLUS_005.61']
for off in (0x1540c,0x15ecc,0x233c8,0x23400,0xea20c):
    assert p.read(base+off,48)==exe[off-0x10000+2048:off-0x10000+2096]
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:
    keys=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')));assert keys[6]==0x2d
u,h=c.checked_window(rec['pid']);u.ShowWindowAsync(h,9);u.SetForegroundWindow(h);time.sleep(.2)
trace=[];start=time.monotonic();pressed=False
try:
    while time.monotonic()-start<30:
        e=p.read(base+0x1721c0,4);fade=p.read(base+0x141bdc,1)[0]
        if e[0]!=3 or e[1]==4:break
        if fade:time.sleep(.1);continue
        assert u.GetForegroundWindow()==h,'Focus changed'
        event=c.Input();event.type=1;event.data.key=c.KeyInput(0,0x2d,8,0,0)
        assert u.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))==1;pressed=True
        time.sleep(.12);event.data.key.flags|=2
        assert u.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))==1;pressed=False
        trace.append({'at':time.monotonic()-start,'engine':list(e),'button':'Cross/X'});time.sleep(.65)
finally:
    if pressed:
        event.data.key.flags|=2;u.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))
    end=list(p.read(base+0x1721c0,4));p.close()
report={'session':str(session.relative_to(ROOT)),'pid':rec['pid'],'trace':trace,'end_engine':end,
    'stopped_before_stage_choice':end[:2]==[3,4],'process_memory_written':False,'save_keys_sent':False}
out=ROOT/'work/sprite_consistency_20261105/runtime/rin_dialogue.json'
with out.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report))
