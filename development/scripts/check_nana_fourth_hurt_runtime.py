"""근처 적에게 일반 점프/이동을 한 번 수행하고 읽기 전용 관찰 후 진행을 복원한다."""
import argparse,ctypes,gzip,json,sys,threading,time,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.observe_nana_armor_hurt_palette import observe
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.project import digest

def check(session,discovery,out):
    session,discovery,out=session.resolve(),discovery.resolve(),out.resolve()
    require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions'),'Unexpected session')
    rec=json.loads((session/'session.local.json').read_text('utf8'));build=Path(rec['cue']).parent
    require(out.is_relative_to(build) and not out.exists(),'Fresh evidence required')
    require(digest(build/'rin_nana.bin')==rec['bin_sha256'],'BIN changed')
    state=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';before=state.read_bytes();p=gzip.decompress(before)[442+0x1418c8:442+0x1418c8+0xe4]
    require(p[2]==0 and p[0xa7]==15 and p[0x17]==5,'Full armor idle required')
    em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';user,hwnd=em.checked_window(rec['pid'])
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as key:pad=list(map(int,winreg.QueryValueEx(key,'Pad1')[0].split(',')))
    require(len(pad)==16,'Unknown controls');left,jump=pad[0],pad[6]
    out.mkdir();(out/'before.000').write_bytes(before);events=[];held=set();start=time.monotonic();errors=[]
    def send(scan,down):
        if down:require(user.GetForegroundWindow()==hwnd,'Focus lost')
        event=em.Input();event.type=1;event.data.key=em.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0)
        require(user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))==1,'Input failed');events.append([round(time.monotonic()-start,4),scan,down])
        if down:held.add(scan)
        else:held.discard(scan)
    def monitor():
        try:observe(session,discovery,8)
        except Exception as e:errors.append(repr(e))
    thread=threading.Thread(target=monitor)
    try:
        thread.start();time.sleep(1.0);require(not errors,'Observer failed')
        send(left,True);send(jump,True);time.sleep(.3);send(jump,False);send(left,False)
        thread.join(timeout=12);require(not thread.is_alive(),'Observation exceeded deadline');require(not errors,'Observation failed: '+str(errors))
    finally:
        for scan in list(held):send(scan,False)
        state.write_bytes(before);send(0x3d,True);time.sleep(.06);send(0x3d,False);time.sleep(.3)
        write(out/'control.json',{'session':session.relative_to(ROOT).as_posix(),'discovery':discovery.relative_to(ROOT).as_posix(),'events':events,'pad1':pad,'before_hp':p[0x5c],'before_sha256':digest(out/'before.000'),'checkpoint_restored_exact':state.read_bytes()==before,'process_memory_written':False,'observation_errors':errors,'evidence':'ordinary jump into nearby enemy after graphics-refreshed checkpoint; not fresh disc loading'})
    print(json.dumps({'restored':state.read_bytes()==before,'events':len(events)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--discovery',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();check(a.session,a.discovery,a.output)
