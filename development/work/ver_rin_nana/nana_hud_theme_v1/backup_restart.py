import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.project import digest
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261030T042833223241Z'
s=json.loads((session/'session.local.json').read_text('utf8'))
dst=ROOT/'work/ver_rin_nana/checkpoints/before_nana_hud_theme_20261030';dst.mkdir(exist_ok=False)
files=list((ROOT/'work/ver_rin_nana/emulator/sstates').glob('SLUS_005.61.000*'))+[Path(q['path'])for q in s['memory_card_overrides'].values()];report=[]
for i,p in enumerate(files):
    h=digest(p);out=dst/(f'{i:02}_'+p.name);shutil.copyfile(p,out)
    if digest(out)!=h or digest(p)!=h:raise ValueError('Backup differs')
    report.append({'source':str(p),'backup':str(out),'sha256':h})
cards=ROOT/'work/ver_rin_nana/test_cards/nana_hud_theme_v1';cards.mkdir(exist_ok=False)
for q in s['memory_card_overrides'].values():
    p=Path(q['path']);shutil.copyfile(p,cards/p.name)
(dst/'backup.json').write_text(json.dumps({'session':s,'files':report,'scene':'intro stage; prior F1 preserved before restart'},indent=2)+'\n','utf8');print(json.dumps({'files':len(files),'cards':str(cards)}))
