"""Install bounded X4 shared-archive name routing after normal Steam launch."""
import ctypes,json,hashlib,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
from src.steam_region_routes import build,original_sites,routing_data,SHARED,HQ_PRIVATE
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()

def apply():
    path=W/'portrait_routes.json'
    if not path.exists():return {'active':False,'reason':'No portrait build'}
    spec=json.loads(path.read_text('utf8'));routes=spec['routes']
    if {r['original_arc'] for r in routes}!={n+'.arc' for n in SHARED}:raise ValueError('Unrecognized shared resource set')
    if any(r['private_arc']!='cliche_br_'+r['original_arc'] for r in routes):raise ValueError('Unrecognized private resource name')
    expected={r['target_arc']:r['output_sha256'] for r in json.loads((W/'portrait_builds.json').read_text('utf8'))}
    if spec['requirements']!={'nativeDX10/X4/romPC/'+n:h for n,h in expected.items()}:raise ValueError('Portrait requirements differ')
    matches=[(EXE.parent/n).exists() and sha((EXE.parent/n).read_bytes())==h for n,h in spec['requirements'].items()]
    if not any(matches):return {'active':False,'reason':'Portrait files not installed'}
    if not all(matches):raise ValueError('Incomplete portrait installation')
    hq_file=W/'hq_variant_builds.json';with_hq=False
    if hq_file.exists():
        hq=json.loads(hq_file.read_text('utf8'))
        if len(hq)!=36 or {r['target_arc'] for r in hq}!=set(HQ_PRIVATE):raise ValueError('HQ variant target set differs')
        hm=[(EXE.parent/'nativeDX10/X4/romPC'/r['target_arc']).exists() and sha((EXE.parent/'nativeDX10/X4/romPC'/r['target_arc']).read_bytes())==r['output_sha256'] for r in hq]
        if any(hm) and not all(hm):raise ValueError('Incomplete HQ variant installation')
        with_hq=all(hm)
    original=EXE.read_bytes()
    if sha(original)!=ORIGINAL_SHA256:raise ValueError('Original EXE required')
    _,(_,pid,title)=game_window()
    if title!='Mega Man X Legacy Collection / ROCKMAN X ANNIVERSARY COLLECTION':raise ValueError('Unexpected game window')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes
    k.VirtualAllocEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,wintypes.DWORD];k.VirtualAllocEx.restype=ctypes.c_void_p
    k.VirtualFreeEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD]
    k.VirtualProtectEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    k.FlushInstructionCache.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t]
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x438,False,pid)
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    def read(addr,size):
        buf=ctypes.create_string_buffer(size);done=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,addr,buf,size,ctypes.byref(done)) or done.value!=size:raise ctypes.WinError(ctypes.get_last_error())
        return buf.raw
    def write(addr,data):
        old=wintypes.DWORD();done=ctypes.c_size_t()
        if not k.VirtualProtectEx(h,addr,len(data),0x40,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
        try:
            buf=ctypes.create_string_buffer(data)
            if not k.WriteProcessMemory(h,addr,buf,len(data),ctypes.byref(done)) or done.value!=len(data):raise ctypes.WinError(ctypes.get_last_error())
            if not k.FlushInstructionCache(h,addr,len(data)) or read(addr,len(data))!=data:raise ValueError('Route write/readback failed')
        finally:
            unused=wintypes.DWORD()
            if not k.VirtualProtectEx(h,addr,len(data),old.value,ctypes.byref(unused)):raise ctypes.WinError(ctypes.get_last_error())
    record=W/'runtime'/f'portrait_routes_{pid}.json';allocated=None;changed=[]
    try:
        if read(0x400000,2)!=b'MZ':raise ValueError('Unexpected module base')
        # Validate the native game-language getter, not a guessed global offset.
        for addr,value in [(0x9831dd,bytes.fromhex('8b0d083ab4016a04')),(0x75e864,bytes.fromhex('83c17085c97408e8f040f3ffc20400')),(0x692960,bytes.fromhex('8b4108c3'))]:
            if read(addr,len(value))!=value:raise ValueError('Language consumer signature differs: '+hex(addr))
        if read(0xf6c910,0x3d8)!=original[0xb6bd10:0xb6c0e8] or read(0xf6ccf0,0x3d8)!=original[0xb6c0f0:0xb6c4c8]:raise ValueError('Resource lookup tables differ')
        if with_hq:
            for addr,value in [(0x97f080,'a140b1b901c3'),(0x97f060,'8d4154c3'),(0x986080,'83c108e9c8cc0000'),(0x992d50,'8a8193000000c3'),(0x992d80,'8a818f000000c3'),(0x992e30,'8a8183000000c3')]:
                if read(addr,len(bytes.fromhex(value)))!=bytes.fromhex(value):raise ValueError('HQ equipment getter signature differs: '+hex(addr))
        if record.exists():
            previous=json.loads(record.read_text());base=previous['allocation'];blob,hooks=build(original,base,with_hq)
            if read(base,len(blob))!=blob or any(read(a,len(new))!=new for a,old,new in hooks):raise ValueError('Existing route allocation differs')
            return {**previous,'already_active':True}
        if any(read(a,len(old))!=old for a,old in original_sites()):raise ValueError('Unexpected native lookup instructions')
        allocated=k.VirtualAllocEx(h,None,4096,0x3000,4)
        if not allocated or allocated>=0x80000000:raise ValueError('Unable to allocate bounded x86 routing block')
        blob,hooks=build(original,allocated,with_hq);write(allocated,blob);old=wintypes.DWORD()
        if not k.VirtualProtectEx(h,allocated,4096,0x20,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
        for a,before,after in hooks:changed.append((a,before));write(a,after)
        result={'pid':pid,'active':True,'hq_variants':with_hq,'allocation':allocated,'allocation_bytes':4096,'blob_sha256':sha(blob),'hooks':[{'address':a,'before_hex':b.hex(),'after_hex':c.hex()} for a,b,c in hooks],'routes':routes,'executable_file_unchanged':sha(EXE.read_bytes())==ORIGINAL_SHA256,'runtime_scene_verified':False}
        record.write_text(json.dumps(result,indent=2)+'\n');return result
    except Exception:
        for a,old in reversed(changed):write(a,old)
        if allocated:k.VirtualFreeEx(h,allocated,0,0x8000)
        raise
    finally:k.CloseHandle(h)
if __name__=='__main__':print(json.dumps(apply()))
