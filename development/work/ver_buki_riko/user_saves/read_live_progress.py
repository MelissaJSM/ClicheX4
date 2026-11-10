"""검증된 작업용 ePSXe의 미국판 RAM에서 진행도만 읽고 표본을 보존한다."""
from pathlib import Path
import ctypes, json, struct, sys
from ctypes import wintypes
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.emulator_session import checked_window
from scripts.capture_poc_memory import Region
from scripts.project import new_run, write_json, digest

session = ROOT / sys.argv[1]
record = json.loads((session/'session.local.json').read_text())
checked_window(record['pid'])
profile = json.loads((ROOT/'config/ps1_us_slus00561.json').read_text())
exe = ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z/original.exe'
assert digest(exe) == profile['executable']['sha256']
address = profile['zero_animation_table_address']
offset = address - profile['executable']['load_address'] + 2048
anchor = exe.read_bytes()[offset:offset+576]
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
k.OpenProcess.restype = wintypes.HANDLE
k.ReadProcessMemory.argtypes = [wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.VirtualQueryEx.argtypes = [wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
k.CloseHandle.argtypes = [wintypes.HANDLE]
h = k.OpenProcess(0x410, False, record['pid'])
if not h: raise OSError('Cannot read process')
def read(a,n):
    b = ctypes.create_string_buffer(n);got = ctypes.c_size_t()
    return b.raw[:got.value] if k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) else b''
try:
    bases = set()
    if len(sys.argv)>2:
        prior=json.loads((ROOT/sys.argv[2]).read_text())
        assert prior['pid']==record['pid']
        bases.add(prior['ram_host_address'])
    else:
        cursor=0
        while cursor<0x100000000:
            r=Region()
            if not k.VirtualQueryEx(h,cursor,ctypes.byref(r),ctypes.sizeof(r)):break
            start=r.base or 0;end=start+r.size
            if end<=cursor:break
            if r.state==0x1000 and not r.protect&0x100 and r.protect&0xff in (2,4,8,0x20,0x40,0x80):
                for pos in range(start,end,1048576):
                    blob=read(pos,min(1048576+576,end-pos));at=blob.find(anchor)
                    while at>=0:
                        bases.add(pos+at-(address&0x1fffff));at=blob.find(anchor,at+1)
            cursor=end
    valid=[b for b in bases if b>=0 and read(b+(address&0x1fffff),576)==anchor and len(read(b,2097152))==2097152]
    if len(valid)!=1:raise ValueError(f'Expected one US RAM; candidates={valid}')
    base=valid[0];p=read(base+0x1418c8,0xe4);e=read(base+0x1721c0,0x64)
    out=new_run(ROOT,'ver_buki_riko','save_validation')
    (out/'player.bin').write_bytes(p);(out/'engine.bin').write_bytes(e)
    result=dict(pid=record['pid'],session=str(session),bin_sha256=record['bin_sha256'],ram_host_address=base,
                character=p[2],animation=p[0x17],frame=p[0x47],hp=p[0x5c],player_boss_flags=p[0xb9],
                engine_boss_flags=e[0x59],stage=e[0xc],substage=e[0xd],lives=e[0x44],
                x=struct.unpack_from('<i',p,8)[0]/65536,y=struct.unpack_from('<i',p,12)[0]/65536,
                process_memory_written=False,state_load_from_session=record.get('save_state_loaded'),
                source_note='US animation-table anchor; PS1 player+0xB9 unlock field; no progress edits')
    write_json(out/'progress.local.json',result)
    print(json.dumps(dict(output=str(out),**result)))
finally:k.CloseHandle(h)
