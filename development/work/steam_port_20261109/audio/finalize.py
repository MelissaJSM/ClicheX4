from pathlib import Path
import json,hashlib,sys,ctypes,struct
from ctypes import wintypes
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
W=R/'work/steam_port_20261109';D=W/'audio'
def sha(b):return hashlib.sha256(b).hexdigest()
state=json.loads((W/'install_state.json').read_text('utf8'))
for row in state['files']:
 if sha((EXE.parent/row['relative_path']).read_bytes())!=row['installed_sha256']:raise ValueError('Installed asset mismatch')
baseline=json.loads((W/'backup_manifest.json').read_text('utf8'))
installed={r['relative_path'] for r in state['files']}
for row in baseline['originals']:
 if sha((W/'original'/row['relative_path']).read_bytes())!=row['sha256']:raise ValueError('Original backup modified')
 if row['relative_path'] not in installed and sha((EXE.parent/row['relative_path']).read_bytes())!=row['sha256']:raise ValueError('Unrelated installed file modified')
assert sha(EXE.read_bytes())==ORIGINAL_SHA256
before=json.loads((D/'preserved_before/manifest.json').read_text());preservation=[]
for row in before:
 p=Path(row['source']);same=sha(p.read_bytes())==row['sha256'];preservation.append({'path':str(p),'same':same})
 if p.is_relative_to(R/'projects'):assert same
 if p.name=='savedata.dat':
  old=(R/row['backup']).read_bytes();now=p.read_bytes()
  save_compare={'before_sha256':sha(old),'after_sha256':sha(now),'same_length':len(old)==len(now),'changed_offsets':[i for i,(a,b) in enumerate(zip(old,now)) if a!=b],'written_or_restored_by_tools':False}
  (D/'savedata_after_start.dat').write_bytes(now)
_,(_,pid,title)=game_window()
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) or got.value!=n:raise ctypes.WinError(ctypes.get_last_error())
 return b.raw
try:
 engine=struct.unpack('<I',read(0x1b9b140,4))[0];slots=[]
 for region,offset in [('JP',0x3a0),('EN',0x4c0)]:
  for slot in range(6):
   b=read(engine+offset+slot*48,48)
   slots.append({'region':region,'slot':slot+1,'character':b[0],'arm_type':b[2],'armor':b[3],'weapons':b[4],'items_word':struct.unpack_from('<H',b,6)[0],'special':b[0x29]})
finally:k.CloseHandle(h)
historical=json.loads((W/'save_issue_20261109/live_save_records.json').read_text())['slots']
(D/'live_save_records_after.json').write_text(json.dumps({'pid':pid,'read_only':True,'slots':slots,'matches_previously_verified_12_slot_fields':slots==historical},indent=2)+'\n')
result={'pid':pid,'installed_files':len(state['files']),'all_installed_hashes_match':True,'all_original_backups_unchanged':True,'unmodified_installed_originals_unchanged':True,'original_exe_unchanged':True,'ps1_pointers_unchanged':True,'save_file_comparison':save_compare,'live_save_fields_match_prior_snapshot':slots==historical,'preservation':preservation,'runtime_report':f'work/steam_port_20261109/runtime/audio_{pid}.json','game_audio_user_acceptance':False}
(D/'application.json').write_text(json.dumps(result,indent=2)+'\n');(W/'current_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='preservation'}))
