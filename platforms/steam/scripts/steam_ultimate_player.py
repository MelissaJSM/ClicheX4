"""Connect the Ultimate player display layers after normal startup."""
import ctypes,hashlib,json,struct,sys
from ctypes import wintypes
from pathlib import Path
from release_paths import ROOT
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
from src.steam_ultimate import build,original_sites,SIGNATURES
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def apply():
    file=W/'ultimate_runtime.json'
    if not file.exists():return {'active':False}
    spec=json.loads(file.read_text('utf8'));manifest=spec.get('build_manifest','ultimate_builds.json')
    if manifest not in ('ultimate_builds.json','pause_builds.json'):raise ValueError('Unknown cumulative player manifest')
    expected={'nativeDX10/X4/romPC/'+r['target_arc']:r['output_sha256'] for r in json.loads((W/manifest).read_text('utf8')) if r['target_arc'].startswith('pl02')}
    if spec['installed_requirements']!=expected:raise ValueError('Ultimate player requirements differ')
    matches=[(EXE.parent/n).exists() and sha((EXE.parent/n).read_bytes())==h for n,h in expected.items()]
    if not any(matches):return {'active':False}
    if not all(matches):raise ValueError('Ultimate player files incompletely installed')
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
    record=W/'runtime'/f'ultimate_player_{pid}.json';base=None;changed=[]
    try:
        if read(0x400000,2)!=b'MZ':raise ValueError('Module base differs')
        for a,s in SIGNATURES.items():
            if read(a,len(bytes.fromhex(s)))!=bytes.fromhex(s):raise ValueError('Native player display/getter signature differs: '+hex(a))
        if record.exists():
            prior=json.loads(record.read_text());data,hooks=build(prior['allocation'])
            if read(prior['allocation'],4096)!=data or any(read(a,len(c))!=c for a,b,c in hooks):raise ValueError('Existing outfit hook differs')
            return {**prior,'already_active':True}
        if any(read(a,len(b))!=b for a,b in original_sites()):raise ValueError('Native portrait call site differs')
        base=k.VirtualAllocEx(h,None,4096,0x3000,4)
        if not base or base>=0x80000000:raise ValueError('Unable to allocate x86 display block')
        data,hooks=build(base);write(base,data);old=wintypes.DWORD()
        if not k.VirtualProtectEx(h,base,4096,0x20,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
        for a,b,c in hooks:changed.append((a,b));write(a,c)
        report={'pid':pid,'active':True,'allocation':base,'blob_sha256':sha(data),'hooks':[{'address':a,'before_hex':b.hex(),'after_hex':c.hex()} for a,b,c in hooks],'owned_equipment_unchanged':True,'original_executable_verified':sha(EXE.read_bytes())==ORIGINAL_SHA256,'runtime_scene_verified':False}
        record.write_text(json.dumps(report,indent=2)+'\n');return report
    except Exception:
        for a,b in reversed(changed):write(a,b)
        if base:k.VirtualFreeEx(h,base,0,0x8000)
        raise
    finally:k.CloseHandle(h)
if __name__=='__main__':print(json.dumps(apply()))
