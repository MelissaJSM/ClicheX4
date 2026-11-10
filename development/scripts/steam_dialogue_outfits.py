"""Connect Ultimate dialogue art and Black Zero colors after normal startup."""
import ctypes,hashlib,json,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
from src.steam_dialogue_variants import build,original_sites,native_sequences
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def apply():
    file=W/'dialogue_variant_runtime.json'
    if not file.exists():return {'active':False}
    spec=json.loads(file.read_text('utf8'));expected={'nativeDX10/X4/romPC/'+r['target_arc']:r['output_sha256'] for r in json.loads((W/'portrait_builds.json').read_text('utf8'))}
    if spec['installed_requirements']!=expected:raise ValueError('Portrait variant requirements differ')
    matches=[(EXE.parent/n).exists() and sha((EXE.parent/n).read_bytes())==h for n,h in expected.items()]
    if not any(matches):return {'active':False}
    if not all(matches):raise ValueError('Portrait variant files incompletely installed')
    if sha(EXE.read_bytes())!=ORIGINAL_SHA256:raise ValueError('Original EXE required')
    _,(_,pid,title)=game_window()
    if title!='Mega Man X Legacy Collection / ROCKMAN X ANNIVERSARY COLLECTION':raise ValueError('Normal game window required')
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes
    k.VirtualAllocEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,wintypes.DWORD];k.VirtualAllocEx.restype=ctypes.c_void_p
    k.VirtualFreeEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD];k.VirtualProtectEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    k.FlushInstructionCache.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x438,False,pid)
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    def read(a,n):
        b=ctypes.create_string_buffer(n);d=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(d)) or d.value!=n:raise ctypes.WinError(ctypes.get_last_error())
        return b.raw
    def write(a,b):
        old=wintypes.DWORD();d=ctypes.c_size_t()
        if not k.VirtualProtectEx(h,a,len(b),0x40,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
        try:
            buf=ctypes.create_string_buffer(b)
            if not k.WriteProcessMemory(h,a,buf,len(b),ctypes.byref(d)) or d.value!=len(b):raise ctypes.WinError(ctypes.get_last_error())
            if not k.FlushInstructionCache(h,a,len(b)) or read(a,len(b))!=b:raise ValueError('Outfit patch readback failed')
        finally:
            temp=wintypes.DWORD()
            if not k.VirtualProtectEx(h,a,len(b),old.value,ctypes.byref(temp)):raise ctypes.WinError(ctypes.get_last_error())
    record=W/'runtime'/f'dialogue_outfits_{pid}.json';base=None;changed=[]
    try:
        if read(0x400000,2)!=b'MZ':raise ValueError('Module base differs')
        for a,s in [(0x1adb15c,'08b1ad01'),(0x97f080,'a140b1b901c3'),(0x97f060,'8d4154c3'),(0x992d50,'8a8193000000c3'),(0x992d80,'8a818f000000c3'),(0x992e30,'8a8183000000c3'),(0x97c010,'a11cb1b901c3'),(0x97c020,'8b44240405168000008d0441c20400'),(0x97c240,'8a44240408812c800200c20400')]:
            if read(a,len(bytes.fromhex(s)))!=bytes.fromhex(s):raise ValueError('Native display/getter signature differs: '+hex(a))
        if read(0x1b9d9e8,64)!=native_sequences():raise ValueError('Native dialogue timing data differs')
        if record.exists():
            prior=json.loads(record.read_text());data,hooks=build(prior['allocation'],spec['zero_palettes'])
            if read(prior['allocation'],4096)!=data or any(read(a,len(c))!=c for a,b,c in hooks):raise ValueError('Existing outfit hook differs')
            return {**prior,'already_active':True}
        if any(read(a,len(b))!=b for a,b in original_sites()):raise ValueError('Native portrait call site differs')
        base=k.VirtualAllocEx(h,None,4096,0x3000,4)
        if not base or base>=0x80000000:raise ValueError('Unable to allocate x86 display block')
        data,hooks=build(base,spec['zero_palettes']);write(base,data);old=wintypes.DWORD()
        if not k.VirtualProtectEx(h,base,4096,0x20,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
        for a,b,c in hooks:changed.append((a,b));write(a,c)
        report={'pid':pid,'active':True,'allocation':base,'blob_sha256':sha(data),'hooks':[{'address':a,'before_hex':b.hex(),'after_hex':c.hex()} for a,b,c in hooks],'normal_animation_timing_verified':True,'original_executable_verified':sha(EXE.read_bytes())==ORIGINAL_SHA256,'runtime_scene_verified':False}
        record.write_text(json.dumps(report,indent=2)+'\n');return report
    except Exception:
        for a,b in reversed(changed):write(a,b)
        if base:k.VirtualFreeEx(h,base,0,0x8000)
        raise
    finally:k.CloseHandle(h)
if __name__=='__main__':print(json.dumps(apply()))
