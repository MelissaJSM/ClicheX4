from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];W=R/'work/steam_port_20261109';D=W/'audio/preserved_before'
D.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((W/'backup_manifest.json').read_text());report=[]
for row in manifest['user_state']:
 p=Path(row['source']);b=p.read_bytes();target=D/p.name
 if target.exists():raise ValueError('State backup exists')
 target.write_bytes(b);report.append({'source':str(p),'backup':str(target.relative_to(R)),'sha256':sha(b)})
for mode in ('ver_rin_nana','ver_buki_riko'):
 for name in ('project.json','current_build.json'):
  p=R/'projects'/mode/name;b=p.read_bytes();target=D/mode/name;target.parent.mkdir(exist_ok=True);target.write_bytes(b)
  report.append({'source':str(p),'backup':str(target.relative_to(R)),'sha256':sha(b)})
(D/'install_state.json').write_bytes((W/'install_state.json').read_bytes())
(D/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print({'preserved_files':len(report)})
