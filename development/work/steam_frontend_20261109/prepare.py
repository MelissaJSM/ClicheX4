from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
BASE=ROOT/'work/steam_port_20261109'
STEAM=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')
sha=lambda b:hashlib.sha256(b).hexdigest()
p=BASE/'backup_manifest.json'
d=json.loads(p.read_text('utf8'))
targets=['nativeDX10/RXC1/romPC/MenuGUIRXCRes.arc','nativeDX10/RXC1/romPC/TitleLogo.arc','nativeDX10/RXC1/romPC/Wallpaper.arc']
known={r['relative_path']:r for r in d['originals']}
backup=WORK/'preserved_before'
backup.mkdir(exist_ok=True)
for name in ['backup_manifest.json','install_state.json']:
    dest=backup/name
    if dest.exists():raise ValueError('Preservation already performed')
    shutil.copy2(BASE/name,dest)
for rel in targets:
    original=BASE/'original'/rel
    raw=(STEAM/rel).read_bytes()
    if rel in known:
        assert sha(original.read_bytes())==known[rel]['sha256']
        assert sha(raw)==known[rel]['sha256']
    else:
        if original.exists():raise ValueError('Unregistered original collision')
        original.parent.mkdir(parents=True,exist_ok=True)
        original.write_bytes(raw)
        assert original.read_bytes()==raw
        d['originals'].append({'relative_path':rel,'sha256':sha(raw),'size':len(raw)})
for rel in targets+['nativeDX10/X4/romPC/drawunit.arc']:
    dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(STEAM/rel,dest)
p.write_text(json.dumps(d,indent=2)+'\n','utf8')
(WORK/'baseline_extension.json').write_text(json.dumps({'targets':targets,'total_originals':len(d['originals']),'previous_manifest_sha256':sha((backup/'backup_manifest.json').read_bytes()),'new_manifest_sha256':sha(p.read_bytes())},indent=2)+'\n','utf8')
print('Verified backups:',targets)
