import sys,json,random,math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from src.psx_tile_layout import pack_rectangles,remap_tiles
from src.psx_compress import encode_stream
d=Path(__file__).parent/'production01';arc=(ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z/modified.arc').read_bytes()
e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][92];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128)
rows=json.loads((d/'packing.json').read_text());old=next(r for r in rows if r['frame']==92);im=Image.open(d/'standing_092.png');best=old['encoded_bytes'];winner=old;current=best;state=old;rng=random.Random(719)
for step in range(6000):
 r=json.loads(json.dumps(state));kind=rng.randrange(5)
 if kind==0:
  i=rng.randrange(6);axis=rng.randrange(2);r['rects'][i][axis]+=rng.choice((-2,-1,1,2))
 elif kind==1:
  a,b=rng.sample(range(6),2);r['rects'][a],r['rects'][b]=r['rects'][b],r['rects'][a]
 elif kind==2:
  a,b=map(str,rng.sample(r['writable'],2));r['mapping'][a],r['mapping'][b]=r['mapping'][b],r['mapping'][a]
 elif kind==3:
  a=str(rng.choice(r['writable']));r['flips'][a]=r['flips'].get(a,0)^rng.choice((64,128,192))
 else:
  a=str(rng.choice(r['writable']));xy=r['shifts'].get(a,[0,0]);xy[rng.randrange(2)]+=rng.choice((-1,1));r['shifts'][a]=xy
 try:
  raw=pack_rectangles(dec.data,desc['tile_count'],im.tobytes(),im.size,r['rects'],r['tiles'],r['writable'])
  result=remap_tiles(raw,desc['tile_count'],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});cost=len(encode_stream(result))
 except ValueError:continue
 temp=.8+3*(1-step/6000)
 if cost<=current or rng.random()<math.exp((current-cost)/temp):state=r;current=cost
 if cost<best:
  best=cost;winner={**r,'encoded_bytes':cost,'fits':cost<=old['budget'],'raw_sha256':sha256(raw)};print({'step':step,'best':best},flush=True)
  (d/'packing.json').write_text(json.dumps([winner if q['frame']==92 else q for q in rows],indent=2))
 if best<=old['budget']:break
print({'final':best,'fits':winner['fits']})
