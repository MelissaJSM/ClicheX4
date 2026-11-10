"""Enter the native US Black Zero code and verify it by read-only RAM checks."""
import ctypes, json, sys, time, winreg
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window, Input, KeyInput
from scripts.capture_poc_memory import Region
from scripts.project import write_json

def main():
    session=Path(sys.argv[1]).resolve()
    projects=[p for p in ('ver_buki_riko','ver_rin_nana') if session.is_relative_to(ROOT/'work'/p/'emulator_sessions')]
    if len(projects)!=1:raise ValueError('Unexpected session')
    project=projects[0]
    if project=='ver_rin_nana':
        import scripts.emulator_session as session_control
        session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    info=json.loads((session/'session.local.json').read_text())
    output=session/'black_zero_native_command.json'
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
                        if base>=0 and read(base+0x29bd8,64)==exe[0x29bd8-0x10000+2048:0x29bd8-0x10000+2048+64]:candidates.add(base)
                        pos=blob.find(anchor,pos+1)
            address=end
        if len(candidates)!=1:raise ValueError(f'Expected one verified US RAM, got {candidates}')
        base=candidates.pop();result['ram_host_address']=base
        def observe(label):
            e=read(base+0x1721c0,0x64)
            if len(e)!=0x64:raise OSError('Engine read failed')
            row={'label':label,'state':e[0],'substate':e[1],'character':e[0x43],'phase':e[0x2a],'index':e[0x2b],'special_mode':e[0x37],'armor':e[0x47],'engine_hex':e.hex()};trace.append(row);return row
        before=observe('before')
        if (before['state'],before['substate'],before['character'],before['special_mode'])!=(1,3,1,0):raise ValueError('Expected unactivated Zero selection screen')
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
        if len(pad)!=16:raise ValueError('Unexpected pad settings')
        result['pad1']=pad
        user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.2)
        # Hold R1, press Right six times, release all, then Circle+Start.
        expected_table=bytes.fromhex('00200020002000200020002020000000')
        if read(base+0xf44d8,16)!=expected_table:raise ValueError('Unexpected US Black Zero input table')
        key(pad[10],True);time.sleep(.18)
        for i in range(6):
            key(pad[1],True);time.sleep(.14);key(pad[1],False);time.sleep(.18);row=observe(f'right_{i+1}')
            if row['phase']!=(1 if i<5 else 2) or row['index']!=i+1:raise RuntimeError(f'Command sequence rejected at {i+1}: {row}')
        key(pad[10],False);time.sleep(.2)
        row=observe('all_released')
        if row['phase']!=3 or row['index']!=6:raise RuntimeError('Release phase rejected')
        key(pad[5],True);time.sleep(.2)
        key(pad[12],True);time.sleep(.14);key(pad[12],False);time.sleep(.2)
        after=observe('confirmed')
        result['activated']=after['special_mode']==1 and after['character']==1
        if not result['activated']:raise RuntimeError('Black Zero flag was not activated')
        time.sleep(4)
        observe('after_transition')
    finally:
        for sc in list(held):key(sc,False)
        kernel.CloseHandle(handle)
        result['trace']=trace;write_json(output,result)
    print(json.dumps({'evidence':str(output),'activated':result.get('activated',False),'ram_host_address':result.get('ram_host_address')}))

if __name__=='__main__':main()
