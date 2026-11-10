import sys,json,itertools
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_tile_layout import pack_rectangles,remap_tiles
from src.psx_compress import encode_stream
d=Path(__file__).parent/'production02';arc=(ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][92];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128)
rows=json.loads((d/'packing.json').read_text());r=next(r for r in rows if r['frame']==92);im=Image.open(d/'standing_092.png');raw=pack_rectangles(dec.data,desc['tile_count'],im.tobytes(),im.size,r['rects'],r['tiles'],r['writable'])
m={int(k):v for k,v in r['mapping'].items()};f={int(k):v for k,v in r['flips'].items()};s={int(k):v for k,v in r['shifts'].items()};best=r['encoded_bytes'];atlas,_,_=indexed_atlas(raw,desc['tile_count']);movements={}
for t in r['writable']:
 coords=[(x,y) for y in range(16) for x in range(16) if atlas[(t//16*16+y)*256+t%16*16+x]]
 if coords:
  xs,ys=zip(*coords);movements[t]=[(x,y) for x in range(-min(xs),16-max(xs)) for y in range(-min(ys),16-max(ys))]
for sweep in range(5):
 candidates=[]
 for aa,bb in itertools.combinations(r['writable'],2):
  mm=dict(m);mm[aa],mm[bb]=mm[bb],mm[aa];candidates.append((mm,dict(f),dict(s)))
 for aa in r['writable']:
  for flag in (64,128,192):candidates.append((dict(m),{**f,aa:f.get(aa,0)^flag},dict(s)))
 for aa,opts in movements.items():
  for xy in opts:candidates.append((dict(m),dict(f),{**s,aa:xy}))
 for mm,ff,ss in candidates:
  try:val=len(encode_stream(remap_tiles(raw,desc['tile_count'],mm,ff,ss)))
  except ValueError:continue
  if val<best:best,m,f,s=val,mm,ff,ss;print({'best':best},flush=True)
  if best<=1200:break
 if best<=1200:break
r.update(mapping=m,flips=f,shifts=s,encoded_bytes=best,fits=best<=1200);(d/'packing.json').write_text(json.dumps(rows,indent=2));print({'final':best,'fits':r['fits']})
