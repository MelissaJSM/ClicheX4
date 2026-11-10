"""전용 린 세션에서 일반 키만으로 벽을 올라 베기1회를 재현한다."""
import argparse,ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as control
from scripts.emulator_session import Input,KeyInput,checked_window
from scripts.project import digest,new_run,write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);a=p.parse_args()
    session=a.session.resolve();baseline=a.baseline.resolve()
    if not session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions') or not baseline.is_relative_to(ROOT/'work/ver_rin_nana/live_poc'):raise ValueError('Isolated Rin paths required')
    record=json.loads((session/'session.local.json').read_text());b=json.loads(baseline.read_text())
    if b['pid']!=record['pid'] or b['modified_bin_sha256']!=record['bin_sha256']:raise ValueError('Session/baseline mismatch')
    control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';user,hwnd=checked_window(record['pid'])
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
    if len(pad)!=16 or any(not 1<=v<=255 for v in pad):raise ValueError('Invalid pad')
    keys={k:pad[i] for k,i in {'right':1,'jump':6,'fire':7,'start':12}.items()}
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,record['pid'])
    if not handle:raise OSError('Read-only process open failed')
    def player():
        buf=ctypes.create_string_buffer(0xe4);n=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,b['ram_host_address']+0x1418c8,buf,len(buf),ctypes.byref(n)) or n.value!=len(buf):raise OSError('Short RAM read')
        return buf.raw
    def send(name,down):
        sc=keys[name];ev=Input();ev.type=1;ev.data.key=KeyInput(0,sc&127,8|int(bool(sc&128))|(0 if down else 2),0,0)
        if user.SendInput(1,ctypes.byref(ev),ctypes.sizeof(ev))!=1:raise OSError('Input failed')
    held=set();trace=[];out=new_run(ROOT,'ver_rin_nana','wall_probe');failure=None;attack_seen=False;attack_finished=False
    try:
        user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.15)
        start=time.monotonic();contact=False;last_jump=-10;jump_until=0;fire_until=0;shot=False;pause_until=None
        while time.monotonic()-start<18:
            t=time.monotonic()-start
            if user.GetForegroundWindow()!=hwnd:raise RuntimeError('Focus changed; input stopped')
            v=player();x,y=[struct.unpack_from('<i',v,k)[0]/65536 for k in (8,12)];anim=v[0x17];frame=v[0x47];hp=v[0x5c]&0x7f
            row=[round(t,4),anim,frame,round(x,3),round(y,3),hp,v[0x89]]
            if not trace or row[1:]!=trace[-1][1:]:trace.append(row)
            if v[2]!=1 or v[4]!=1 or hp>48:raise RuntimeError('Player no longer in expected live gameplay')
            if anim in (13,15):contact=True
            wanted={'right'} if t>=.3 else set()
            if not contact:
                if 1.5<=t<2.2 or 3.4<=t<4.1:wanted.add('jump')
            else:
                if anim in (13,15) and y>2290 and t-last_jump>.6:
                    jump_until=t+.12;last_jump=t
                if anim==15 and y<=2290 and not shot:
                    fire_until=t+.1;shot=True
                if t<jump_until:wanted.add('jump')
                if t<fire_until:wanted.add('fire')
                if anim==94:attack_seen=True
                if attack_seen and anim==15 and pause_until is None:
                    attack_finished=True;pause_until=t+.12
            if pause_until is not None:
                wanted={'start'} if t<pause_until else set()
            for k in held-wanted:send(k,False)
            for k in wanted-held:send(k,True)
            held=wanted
            if pause_until is not None and t>=pause_until:break
            time.sleep(.006)
    except BaseException as e:failure=repr(e);raise
    finally:
        for k in held:send(k,False)
        kernel.CloseHandle(handle)
        write_json(out/'probe.local.json',{'session':str(session),'baseline':str(baseline),'process_memory_written':False,'columns':['seconds','animation','frame','x','y','hp','collision_flags'],'trace':trace,'attack_seen':attack_seen,'attack_finished':attack_finished,'error':failure})
        print(json.dumps({'output':str(out),'attack_seen':attack_seen,'attack_finished':attack_finished,'error':failure,'last':trace[-1] if trace else None}))

if __name__=='__main__':main()
