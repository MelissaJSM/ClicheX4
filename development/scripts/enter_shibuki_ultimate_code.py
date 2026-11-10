"""미국판 선택 화면에서 원래 얼티밋 커맨드 입력 및 RAM 읽기 검증."""
import argparse, ctypes, json, sys, time, winreg
from datetime import datetime, timezone
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window, Input, KeyInput
from scripts.capture_poc_memory import Region
from scripts.project import write_json

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path,nargs='?')
    parser.add_argument('--existing-pid',type=int,help='User-requested input in the provided original ePSXe instance')
    parser.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'))
    args=parser.parse_args()
    import scripts.emulator_session as session_control
    if args.existing_pid is not None:
        if args.session is not None or args.project is None or args.existing_pid<=0:
            parser.error('Existing PID requires project and no managed session')
        project=args.project
        session_control.EMULATOR=ROOT/'ePSXe2018/ePSXe.exe'
        # checked_window still checks the exact executable path/hash, PID and unique game window.
        checked_window(args.existing_pid)
        session=ROOT/'work'/project/'native_command_requests'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        session.mkdir(parents=True)
        info={'pid':args.existing_pid,'bin_sha256':None,'managed_session':False,
              'executable':str(session_control.EMULATOR),
              'source_bin_verified':False,'source_bin_note':'Registry path is not proof of mounted disc'}
        write_json(session/'request.local.json',info)
    else:
        if args.session is None:parser.error('Session or existing PID required')
        session=args.session.resolve()
        projects=[p for p in ('ver_buki_riko','ver_rin_nana') if session.is_relative_to(ROOT/'work'/p/'emulator_sessions')]
        if len(projects)!=1:raise ValueError('Unexpected session')
        project=projects[0]
        if project=='ver_rin_nana':session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
        info=json.loads((session/'session.local.json').read_text())
    output=session/'ultimate_native_command.json'
    if output.exists():raise ValueError('Already attempted in this session; inspect evidence first')
    user,hwnd=checked_window(info['pid'])
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,info['pid'])
    if not handle:raise OSError('Cannot read process')
    def read(address,size):
        buf=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,address,buf,size,ctypes.byref(got)):return b''
        return buf.raw[:got.value]
    trace=[];held=set();result={'project':project,'pid':info['pid'],'process_memory_written':False,'source_bin_sha256':info['bin_sha256']}
    def key(sc,down):
        if down and user.GetForegroundWindow()!=hwnd:raise RuntimeError('Focus changed')
        ev=Input();ev.type=1;ev.data.key=KeyInput(0,sc&127,8|int(bool(sc&128))|(0 if down else 2),0,0)
        if user.SendInput(1,ctypes.byref(ev),ctypes.sizeof(ev))!=1:raise OSError('Input failed')
        if down:held.add(sc)
        else:held.discard(sc)
    try:
        anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100');address=0;candidates=set()
        exe=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes()
        while address<0x100000000:
            region=Region()
            if not kernel.VirtualQueryEx(handle,address,ctypes.byref(region),ctypes.sizeof(region)):break
            start=region.base or 0;end=start+region.size
            if end<=address:break
            if region.state==0x1000 and not region.protect&0x100 and region.protect&0xff in (2,4,8,0x20,0x40,0x80):
                for offset in range(start,end,1048576):
                    blob=read(offset,min(1048576+64,end-offset));pos=blob.find(anchor)
                    while pos>=0:
                        base=offset+pos-0x11a2f8
                        if base>=0 and read(base+0x29a48,64)==exe[0x29a48-0x10000+2048:0x29a48-0x10000+2048+64]:candidates.add(base)
                        pos=blob.find(anchor,pos+1)
            address=end
        if len(candidates)!=1:raise ValueError(f'Expected one verified US RAM, got {candidates}')
        base=candidates.pop();result['ram_host_address']=base
        result['boss_voice_branch_runtime_hex']=read(base+0x921f8,4).hex()
        result['existing_original_instance']=args.existing_pid is not None
        def observe(label):
            e=read(base+0x1721c0,0x64)
            if len(e)!=0x64:raise OSError('Engine read failed')
            row={'label':label,'state':e[0],'substate':e[1],'character':e[0x43],'phase':e[0x2a],'index':e[0x2b],'ultimate':e[0x37],'armor':e[0x47],'engine_hex':e.hex()};trace.append(row);return row
        before=observe('before')
        if (before['state'],before['substate'],before['character'],before['ultimate'])!=(1,3,0,0):raise ValueError('Expected unactivated X selection screen')
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
        if len(pad)!=16:raise ValueError('Unexpected pad settings')
        result['pad1']=pad
        user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.2)
        for i,sc in enumerate([pad[5]]*2+[pad[0]]*6):
            key(sc,True);time.sleep(.14);key(sc,False);time.sleep(.18);row=observe(f'input_{i+1}')
            if row['phase']!=(1 if i<7 else 2) or row['index']!=i+1:raise RuntimeError(f'Command sequence rejected at {i+1}: {row}')
        key(pad[8],True);key(pad[11],True);time.sleep(.2)
        key(pad[12],True);time.sleep(.14);key(pad[12],False);time.sleep(.2)
        after=observe('confirmed')
        result['activated']=after['ultimate']==1
        if not result['activated']:raise RuntimeError('Ultimate flag was not activated')
        time.sleep(4)
        observe('after_transition')
    finally:
        for sc in list(held):key(sc,False)
        kernel.CloseHandle(handle)
        result['trace']=trace;write_json(output,result)
    print(json.dumps({'evidence':str(output),'activated':result.get('activated',False),'ram_host_address':result.get('ram_host_address')}))

if __name__=='__main__':main()
