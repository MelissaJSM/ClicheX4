import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.cwd();sys.path.insert(0,str(root));from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.epsxe_state import match_sprite
p=root/'work/ver_rin_nana/nana_batch_runtime/20261030T000553991463Z';build=root/'out/ver_rin_nana/nana_arrival_20261029T235340020385Z';arc=(build/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True);rows=[]
for n in (133,135,136,137,138,139,141,142):
 f=bank['frames'][n];raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data;_,size,bounds,_=compose_indices(raw,f['tile_count'],composition_frame(es[3],0,n));expected=Image.open(p/f'expected_{n:03d}_002_64_w0_0.png').convert('RGBA');a=np.array(expected);a[max(0,-8-bounds[1]):,:,3]=0;matches=[]
 for path in p.glob(f'observed_{n:03d}_002_64_w0_*.png'):
  for m in match_sprite(Image.open(path),Image.fromarray(a)):matches.append({'image':path.name,**m})
 rows.append({'frame':n,'scope':'only world Y < -8; lower body/effects excluded','tested_pixels':int((a[:,:,3]>0).sum()),'matches':matches})
report={'full_body_verified':False,'same_frame_first_screens_only':True,'rows':rows};(build/'upper_body_screen_check.local.json').write_text(json.dumps(report,indent=2),'utf8');print([(r['frame'],r['tested_pixels'],len(r['matches']))for r in rows])
