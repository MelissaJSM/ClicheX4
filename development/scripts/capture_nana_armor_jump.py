"""검증된 나나 아머 세션에서 수직 점프 한 번의 실제 F1을 보존한다."""
import argparse,ctypes,gzip,json,shutil,sys,time,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.project import digest

def capture(session,out,shoot=False):
    session,out=session.resolve(),out.resolve();require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions'),'Session outside project')
    record=json.loads((session/'session.local.json').read_text('utf8'));build=Path(record['cue']).parent
    require(out.is_relative_to(build) and not out.exists(),'Fresh build evidence folder required')
    m=json.loads((build/'manifest.json').read_text('utf8'));require(m['task']=='fourth_armor_nana' and digest(build/'rin_nana.bin')==record['bin_sha256']==m['modified_bin']['sha256'],'Build/session mismatch')
    state=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';before=state.read_bytes();player=gzip.decompress(before)[442+0x1418c8:442+0x1418c8+0xe4]
    require(player[2]==0 and player[0xa7]==15 and player[0x17]==5,'Expected saved full-armor idle')
    em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';user,hwnd=em.checked_window(record['pid'])
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as k:pad=list(map(int,winreg.QueryValueEx(k,'Pad1')[0].split(',')))
    require(len(pad)==16,'Unexpected pad layout');jump,fire=pad[6],pad[7]
    out.mkdir();(out/'before.000').write_bytes(before);held=set();events=[]
    def key(scan,down):
        if down:require(user.GetForegroundWindow()==hwnd,'Focus lost; stop input')
        e=em.Input();e.type=1;e.data.key=em.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0)
        require(user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1,'Input failed')
        events.append({'scan':scan,'down':down,'seconds':round(time.monotonic()-start,4)})
        if down:held.add(scan)
        else:held.discard(scan)
    start=time.monotonic()
    try:
        key(jump,True);time.sleep(.09)
        if shoot:key(fire,True)
        time.sleep(.08)
        if shoot:key(fire,False)
        key(0x3b,True);time.sleep(.06);key(0x3b,False);time.sleep(.09);key(jump,False)
        time.sleep(.25);saved=state.read_bytes();require(saved!=before,'F1 did not update');(out/'captured.000').write_bytes(saved)
        p=gzip.decompress(saved)[442+0x1418c8:442+0x1418c8+0xe4]
        require(p[2]==0 and p[0xa7]==15 and 33<=p[0x47]<=54,'Captured frame is outside airborne scope')
        time.sleep(.9);key(0x3b,True);time.sleep(.06);key(0x3b,False);time.sleep(.2)
        shutil.copyfile(state,out/'after.000')
        report={'session':session.relative_to(ROOT).as_posix(),'build':build.relative_to(ROOT).as_posix(),'frame':p[0x47],'animation':p[0x17],'shoot':shoot,'events':events,'pad1':pad,'before_sha256':digest(out/'before.000'),'captured_sha256':digest(out/'captured.000'),'state_edits':False,'evidence':'ordinary key input after graphics-refreshed F3; not fresh disc asset loading'}
        write(out/'capture.json',report);print(json.dumps(report))
    finally:
        for scan in list(held):key(scan,False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--shoot',action='store_true');a=p.parse_args();capture(a.session,a.output,a.shoot)
