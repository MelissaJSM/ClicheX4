import json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.project import digest
S=R/'work/ver_rin_nana/emulator_sessions/20261030T044407793268Z';s=json.loads((S/'session.local.json').read_text('utf8'));D=R/'work/ver_rin_nana/checkpoints/before_nana_personal_effects_20261030';D.mkdir(exist_ok=False);rows=[]
for i,p in enumerate(list((R/'work/ver_rin_nana/emulator/sstates').glob('SLUS_005.61.000*'))+[Path(q['path'])for q in s['memory_card_overrides'].values()]):
 h=digest(p);dst=D/(f'{i:02}_'+p.name);shutil.copyfile(p,dst);assert digest(dst)==h==digest(p);rows.append({'source':str(p),'backup':str(dst),'sha256':h})
C=R/'work/ver_rin_nana/test_cards/nana_personal_effects_v1';C.mkdir(exist_ok=False)
for q in s['memory_card_overrides'].values():shutil.copyfile(q['path'],C/Path(q['path']).name)
(D/'backup.json').write_text(json.dumps({'session':s,'files':rows,'scene':'Nana pause menu, all weapons'},indent=2)+'\n','utf8');print(len(rows))
