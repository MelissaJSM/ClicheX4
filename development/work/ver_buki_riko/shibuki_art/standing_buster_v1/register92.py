import sys,json,itertools,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream
from src.psx_tile_layout import pack_rectangles,remap_tiles
from src.psx_compress import encode_stream
d=Path(__file__).parent/'production01';out=Path(__file__).parent/'production03';arc=(ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][92];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128)
rows=json.loads((d/'packing.json').read_text());old=next(r for r in rows if r['frame']==92);base=np.array(Image.open(d/'standing_000.png'));arm=np.array(Image.open(d/'isolated_arm_092.png'));yy,xx=np.nonzero(arm);results=[]
for dx,dy in itertools.product(range(6,7),range(-1,3)):
 b=base.copy();b[36:53,:42]=0;b[53:55,:39]=0;b[yy+dy,xx+dx]=arm[yy,xx];b[:20]=base[:20];b[20:36,42:]=base[20:36,42:];b[55:]=base[55:]
 try:
  raw=pack_rectangles(dec.data,desc['tile_count'],b.tobytes(),(96,80),old['rects'],old['tiles'],old['writable']);packed=remap_tiles(raw,desc['tile_count'],{int(k):v for k,v in old['mapping'].items()},{int(k):v for k,v in old['flips'].items()},{int(k):v for k,v in old['shifts'].items()})
 except ValueError:continue
 cost=len(encode_stream(packed));print({'shift':[dx,dy],'bytes':cost},flush=True);results.append((cost,abs(dx-3)+abs(dy-1),dx,dy,b,raw))
fit=sorted([q for q in results if q[0]<=1200],key=lambda q:(q[1],q[0]))
if not fit:fit=sorted(results,key=lambda q:(q[0],q[1]))
cost,_,dx,dy,b,raw=fit[0];shutil.copytree(d,out);art=json.loads((out/'art.json').read_text());save_image(b.tobytes(),(96,80),art['palette_words'],out/'standing_092.png')
new={**old,'encoded_bytes':cost,'fits':cost<=1200,'raw_sha256':sha256(raw)};(out/'packing.json').write_text(json.dumps([new if r['frame']==92 else r for r in rows],indent=2))
next(r for r in art['frames'] if r['frame']==92)['arm_shift']=[dx,dy];(out/'art.json').write_text(json.dumps(art,indent=2));print(out)
