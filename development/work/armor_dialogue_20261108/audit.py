from pathlib import Path
import sys,json,struct
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import file_hash
from scripts.inventory_nana_dialogue import locate
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba
for mode in ['ver_rin_nana','ver_buki_riko']:
 dest=H/mode;dest.mkdir(exist_ok=False);p=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));bin=ROOT/Path(p['cue']).with_suffix('.bin');assert file_hash(bin)==p['sha256'];raw={};records={}
 with bin.open('rb') as f:
  disc=DiscReader(f,bin.stat().st_size)
  for r in disc.inspect()['files']:
   if r['path']=='/SLUS_005.61;1':(dest/'SLUS_005.61').write_bytes(disc.read(r['lba'],r['size']))
   if not r['path'].startswith('/ARC/') or not r['path'].endswith('.ARC;1'):continue
   name=r['name'].split(';')[0];data=disc.read(r['lba'],r['size']);raw[name]=data;records[name]={**r,'sha256':sha256(data)}
 inv=locate(records,raw);names=sorted({q['file'] for key in ['graphics','compositions','palettes'] for q in inv[key]});orig=dest/'originals';orig.mkdir()
 for n in names:(orig/n).write_bytes(raw[n])
 g=entry(raw['ST00_00.ARC'],0x10102)[204800:217088];parts=entry(raw['ST00_00.ARC'],10);pal=entry(raw['COL00_0X.ARC'],5);colors={i:struct.unpack('<16H',pal[(62+i)*32:(63+i)*32]) for i in range(2)}
 board=Image.new('RGB',(1344,640),(32,40,55));draw=ImageDraw.Draw(board);frames=[]
 for n in range(8):
  comp=aliased_composition(parts,11,n);im,bounds=render_static_rgba(g,comp,colors);im.save(dest/f'current_{n}.png');big=im.resize((336,288),Image.Resampling.NEAREST);board.paste(big,(n%4*336,n//4*320+30),big);draw.text((n%4*336+6,n//4*320+6),f'{n}: head {n&1}, body {(n>>1)&1}, mouth {(n>>2)&1}',fill='white');frames.append({'frame':n,'rgba_sha256':sha256(im.tobytes()),'bounds':bounds,'parts':len(comp['parts'])})
 board.save(dest/'current_sheet.png');report={'pointer':p,'records':{n:records[n] for n in names},'inventory':inv,'frames':frames,'unique_closed':len({r['rgba_sha256'] for r in frames[:4]}),'unique_open':len({r['rgba_sha256'] for r in frames[4:]})};(dest/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(mode,{'graphics':len(inv['graphics']),'parts':len(inv['compositions']),'palettes':sum(len(q['rows']) for q in inv['palettes']),'closed_variants':report['unique_closed'],'open_variants':report['unique_open']},flush=True)
