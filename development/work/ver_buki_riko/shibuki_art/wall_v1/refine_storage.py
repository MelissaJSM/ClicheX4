"""그림 픽셀은 그대로 두고 분할 사각형과 저장 순서만 탐색한다."""
import sys,json,random,math,argparse
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles
from src.psx_compress import encode_stream
p=argparse.ArgumentParser();p.add_argument('frame',type=int);p.add_argument('--steps',type=int,default=5000);p.add_argument('--seed',type=int,default=0);p.add_argument('--fast-cost',action='store_true');p.add_argument('--art-name',default='paired02');args=p.parse_args();n=args.frame
if args.fast_cost:
 sys.path.insert(0,str(ROOT/'work/tools'));from psx_compress_cost import encoded_cost
else:
 def encoded_cost(raw):return len(encode_stream(raw))
d=Path(__file__).parent;art=d/args.art_name;previous=json.loads((art/'packing.json').read_text());old=next(r for r in previous if r['frame']==n)
fallback=old
cached=d/f'geometry_{n:03d}.json' if args.art_name=='paired02' else art/f'geometry_{n:03d}.json'
if cached.exists():
 candidate=json.loads(cached.read_text())
 if candidate['encoded_bytes']<old['encoded_bytes'] or old.get('overlap_fill') or old.get('post_mapping'):old=candidate
arc=(ROOT/'out/ver_buki_riko/shibuki_dash_20261026T113618370649Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128)
a=np.array(Image.open(art/f'run_{n:03d}.png'));b=np.array(Image.open(art/f'shoot_{n:03d}.png'));writable={int(t) for t in old['mapping']};rng=random.Random(1005+n+args.seed);best=old['encoded_bytes'];current=best;winner=old;state=old
sys.path.insert(0,str(ROOT/'work/tools'));from psx_variant_search import VariantSearch
fastpack=VariantSearch(dec.data,desc['tile_count'],a,b,writable)
def packing(r):
 return fastpack.pack(r['common_rects'],r['variant_run_rects'],r['variant_shot_rects'],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()})
raw,modified=packing(old)
if sha256(raw)!=old['raw_sha256']:old=fallback;raw,modified=packing(old)
assert sha256(raw)==old['raw_sha256']
best=encoded_cost(modified);assert best==old['encoded_bytes'];current=best;winner=old;state=old
for step in range(args.steps):
 if best<=old['budget']:break
 r=json.loads(json.dumps(state));kind=rng.randrange(6)
 if kind in (0,1):
  group=rng.choice(('common_rects','common_rects','variant_run_rects','variant_shot_rects'));i=rng.randrange(len(r[group]));axis=rng.randrange(2);r[group][i][axis]+=rng.choice((-3,-2,-1,1,2,3))
 elif kind==2:
  group='common_rects';i,j=rng.sample(range(len(r[group])),2);r[group][i],r[group][j]=r[group][j],r[group][i]
 elif kind==3:
  i,j=map(str,rng.sample(sorted(writable),2));r['mapping'][i],r['mapping'][j]=r['mapping'][j],r['mapping'][i]
 elif kind==4:
  i=str(rng.choice(sorted(writable)));r['flips'][i]=r['flips'].get(i,0)^rng.choice((64,128,192))
 else:
  i=str(rng.choice(sorted(writable)));xy=list(r['shifts'].get(i,[0,0]));xy[rng.randrange(2)]+=rng.choice((-1,1));r['shifts'][i]=xy
 try:
  raw,modified=packing(r);cost=encoded_cost(modified)
 except (ValueError,IndexError):continue
 temp=.5+8*(1-step/args.steps)
 if cost<=current or rng.random()<math.exp((current-cost)/temp):state=r;current=cost
 if cost<best:
  best=cost;winner={**r,'encoded_bytes':cost,'fits':cost<=old['budget'],'raw_sha256':sha256(raw)};cached.write_text(json.dumps(winner,indent=2));print({'frame':n,'step':step,'best':best,'budget':old['budget']},flush=True)
print({'frame':n,'final':best,'fits':best<=old['budget']})
