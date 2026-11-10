"""자연 피격을 짧게 포착한 뒤 진행을 복원한다. 프로세스 메모리는 읽기만 한다."""
import argparse,ctypes,gzip,json,sys,time,winreg
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.prepare_nana_fourth_pilot import require,entry,write
from scripts.project import digest

def capture(session,discovery,out):
    session,discovery,out=session.resolve(),discovery.resolve(),out.resolve()
    require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions') and discovery.is_relative_to(ROOT/'work/ver_rin_nana/live_poc'),'Unexpected sources')
    r=json.loads((session/'session.local.json').read_text('utf8'));d=json.loads(discovery.read_text('utf8'));build=Path(r['cue']).parent
    require(out.is_relative_to(build) and not out.exists(),'Fresh evidence path required')
    m=json.loads((build/'manifest.json').read_text('utf8'))
    require(m['task']=='fourth_armor_nana' and digest(build/'rin_nana.bin')==d['modified_bin_sha256']==r['bin_sha256'] and d['pid']==r['pid'],'Build/session mismatch')
    state=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';before=state.read_bytes()
    player=gzip.decompress(before)[442+0x1418c8:442+0x1418c8+0xe4]
    require(player[2]==0 and player[0xa7]==15 and player[0x17]==5,'Expected full armor idle checkpoint')
    em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';user,hwnd=em.checked_window(r['pid'])
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,r['pid']);require(bool(h),'Cannot open emulator read only')
    def read(address,size):
        b=ctypes.create_string_buffer(size);got=ctypes.c_size_t();require(k.ReadProcessMemory(h,address,b,size,ctypes.byref(got)) and got.value==size,'Short process read');return b.raw
    arc=(build/'modified.arc').read_bytes();bases=[]
    for base in d['ram_candidates']:
        ram=read(base,0x200000)
        if all(ram.find(entry(arc,t))>=0 for t in (2,3,9)):bases.append(base)
    require(len(bases)==1,'No unique current graphics RAM');base=bases[0]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
    require(len(pad)==16,'Unknown controls');out.mkdir();(out/'before.000').write_bytes(before);held=set();events=[];samples=[];trace=[];start=time.monotonic()
    def key(scan,down):
        if down:require(user.GetForegroundWindow()==hwnd,'Focus lost')
        e=em.Input();e.type=1;e.data.key=em.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0)
        require(user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1,'Input failed');events.append([round(time.monotonic()-start,4),scan,down])
        if down:held.add(scan)
        else:held.discard(scan)
    def sample(name):
        key(0x3b,True);time.sleep(.04);key(0x3b,False);time.sleep(.16)
        data=state.read_bytes();(out/(name+'.000')).write_bytes(data);p=gzip.decompress(data)[442+0x1418c8:442+0x1418c8+0xe4]
        samples.append({'name':name,'frame':p[0x47],'animation':p[0x17],'hp':p[0x5c],'sha256':digest(out/(name+'.000'))})
    try:
        sample('live_idle');key(pad[1],True);walk_start=time.monotonic();seen=set()
        while time.monotonic()-walk_start<8:
            if pad[1] in held and time.monotonic()-walk_start>=.9:key(pad[1],False)
            p=read(base+0x1418c8,0xe4);row=[p[0x17],p[0x47],p[0x5c]]
            if not trace or trace[-1][1:]!=row:trace.append([round(time.monotonic()-walk_start,4),*row])
            require(p[2]==0 and p[0xa7]==15,'Player/form changed')
            if 106<=p[0x47]<=114 and p[0x47] not in seen:
                seen.add(p[0x47]);sample('hurt_'+str(p[0x47]))
                if len(seen)>=3:break
            if p[0x5c]==0:break
            time.sleep(.005)
    finally:
        for scan in list(held):key(scan,False)
        state.write_bytes(before);key(0x3d,True);time.sleep(.06);key(0x3d,False);time.sleep(.3);k.CloseHandle(h)
        write(out/'capture.json',{'session':session.relative_to(ROOT).as_posix(),'build':build.relative_to(ROOT).as_posix(),'samples':samples,'trace_columns':['seconds','animation','frame','hp'],'trace':trace,'events':events,'pad1':pad,'live_ram_entries_equal':[2,3,9],'before_sha256':digest(out/'before.000'),'checkpoint_restored_exact':state.read_bytes()==before,'process_memory_written':False,'evidence':'ordinary gameplay after graphics-refreshed F3; not fresh disc resource loading'})
    print(json.dumps({'samples':samples,'restored':state.read_bytes()==before}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--discovery',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();capture(a.session,a.discovery,a.output)
