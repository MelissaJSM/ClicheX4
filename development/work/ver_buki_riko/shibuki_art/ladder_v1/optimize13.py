import json,sys,random,math,itertools
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from src.psx_paired_layout import pack_variant_pair
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production13';parent=ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z';arc=(parent/'modified.arc').read_bytes();manifest=json.loads((parent/'manifest.json').read_text());assert sha256(arc)==manifest['modified_archive_sha256']
entry=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[entry['offset']:entry['offset']+entry['size']];bank=graphics_bank(g,0,allow_bank_aliases=True)
layouts=json.loads((a/'layout.json').read_text());plan=json.loads((d/'plan.json').read_text());previous=json.loads((a/'packing.json').read_text()) if (a/'packing.json').exists() else [];records=[]
for n in (143,144,146,149,151,153,154,155,183):
 q=next(r for r in plan['groups'] if r['frame']==n)
 if n==149:q={**q,'writable':list(range(11))}
 n=q['frame'];desc=bank['frames'][n];decoded=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128);target=np.array(Image.open(a/f'frame_{n:03d}.png'));w=q['writable'];search=VariantSearch(decoded.data,desc['tile_count'],target,np.array(Image.open(a/'frame_150.png')) if n==149 else target,w);layout=next(r for r in layouts if r['frame']==n);assert layout['fits'];rng=random.Random(n+771)
 state={'rects':layout['rects'],'run_rects':layout.get('run_rects',[]),'shot_rects':layout.get('shot_rects',[]),'mapping':{str(t):t for t in w},'flips':{},'shifts':{}}
 def encode(r):
  raw,packed=search.pack(r['rects'],r.get('run_rects',[]),r.get('shot_rects',[]),{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});return encoded_cost(packed),sha256(raw)
 try:cost,rawhash=encode(state)
 except ValueError:
  for perm in itertools.permutations(state['rects']):
   state['rects']=list(perm)
   try:cost,rawhash=encode(state);break
   except ValueError:continue
  else:raise ValueError(f'No safe GPU edge layout for {n}')
 old=next((r for r in previous if r['frame']==n),None)
 if old:
  try:
   c,h=encode(old)
   if c<cost:state=old;cost=c;rawhash=h
  except ValueError:pass
 initial=cost;best=cost;winner=json.loads(json.dumps(state));besthash=rawhash
 for step in range(60000):
  if best<=q['budget']:break
  if step%3000==0:state=json.loads(json.dumps(winner));cost=best
  r=json.loads(json.dumps(state));kind=rng.randrange(5)
  if kind==0:
   i,j=rng.sample(range(len(r['rects'])),2);r['rects'][i],r['rects'][j]=r['rects'][j],r['rects'][i]
  elif kind==1:
   key=rng.choice([k for k in ('rects','run_rects','shot_rects') if r.get(k)]);i=rng.randrange(len(r[key]));r[key][i][rng.randrange(2)]+=rng.choice((-2,-1,1,2))
  elif kind==2:
   i,j=map(str,rng.sample([t for t in w if t or n not in (144,146,149,151)],2));r['mapping'][i],r['mapping'][j]=r['mapping'][j],r['mapping'][i]
  elif kind==3:
   i=str(rng.choice([t for t in w if t or n not in (144,146,149,151)]));r['flips'][i]=r['flips'].get(i,0)^rng.choice((64,128,192))
  else:
   i=str(rng.choice([t for t in w if t or n not in (144,146,149,151)]));v=r['shifts'].get(i,[0,0]).copy();v[rng.randrange(2)]+=rng.choice((-1,1));r['shifts'][i]=v
  try:value,h=encode(r)
  except (ValueError,IndexError):continue
  temp=.2+2*(1-(step%3000)/3000)
  if value<=cost or rng.random()<math.exp((cost-value)/temp):state=r;cost=value
  if value<best:best=value;winner=r;besthash=h
 raw,rp,_,blank,_=pack_variant_pair(decoded.data,desc['tile_count'],target,np.array(Image.open(a/'frame_150.png')) if n==149 else target,winner['rects'],winner.get('run_rects',[]),winner.get('shot_rects',[]),set(w));assert sha256(raw)==besthash
 winner.update(frame=n,writable=w,tiles=[t for t,x,y in rp],blank=blank,raw_sha256=besthash,encoded_bytes=best,budget=q['budget'],initial=initial,fits=best<=q['budget']);records.append(winner)
 print({'frame':n,'initial':initial,'final':best,'budget':q['budget'],'fits':winner['fits']},flush=True)
 (a/'packing.json').write_text(json.dumps(records+[r for r in previous if r['frame']>n],indent=2),encoding='utf-8')
