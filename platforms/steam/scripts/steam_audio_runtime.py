"""Enable the original eight-boss intro playback path after normal Steam launch."""
from pathlib import Path
import ctypes,hashlib,json,sys
from ctypes import wintypes
from release_paths import ROOT
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def apply():
 if not (W/'audio_runtime.json').exists():return {'active':False}
 proof=json.loads((W/'audio/independent_verification.json').read_text())
 if not proof['passed'] or proof['native_intro_cases']!=9984:raise ValueError('Audio CPU verification required')
 spec=json.loads((W/'audio_runtime.json').read_text());rows=json.loads((W/'audio_builds.json').read_text())
 expected={r['relative_path']:r['output_sha256'] for r in rows}
 if spec['installed_requirements']!=expected:raise ValueError('Audio runtime requirements differ')
 if any(not (EXE.parent/n).exists() or sha((EXE.parent/n).read_bytes())!=v for n,v in expected.items()):raise ValueError('Incomplete audio installation')
 if sha(EXE.read_bytes())!=ORIGINAL_SHA256:raise ValueError('Original EXE required')
 _,(_,pid,title)=game_window()
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
 k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes
 k.VirtualProtectEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
 k.FlushInstructionCache.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
 h=k.OpenProcess(0x438,False,pid)
 if not h:raise ctypes.WinError(ctypes.get_last_error())
 def read(a,n):
  b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
  if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) or got.value!=n:raise ctypes.WinError(ctypes.get_last_error())
  return b.raw
 a=0x987ec9;before=bytes.fromhex('725e');after=b'\x90\x90';changed=False
 def write(data):
  old=wintypes.DWORD();got=ctypes.c_size_t()
  if not k.VirtualProtectEx(h,a,2,0x40,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
  try:
   b=ctypes.create_string_buffer(data)
   if not k.WriteProcessMemory(h,a,b,2,ctypes.byref(got)) or got.value!=2:raise ctypes.WinError(ctypes.get_last_error())
   k.FlushInstructionCache(h,a,2)
   if read(a,2)!=data:raise ValueError('Audio branch readback failed')
  finally:
   unused=wintypes.DWORD();k.VirtualProtectEx(h,a,2,old.value,ctypes.byref(unused))
 try:
  start=0x987e60;n=0xf6;before_hash='9359629a8c2e2070a6d911e7a7652f2594b6405e81b00dea7f6ce043a66ae04b';after_hash='26517f7d45533e7e9d5f8a00b19ce24dd173c3009b9dfa2c4f619c15e02cb8cc'
  live_hash=sha(read(start,n))
  if live_hash not in (before_hash,after_hash):raise ValueError('Native intro function changed unexpectedly')
  if live_hash==before_hash:changed=True;write(after)
  if sha(read(start,n))!=after_hash:raise ValueError('Native intro readback differs')
  result={'pid':pid,'active':True,'address':hex(a),'before_hex':before.hex(),'after_hex':after.hex(),'already_active':not changed,'installed_files':len(rows),'original_exe_verified':True,'save_state_untouched':True,'actual_audio_heard':False}
  (W/'runtime'/f'audio_{pid}.json').write_text(json.dumps(result,indent=2)+'\n');return result
 except Exception:
  if changed:write(before)
  raise
 finally:k.CloseHandle(h)
if __name__=='__main__':print(json.dumps(apply()))
