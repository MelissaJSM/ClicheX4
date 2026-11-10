import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts,pack_original_layout
d=Path(__file__).parent;a=d/'production04';art=json.loads((a/'art.json').read_text());arc=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc').read_bytes();es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t];bank=graphics_bank(g,0,allow_bank_aliases=True);fx=np.array(art['effect_index_mapping'],np.uint8)
def orig(n):
 f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;return raw,canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,n))
def get(n):return np.array(Image.open(a/f'frame_{n:03d}.png'))
def over(bg,fg):
 out=bg.copy();out[fg!=0]=fg[fg!=0];return out
def move(v,dy):
 out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x]=v[y,x];return out
raw,bg=orig(130);bg[np.isin(bg,[5,8])]=14;v=over(fx[bg],np.where(get(133)!=0,9,0).astype(np.uint8));save_image(v.tobytes(),(160,160),art['palette_words'],a/'frame_130.png')
v=move(get(217),-6);save_image(v.tobytes(),(160,160),art['palette_words'],a/'frame_217.png')
raw,bg=orig(220);bg[(bg!=0)&~np.isin(bg,[8,12])]=8;v=over(fx[bg],get(217));save_image(v.tobytes(),(160,160),art['palette_words'],a/'frame_220.png')
for n in (130,134,158,220):
 q=next(r for r in art['groups'] if r['frame']==n);f=bank['frames'][n];raw=orig(n)[0];v=get(n);comp=composition_frame(c,0,n)
 coverage=np.zeros(v.shape,bool)
 for part in comp['parts']:
  x,y=part['x']+80,part['y']+80;coverage[y:y+16,x:x+16]=True
 outside=np.count_nonzero((v!=0)&~coverage)
 if n==158:
  # The neighboring ring frame has a different edge layout; retain only its covered effect pixels.
  assert not np.any(get(156)[~coverage]);v[~coverage]=0;save_image(v.tobytes(),(160,160),art['palette_words'],a/f'frame_{n:03d}.png')
 try:
  packed=pack_original_layout(raw,f['tile_count'],v,comp,set(q['writable']));q['kind']='original_grid';print(n,'exact original layout','effect-edge pixels omitted',outside)
 except ValueError as e:print(n,e,'outside',outside)
(a/'art.json').write_text(json.dumps(art,indent=2))
