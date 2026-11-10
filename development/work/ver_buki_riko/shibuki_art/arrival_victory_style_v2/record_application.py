import json, shutil, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent
build='out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z'
manifest=json.loads((ROOT/build/'manifest.json').read_text())
p=ROOT/'projects/ver_buki_riko/shibuki_pending_revision.json';v=json.loads(p.read_text());v.update(kind='arrival_victory_applied_runtime_in_progress',user_approval_received=True,user_approval_quote='진행 부탁할게',game_applied=True,build=build,bin_sha256=manifest['modified_bin']['sha256']);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
p=d/'provenance.json';v=json.loads(p.read_text());v.update(game_applied=True,applied_build=build,user_accepted=False);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
backup=d/'before_runtime_backup';backup.mkdir(exist_ok=False);rows=[]
em=ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator'
for folder in ('sstates','memcards'):
 for path in (em/folder).iterdir():
  if path.is_file():
   target=backup/folder/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);rows.append({'source':str(path.relative_to(ROOT)),'backup':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for name in ('current_build.json','shibuki_current_build.json'):
 shutil.copy2(ROOT/'projects/ver_buki_riko'/name,backup/name)
(backup/'backup.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
recipe1=ROOT/'work/ver_buki_riko/shibuki_arrival_victory_style/20261026T235424008252Z/modified.arc'
recipe2=ROOT/'work/ver_buki_riko/shibuki_arrival_victory_style/20261026T235445599767Z/modified.arc'
if recipe1.read_bytes()!=recipe2.read_bytes():raise ValueError('Repeat ARC differs')
(ROOT/build/'determinism.json').write_text(json.dumps({'sources':[str(p.relative_to(ROOT)) for p in (recipe1,recipe2)],'equal':True,'sha256':hashlib.sha256(recipe1.read_bytes()).hexdigest()},indent=2))
print(json.dumps({'backup_files':len(rows),'build':build,'repeated_arc_identical':True}))
