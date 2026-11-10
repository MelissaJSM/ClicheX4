"""벽 옆 대기 저장에서 짧게 벽 접촉·사격을 캡처하고 진행을 복원한다."""
import argparse,ctypes,gzip,json,sys,time,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.project import digest


def capture(session,out,shoot=False,motion='wall'):
    session,out=session.resolve(),out.resolve()
    require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions'),'Unexpected session')
    r=json.loads((session/'session.local.json').read_text('utf8'));build=Path(r['cue']).parent
    require(out.is_relative_to(build) and not out.exists(),'Fresh evidence path required')
    m=json.loads((build/'manifest.json').read_text('utf8'))
    require(m['task']=='fourth_armor_nana' and digest(build/'rin_nana.bin')==r['bin_sha256']==m['modified_bin']['sha256'],'Build mismatch')
    state=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';before=state.read_bytes()
    player=gzip.decompress(before)[442+0x1418c8:442+0x1418c8+0xe4]
    require(player[2]==0 and player[0xa7]==15 and player[0x17]==5,'Expected saved full armor idle')
    em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';user,hwnd=em.checked_window(r['pid'])
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as k:pad=list(map(int,winreg.QueryValueEx(k,'Pad1')[0].split(',')))
    require(len(pad)==16,'Unexpected pad layout');left,right,jump,fire,dash=pad[0],pad[1],pad[6],pad[7],pad[5]
    out.mkdir();(out/'before.000').write_bytes(before);held=set();events=[];samples=[];start=time.monotonic()
    def key(scan,down):
        if down:require(user.GetForegroundWindow()==hwnd,'Focus lost')
        e=em.Input();e.type=1;e.data.key=em.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0)
        require(user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1,'Input failed')
        events.append({'scan':scan,'down':down,'seconds':round(time.monotonic()-start,4)})
        if down:held.add(scan)
        else:held.discard(scan)
    def sample(name):
        key(0x3b,True);time.sleep(.06);key(0x3b,False);time.sleep(.12)
        data=state.read_bytes();(out/(name+'.000')).write_bytes(data);p=gzip.decompress(data)[442+0x1418c8:442+0x1418c8+0xe4]
        samples.append({'name':name,'frame':p[0x47],'animation':p[0x17],'armor':p[0xa7],'sha256':digest(out/(name+'.000'))})
    try:
        if motion=='wall':
            key(left,True);key(jump,True);time.sleep(.12);key(jump,False);time.sleep(.18)
        elif motion=='air_dash':
            key(right,True);time.sleep(.02);key(right,False)
            key(jump,True);time.sleep(.30);key(jump,False)
            key(dash,True);time.sleep(.02 if shoot else .10)
        elif motion=='ground_dash':
            key(left,True);time.sleep(.03);key(dash,True);time.sleep(.04)
        else:raise ValueError('Unsupported capture motion')
        if shoot:
            key(fire,True);time.sleep(.03 if motion!='wall' else .06);key(fire,False)
            if motion=='wall':time.sleep(.03)
        sample('shot' if shoot else motion)
    finally:
        for scan in list(held):key(scan,False)
        state.write_bytes(before);key(0x3d,True);time.sleep(.06);key(0x3d,False);time.sleep(.3)
        write(out/'capture.json',{'session':session.relative_to(ROOT).as_posix(),'build':build.relative_to(ROOT).as_posix(),'motion':motion,'samples':samples,'events':events,'pad1':pad,'before_sha256':digest(out/'before.000'),'checkpoint_restored_exact':state.read_bytes()==before,'state_gameplay_edits':False,'evidence':'ordinary controls after graphics-refreshed F3; not fresh disc loading'})
    print(json.dumps(samples))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--shoot',action='store_true');p.add_argument('--motion',choices=('wall','air_dash','ground_dash'),default='wall');a=p.parse_args();capture(a.session,a.output,a.shoot,a.motion)
