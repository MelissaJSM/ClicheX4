"""검증된 나나 작업 창에 짧은 일반 키 계획만 재생한다."""
import argparse,ctypes,json,sys,time,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.emulator_probe import Input,KeyInput
from scripts.project import digest
from scripts.prepare_nana_fourth_pilot import require,write

def run(session,plan):
    session,plan=session.resolve(),plan.resolve();require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions') and any(plan.is_relative_to(ROOT/'work/ver_rin_nana'/folder) for folder in ('nana_fourth_armor','nana_ultimate_armor')),'Unexpected paths')
    s=json.loads((session/'session.local.json').read_text('utf8'));p=json.loads(plan.read_text('utf8'));pointer=json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf8'))
    require(s['bin_sha256']==p['bin_sha256']==pointer['sha256']==digest(Path(s['cue']).with_suffix('.bin')),'Build mismatch')
    keys={'left':203,'right':205,'jump':45,'fire':46,'dash':44};duration=p['seconds'];require(.1<=duration<=30,'Invalid duration')
    require(all(k in keys and 0<=a<b<=duration for k,a,b in p['keys']),'Unsupported input plan')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as k:pad=list(map(int,winreg.QueryValueEx(k,'Pad1')[0].split(',')))
    require([pad[i] for i in (0,1,6,7,5)]==list(keys.values()),'Pad mapping changed')
    em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';u,w=em.checked_window(s['pid']);held=set();pressed=set();events=[]
    def send(sc,down):
        e=Input();e.type=1;e.data.key=KeyInput(0,sc&127,8|int(sc>127)|(0 if down else 2),0,0)
        require(u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1,'Input failed')
        if down:pressed.add(sc)
        else:pressed.discard(sc)
    if u.GetForegroundWindow()!=w:send(0x38,True);send(0x38,False);u.SetForegroundWindow(w);time.sleep(.2)
    started=time.monotonic();failure=None
    try:
        while time.monotonic()-started<duration:
            require(u.GetForegroundWindow()==w,'Focus changed');t=time.monotonic()-started;wanted={k for k,a,b in p['keys'] if a<=t<b}
            for k in held-wanted:send(keys[k],False);events.append([round(t,4),k,False])
            for k in wanted-held:send(keys[k],True);events.append([round(t,4),k,True])
            held=wanted;time.sleep(.003)
    except Exception as e:failure=repr(e);raise
    finally:
        for sc in list(pressed):send(sc,False)
        out=session/('input_'+time.strftime('%Y%m%dT%H%M%S')+'.json');write(out,{'plan':plan.relative_to(ROOT).as_posix(),'bin_sha256':s['bin_sha256'],'pid':s['pid'],'events':events,'failure':failure,'process_memory_written':False,'save_files_written':False});print(json.dumps({'input_log':out.relative_to(ROOT).as_posix(),'failure':failure}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);a=p.parse_args();run(a.session,a.plan)
