from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
W=R/'work/steam_port_20261109';D=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
state=json.loads((W/'install_state.json').read_text('utf8'));base=json.loads((W/'backup_manifest.json').read_text('utf8'));known={r['relative_path']:r for r in state['files']}
for rel,r in known.items():assert sha((EXE.parent/rel).read_bytes())==r['installed_sha256']
for r in base['originals']:
 assert sha((W/'original'/r['relative_path']).read_bytes())==r['sha256']
 if r['relative_path'] not in known:assert sha((EXE.parent/r['relative_path']).read_bytes())==r['sha256']
assert sha(EXE.read_bytes())==ORIGINAL_SHA256
if sys.argv[1]=='before':
 p=D/'preserved_before';p.mkdir();rows=[]
 (p/'archives').mkdir()
 for r in json.loads((W/'frost_labels_builds.json').read_text('utf8')):
  raw=(EXE.parent/'nativeDX10/X4/romPC'/r['target_arc']).read_bytes();assert sha(raw)==r['parent_sha256'];(p/'archives'/r['target_arc']).write_bytes(raw)
 for r in base['user_state']:
  source=Path(r['source']);raw=source.read_bytes();target=p/source.name;target.write_bytes(raw);rows.append({'path':str(source),'backup':str(target.relative_to(R)),'sha256':sha(raw)})
 for mode in ['ver_rin_nana','ver_buki_riko']:
  for name in ['project.json','current_build.json','final_release.json']:
   source=R/'projects'/mode/name
   if not source.exists():continue
   raw=source.read_bytes();target=p/mode/name;target.parent.mkdir(exist_ok=True);target.write_bytes(raw);rows.append({'path':str(source),'backup':str(target.relative_to(R)),'sha256':sha(raw)})
 write(p/'manifest.json',rows);write(p/'install_state.json',state);print({'preserved':len(rows),'installed_verified':len(known)})
else:
 builds=json.loads((W/'frost_labels_builds.json').read_text('utf8'));changed={'nativeDX10/X4/romPC/'+r['target_arc']:r for r in builds};old=json.loads((D/'preserved_before/install_state.json').read_text('utf8'))
 for r in old['files']:
  if r['relative_path'] not in changed:assert known[r['relative_path']]==r
 for rel,r in changed.items():assert known[rel]['installed_sha256']==r['output_sha256']
 preservation=[]
 for r in json.loads((D/'preserved_before/manifest.json').read_text('utf8')):
  p=Path(r['path']);same=sha(p.read_bytes())==r['sha256']
  if p.is_relative_to(R/'projects'):assert same
  preservation.append({'path':str(p),'same':same,'after_sha256':sha(p.read_bytes())})
 _,(_,pid,title)=game_window();report={'pid':pid,'installed_files':len(known),'all_hashes_verified':True,'original_exe_and_backups_unchanged':True,'other_installed_files_preserved':True,'ps1_pointers_unchanged':True,'save_written_or_restored_by_tools':False,'preservation':preservation,'runtime_scenes_verified':False}
 write(D/'application.json',report);write(W/'current_verification.json',report);print(report)
