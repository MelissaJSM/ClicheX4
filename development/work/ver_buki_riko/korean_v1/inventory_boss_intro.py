"""Read-only extraction of native boss introduction resources."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import PARENT,PARENT_HASH,D
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from scripts.prepare_riko_ui import entry
from scripts.inventory_shibuki_ui import background,sheet
from scripts.inventory_korean_ui import grey
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

out=D/'boss_intro_inventory';out.mkdir(exist_ok=False)
inv=json.loads((D/'inventory/inventory.json').read_text('utf-8'))
game=PARENT/'shibuki_riko.bin'
if digest(game)!=PARENT_HASH:raise ValueError('Accepted source changed')
files={};report={};items=[]
names=[f'STD_1_{i}U.ARC' for i in range(1,9)]+[f'COLD_1U{i}.ARC' for i in range(1,9)]
with game.open('rb') as f:
    reader=DiscReader(f,game.stat().st_size)
    for name in names:
        rec=inv['records'][name];raw=reader.read(rec['lba'],rec['size']);files[name]=raw;(out/name).write_bytes(raw)
        report[name]={'record':rec,'sha256':sha256(raw),'entries':inv['resources'][name]['entries']}
for i in range(1,9):
    name=f'STD_1_{i}U.ARC';raw=files[name];pal=entry(files[f'COLD_1U{i}.ARC'],5)
    if i==1:
        for s in range(len(entry(raw,0))//512):
            im=background(raw,pal,s);im.save(out/f'background_{s:02d}.png');items.append((f'background {s}',im))
        for j in range(0,len(items),16):sheet(items[j:j+16],out/f'background_sheet_{j//16}.png',4,(260,280))
    g=entry(raw,0x10102);p=entry(raw,10);offs=struct.unpack('<2I',entry(raw,12));frames=[]
    for b,start in enumerate(offs):
        end=min((v for v in offs if v>start),default=len(g));count=aliased_composition(p,b,0)['bank_frame_count']
        report[name].setdefault('banks',[]).append({'bank':b,'start':start,'end':end,'frames':count})
        for n in range(min(count,4)):
            c=aliased_composition(p,b,n);px,size,bounds,_=compose_static(g[start:end],local_composition(c));im=grey(px,size)
            frames.append((f'bank {b} frame {n}',im))
    sheet(frames,out/f'actor_{i}.png',4,(260,240))
(out/'inventory.json').write_text(json.dumps({'source':str(PARENT.relative_to(ROOT)),'source_sha256':PARENT_HASH,'files':report},indent=2),encoding='utf-8')
print(out)
