"""Connect the verified X4 death-orb palette after normal Steam launch."""
from pathlib import Path
import ctypes,hashlib,json,sys
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
from src.steam_effect_colors import START,SIZE,ADDRESS,BEFORE,AFTER,signatures
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def apply():
 if not (W/'effect_colors_runtime.json').exists():return {'active':False}
 spec=json.loads((W/'effect_colors_runtime.json').read_text());proof_raw=(W/'get_boss_completion/death_cpu_verification.json').read_bytes();proof=json.loads(proof_raw)
 if sha(proof_raw)!=spec['proof_sha256'] or not proof['passed'] or proof['ps1_death_frames_equal']!=54:raise ValueError('Death palette CPU/source proof required')
 if (spec['address'],spec['before_hex'],spec['after_hex'])!=(ADDRESS,BEFORE.hex(),AFTER.hex()):raise ValueError('Unexpected effect patch')
 rows=[r for r in json.loads((W/'pause_builds.json').read_text()) if r['target_arc'].startswith('pl')]
 expected={r['relative_path']:r['output_sha256'] for r in rows}
 if len(rows)!=6 or expected!=spec['installed_requirements']:raise ValueError('Player graphics requirements differ')
 if any(not (EXE.parent/n).exists() or sha((EXE.parent/n).read_bytes())!=v for n,v in expected.items()):raise ValueError('Incomplete player installation')
 if sha(EXE.read_bytes())!=ORIGINAL_SHA256:raise ValueError('Original EXE required')
 original,patched=signatures((W/'runtime/code/text.bin').read_bytes())
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
 def write(data):
  old=wintypes.DWORD();got=ctypes.c_size_t()
  if not k.VirtualProtectEx(h,ADDRESS,1,0x40,ctypes.byref(old)):raise ctypes.WinError(ctypes.get_last_error())
  try:
   b=ctypes.create_string_buffer(data)
   if not k.WriteProcessMemory(h,ADDRESS,b,1,ctypes.byref(got)) or got.value!=1:raise ctypes.WinError(ctypes.get_last_error())
   if not k.FlushInstructionCache(h,ADDRESS,1):raise ctypes.WinError(ctypes.get_last_error())
   if read(ADDRESS,1)!=data:raise ValueError('Death palette operand readback failed')
  finally:
   unused=wintypes.DWORD();k.VirtualProtectEx(h,ADDRESS,1,old.value,ctypes.byref(unused))
 changed=False
 try:
  live=read(START,SIZE)
  if live not in (original,patched):raise ValueError('Native death initializer changed unexpectedly')
  if live==original:changed=True;write(AFTER)
  if read(START,SIZE)!=patched:raise ValueError('Death initializer readback differs')
  report={'pid':pid,'active':True,'address':hex(ADDRESS),'before_hex':BEFORE.hex(),'after_hex':AFTER.hex(),'already_active':not changed,'function_readback_verified':True,'installed_player_files':len(rows),'original_exe_verified':True,'game_state_untouched':True,'actual_death_scene_verified':False}
  (W/'runtime'/f'effect_colors_{pid}.json').write_text(json.dumps(report,indent=2)+'\n');return report
 except Exception:
  if changed:write(BEFORE)
  raise
 finally:k.CloseHandle(h)
if __name__=='__main__':print(json.dumps(apply()))
