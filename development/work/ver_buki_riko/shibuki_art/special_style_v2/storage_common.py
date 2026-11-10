import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_sprite_batch import pack_original_layout,recolor_tiles
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from psx_compress_cost import encoded_cost

def load(a,n):
 art=json.loads((a/'art.json').read_text());q=next(q for q in art['groups'] if q['frame']==n);r=json.loads((a/f'packing_{n:03}.json').read_text());arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t];f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 targets={k:np.array(Image.open(a/f'frame_{k:03}.png')) for k in q['aliases'] if q['part_slots'][str(k)]};w=set(q['writable'])
 if q['kind']=='original_grid':
  raw=pack_original_layout(raw,f['tile_count'],targets[n],composition_frame(c,0,n),w);assignments={n:[(p['tile'],p['x']+80,p['y']+80,p['flags']&192) for p in composition_frame(c,0,n)['parts']]};assert sha256(raw)==r['raw_sha256']
 else:
  if q['effect_tiles']:raw=recolor_tiles(raw,f['tile_count'],q['effect_tiles'],art['effect_index_mapping'])
  raw,rp,sp,*_=pack_variant_pair(raw,f['tile_count'],targets[n],targets[n+1] if q['kind']=='pair' else targets[n],r['rects'],r['run_rects'],r['shot_rects'],w);assert sha256(raw)==r['raw_sha256']
  m={int(k):v for k,v in r['mapping'].items()};fl={int(k):v for k,v in r['flips'].items()};sh={int(k):v for k,v in r['shifts'].items()};raw=remap_tiles(raw,f['tile_count'],m,fl,sh);assignments={}
  for k in targets:
   dx,dy=q['translations'][str(k)];rows=sp if q['kind']=='pair' and k==n+1 else rp;assignments[k]=[(m[t],x+dx-sh.get(t,[0,0])[0],y+dy-sh.get(t,[0,0])[1],fl.get(t,0)) for t,x,y in rows]
 return art,q,r,f,raw,assignments,targets,w
