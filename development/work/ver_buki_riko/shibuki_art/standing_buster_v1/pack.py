import sys,json,itertools,random,math
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_tile_layout import pack_rectangles,remap_tiles
from src.psx_compress import encode_stream
d=Path(__file__).parent/'production01';parent=ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z'
arc=(parent/'modified.arc').read_bytes();assert sha256(arc)=='0207811d5b5f3630f4d72a171b91545b33b26653e86f7498017cd2eb2f774f4f'
e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];bank=graphics_bank(gfx,0,allow_bank_aliases=True)
rows=[]
for r in json.loads((d/'layout.json').read_text()):
 n=r['frame'];a=Image.open(d/f'standing_{n:03d}.png');desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
 writable=list(range(7 if n==92 else 8));tiles=list(range(1,len(r['rects'])+1));raw=pack_rectangles(dec.data,desc['tile_count'],a.tobytes(),a.size,r['rects'],tiles,writable)
 m={t:t for t in writable};f={};s={};budget=dec.end-dec.start;best=len(encode_stream(raw));initial=best
 print({'frame':n,'initial':best,'budget':budget},flush=True)
 atlas,_,_=indexed_atlas(raw,desc['tile_count']);movements={}
 for t in writable:
  coords=[(x,y) for y in range(16) for x in range(16) if atlas[(t//16*16+y)*256+t%16*16+x]]
  if coords:
   xs,ys=zip(*coords);movements[t]=[(x,y) for x in range(-min(xs),16-max(xs)) for y in range(-min(ys),16-max(ys))]
 def cost(mm,ff,ss):
  try:return len(encode_stream(remap_tiles(raw,desc['tile_count'],mm,ff,ss)))
  except ValueError:return 100000
 rng=random.Random(n)
 for sweep in range(7):
  if best<=budget:break
  candidates=[]
  for aa,bb in itertools.combinations(writable,2):
   mm=dict(m);mm[aa],mm[bb]=mm[bb],mm[aa];candidates.append((mm,dict(f),dict(s)))
  for aa in writable:
   for flag in (64,128,192):candidates.append((dict(m),{**f,aa:f.get(aa,0)^flag},dict(s)))
  for aa,opts in movements.items():
   for xy in opts:candidates.append((dict(m),dict(f),{**s,aa:xy}))
  rng.shuffle(candidates);improved=False
  for mm,ff,ss in candidates:
   val=cost(mm,ff,ss)
   if val<best:best,m,f,s=val,mm,ff,ss;improved=True
   if best<=budget:break
  print({'frame':n,'sweep':sweep,'best':best},flush=True)
  if not improved:break
 current=best;cm,cf,cs=dict(m),dict(f),dict(s)
 for step in range(4000):
  if best<=budget:break
  mm,ff,ss=dict(cm),dict(cf),dict(cs);kind=rng.randrange(3)
  if kind==0:
   aa,bb=rng.sample(writable,2);mm[aa],mm[bb]=mm[bb],mm[aa]
  elif kind==1:
   aa=rng.choice(writable);ff[aa]=ff.get(aa,0)^rng.choice((64,128,192))
  else:
   aa=rng.choice(list(movements));ss[aa]=rng.choice(movements[aa])
  val=cost(mm,ff,ss);temp=1+4*(1-step/4000)
  if val<=current or rng.random()<math.exp((current-val)/temp):current,cm,cf,cs=val,mm,ff,ss
  if val<best:best,m,f,s=val,dict(mm),dict(ff),dict(ss)
 rows.append({**r,'tiles':tiles,'writable':writable,'mapping':m,'flips':f,'shifts':s,'initial_bytes':initial,'encoded_bytes':best,'budget':budget,'fits':best<=budget,'raw_sha256':sha256(raw)})
 (d/'packing.json').write_text(json.dumps(rows,indent=2));print({'frame':n,'final':best,'fits':best<=budget},flush=True)
