import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import pack_original_layout
d=Path(__file__).parent;a=d/'production11';art=json.loads((a/'art.json').read_text());arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t];bank=graphics_bank(g,0,allow_bank_aliases=True)
for n in (130,220):
 q=next(r for r in art['groups'] if r['frame']==n);f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;v=np.array(Image.open(a/f'frame_{n:03d}.png'));cp=composition_frame(c,0,n);uses={t:[r for r in cp['parts'] if r['tile']==t] for t in q['writable']};changes=[]
 for t,ps in uses.items():
  if len(ps)==1:continue
  for y in range(16):
   for x in range(16):
    points=[(80+p['y']+(15-y if p['flip_y'] else y),80+p['x']+(15-x if p['flip_x'] else x)) for p in ps];values=[int(v[py,px]) for py,px in points]
    if len(set(values))>1:
     # Only repeated outer energy fragments may be made symmetric; never body colors.
     if n==130 and any(z not in (0,2,5,6,8,9,14) for z in values):raise ValueError('Body color in shared energy tile')
     if n==220 and any(z not in (0,5,6,9) for z in values):raise ValueError('Body overlaps shared trail tile')
     value=max(set(values),key=lambda z:(values.count(z),z!=0))
     for py,px in points:
      if v[py,px]!=value:changes.append([int(px),int(py),int(v[py,px]),value]);v[py,px]=value
 try:
  packed=pack_original_layout(raw,f['tile_count'],v,cp,set(q['writable']));q['kind']='original_grid';save_image(v.tobytes(),(160,160),art['palette_words'],a/f'frame_{n:03d}.png');print(n,'PASS',len(changes));(a/f'energy_symmetry_{n}.json').write_text(json.dumps(changes))
 except ValueError as e:print(n,e)
(a/'art.json').write_text(json.dumps(art,indent=2))
