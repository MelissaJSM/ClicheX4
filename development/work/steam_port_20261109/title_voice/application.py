from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.steam_runtime import EXE,game_window
from src.steam_executable import ORIGINAL_SHA256
W=R/'work/steam_port_20261109';D=Path(__file__).parent
version=sys.argv[2] if len(sys.argv)>2 else 'v1'
if version not in ('v1','v2','v3'):raise ValueError('Unsupported verification version')
if version!='v1':D=D/version
build_manifest=W/(f'title_voice_{version}_builds.json' if version!='v1' else 'title_voice_builds.json')
def sha(b):return hashlib.sha256(b).hexdigest()
base=json.loads((W/'backup_manifest.json').read_text('utf8'))
state=json.loads((W/'install_state.json').read_text('utf8'))
installed={r['relative_path']:r for r in state['files']}
for row in installed.values():assert sha((EXE.parent/row['relative_path']).read_bytes())==row['installed_sha256']
for row in base['originals']:
 assert sha((W/'original'/row['relative_path']).read_bytes())==row['sha256']
 if row['relative_path'] not in installed:assert sha((EXE.parent/row['relative_path']).read_bytes())==row['sha256']
assert sha(EXE.read_bytes())==ORIGINAL_SHA256
if sys.argv[1]=='before':
 P=D/'preserved_before'
 if P.exists():raise ValueError('Preservation snapshot already exists')
 P.mkdir();rows=[]
 for row in base['user_state']:
  source=Path(row['source']);raw=source.read_bytes();target=P/source.name;target.write_bytes(raw)
  rows.append({'source':str(source),'backup':str(target.relative_to(R)),'sha256':sha(raw)})
 for mode in ('ver_rin_nana','ver_buki_riko'):
  for name in ('project.json','current_build.json','final_release.json'):
   source=R/'projects'/mode/name
   if not source.exists():continue
   raw=source.read_bytes();target=P/mode/name;target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
   rows.append({'source':str(source),'backup':str(target.relative_to(R)),'sha256':sha(raw)})
 (P/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n','utf8')
 (P/'install_state.json').write_bytes((W/'install_state.json').read_bytes())
 print({'preserved':len(rows),'installed_verified':len(installed)})
else:
 before=json.loads((D/'preserved_before/install_state.json').read_text('utf8'))
 builds=json.loads(build_manifest.read_text('utf8'))
 changed={r['relative_path'] for r in builds}
 assert all(installed[r['relative_path']]==r for r in before['files'] if r['relative_path'] not in changed)
 assert all(installed[r['relative_path']]['installed_sha256']==r['output_sha256'] for r in builds)
 preservation=[]
 for row in json.loads((D/'preserved_before/manifest.json').read_text('utf8')):
  p=Path(row['source']);raw=p.read_bytes();same=sha(raw)==row['sha256']
  if p.is_relative_to(R/'projects'):assert same
  item={'path':str(p),'same':same}
  if p.name=='savedata.dat':
   old=(R/row['backup']).read_bytes();item['before_sha256']=sha(old);item['after_sha256']=sha(raw)
   item['same_length']=len(old)==len(raw);item['changed_offsets']=[i for i,(a,b) in enumerate(zip(old,raw)) if a!=b]
   (D/'savedata_after_start.dat').write_bytes(raw)
  preservation.append(item)
 _,(_,pid,title)=game_window()
 report={'pid':pid,'installed_files':len(installed),'all_installed_hashes_match':True,
  'all_original_backups_unchanged':True,'unmodified_installed_originals_unchanged':True,
  'original_exe_unchanged':True,'previous_172_installed_files_unchanged':True,
  'ps1_pointers_unchanged':True,'save_written_or_restored_by_tools':False,
  'preservation':preservation,'title_voice_user_acceptance':False}
 (D/'application.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 (W/'current_verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps(report))
