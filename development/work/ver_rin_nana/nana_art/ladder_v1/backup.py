from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[4];backup=ROOT/'work/ver_rin_nana/checkpoints/before_nana_ladder_20261030';backup.mkdir();em=ROOT/'work/ver_rin_nana/emulator'
shutil.copytree(em/'sstates',backup/'sstates');(backup/'current').mkdir();shutil.copyfile(em/'sstates/SLUS_005.61.000',backup/'current/SLUS_005.61.000')
cards=ROOT/'work/ver_rin_nana/test_cards/nana_fall_legs_v1';shutil.copytree(cards,backup/'cards');shutil.copytree(cards,ROOT/'work/ver_rin_nana/test_cards/nana_ladder_v1')
files=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in backup.rglob('*')if p.is_file()];(backup/'inventory.json').write_text(json.dumps(files,indent=2),'utf8');print(json.dumps(files))
