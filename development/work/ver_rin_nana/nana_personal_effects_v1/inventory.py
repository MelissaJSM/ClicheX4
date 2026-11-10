import json,sys,struct
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels
from scripts.discover_inputs import DiscReader,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
D=Path(__file__).parent;P=R/'out/ver_rin_nana/nana_hud_theme_20261030T044031308363Z'
with (P/'rin_nana.bin').open('rb') as f:
 d=DiscReader(f,(P/'rin_nana.bin').stat().st_size);iso={q['path']:q for q in d.inspect()['files']}
 data={n:d.read(iso[n]['lba'],iso[n]['size']) for n in ['/ARC/PL00_U.ARC;1','/ARC/PL02_U.ARC;1','/ARC/COL00_0X.ARC;1','/SLUS_005.61;1']}
arc=data['/ARC/PL00_U.ARC;1'];pal=entry(arc,9)[:32];parts=entry(arc,3);tex=entry(arc,0x10206);g=entry(arc,2);fr=graphics_bank(g,0,allow_bank_aliases=True)['frames'][184]
raw=decode_stream(g,fr['offset'],fr['limit'],fr['tile_count']*128).data;px,size,bb,_=compose_launch(raw,fr['tile_count'],composition_frame(parts,0,184));head=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);Image.fromarray(head).save(D/'accepted_head_indices.png');render_pixels(head,pal).resize((size[0]*12,size[1]*12),Image.Resampling.NEAREST).save(D/'accepted_head_12x.png')
report={'parent_sha256':sha256((P/'rin_nana.bin').read_bytes()),'head_size':size,'head_bounds':bb,'body_palette':[],'death_exe_bytes':data['/SLUS_005.61;1'][0xbb67c:0xbb680].hex(),'static':{},'stage_palettes':{}}
for i,w in enumerate(struct.unpack('<16H',pal)):report['body_palette'].append({'index':i,'word':w,'rgb':[(w>>s&31)*255//31 for s in(0,5,10)]})
for n in range(89,114):
 bank=3 if n<99 else 1
 if 99<=n<105:continue
 cp=all_compositions(parts)[bank,n];a,sz,b,_=composed(tex,cp);report['static'][str(n)]={'bank':bank,'indices':np.unique(a).tolist(),'tiles':sorted({p['page']*256+p['tile'] for p in cp['parts']}),'cluts':sorted({p['clut']for p in cp['parts']})}
for row in (0,2,11,12,13,14,15,17):report['stage_palettes'][str(row)]=entry(data['/ARC/COL00_0X.ARC;1'],5)[row*32:(row+1)*32].hex()
(D/'inventory.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
