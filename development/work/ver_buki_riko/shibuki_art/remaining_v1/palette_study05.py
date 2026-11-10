import json,sys,itertools
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import recolor_tiles,pack_original_layout
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production05';art=json.loads((a/'art.json').read_text());arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t];bank=graphics_bank(g,0,allow_bank_aliases=True);report=[]
options=[{}, {9:5}, {6:5,9:5}, {2:15,10:11,12:13}, {6:5,9:5,2:15,10:11,12:13}, {6:5,9:5,2:15,10:11,12:13,3:8}, {6:5,9:5,2:15,10:11,12:13,3:8,14:5}, {6:5,9:5,2:15,10:11,12:13,3:8,14:5,8:15}]
for q in art['groups']:
 n=q['frame'];p=a/f'packing_{n:03d}.json'
 if not p.exists() or q['kind']!='body':continue
 r=json.loads(p.read_text())
 if r['fits']:continue
 f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 if q['effect_tiles']:raw=recolor_tiles(raw,f['tile_count'],q['effect_tiles'],art['effect_index_mapping'])
 v=np.array(Image.open(a/f'frame_{n:03d}.png'));costs=[]
 for mapping in options:
  lut=np.arange(16,dtype=np.uint8)
  for old,new in mapping.items():lut[old]=new
  target=lut[v];search=VariantSearch(raw,f['tile_count'],target,target,q['writable']);raw0,packed=search.pack(r['rects'],r['run_rects'],r['shot_rects'],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});costs.append(encoded_cost(packed))
 row={'frame':n,'budget':q['budget'],'costs':costs};report.append(row);print(row,flush=True)
(a/'palette_study.json').write_text(json.dumps({'options':options,'results':report},indent=2))
