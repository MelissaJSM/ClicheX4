import sys,json,itertools
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from src.psx_tile_layout import pack_rectangles,remap_tiles
from src.psx_compress import encode_stream
d=Path(__file__).parent/'production01';arc=(ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z/modified.arc').read_bytes()
e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][92];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128)
rows=json.loads((d/'packing.json').read_text());old=next(r for r in rows if r['frame']==92);im=Image.open(d/'standing_092.png');best=old['encoded_bytes'];winner=old
for order in itertools.permutations(range(6)):
 rects=[old['rects'][i] for i in order];raw=pack_rectangles(dec.data,desc['tile_count'],im.tobytes(),im.size,rects,old['tiles'],old['writable'])
 for mapping,flips,shifts in [({t:t for t in old['writable']},{},{}),({int(k):v for k,v in old['mapping'].items()},{int(k):v for k,v in old['flips'].items()},{int(k):v for k,v in old['shifts'].items()})]:
  try:cost=len(encode_stream(remap_tiles(raw,desc['tile_count'],mapping,flips,shifts)))
  except ValueError:continue
  if cost<best:
   best=cost;winner={**old,'rects':rects,'mapping':mapping,'flips':flips,'shifts':shifts,'encoded_bytes':cost,'fits':cost<=old['budget'],'raw_sha256':sha256(raw)};print({'best':best,'order':order},flush=True)
 if best<=old['budget']:break
rows=[winner if r['frame']==92 else r for r in rows];(d/'packing.json').write_text(json.dumps(rows,indent=2));print({'final':best,'fits':winner['fits']})
