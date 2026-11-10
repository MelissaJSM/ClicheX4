import json,sys,random,math,itertools,os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import recolor_tiles,pack_original_layout
from src.psx_paired_layout import pack_variant_pair
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production07'

def run(n):
 art=json.loads((a/'art.json').read_text());q=next(r for r in art['groups'] if r['frame']==n);arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t];f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];decoded=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128);raw=decoded.data
 if q['kind'] in ('effect','original_grid'):
  result=recolor_tiles(raw,f['tile_count'],q['writable'],art['effect_index_mapping']) if q['kind']=='effect' else pack_original_layout(raw,f['tile_count'],np.array(Image.open(a/f'frame_{n:03d}.png')),composition_frame(c,0,n),set(q['writable']))
  cost=encoded_cost(result);record={'frame':n,'kind':q['kind'],'encoded_bytes':cost,'budget':q['budget'],'fits':cost<=q['budget'],'raw_sha256':sha256(result)}
  (a/f'packing_{n:03d}.json').write_text(json.dumps(record,indent=2));return record
 layout=next(r for r in json.loads((a/'layout.json').read_text()) if r['frame']==n)
 if not layout['fits']:return {'frame':n,'fits':False,'reason':'layout'}
 target=np.array(Image.open(a/f'frame_{n:03d}.png'));other=np.array(Image.open(a/f'frame_{n+1:03d}.png')) if q['kind']=='pair' else target;w=q['writable'];rng=random.Random(1700+n)
 # Shared effect shapes remain intact but use the pale Shibuki effect indices.
 raw=recolor_tiles(raw,f['tile_count'],q['effect_tiles'],art['effect_index_mapping']) if q['effect_tiles'] else raw
 search=VariantSearch(raw,f['tile_count'],target,other,w);state={'rects':layout['rects'],'run_rects':layout.get('run_rects',[]),'shot_rects':layout.get('shot_rects',[]),'mapping':{str(t):t for t in w},'flips':{},'shifts':{}}
 def encode(r):
  raw0,packed=search.pack(r['rects'],r['run_rects'],r['shot_rects'],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});return encoded_cost(packed),sha256(raw0)
 found=False
 for attempt in range(700):
  try:cost,rawhash=encode(state);found=True;break
  except (ValueError,IndexError):
   state['rects']=json.loads(json.dumps(layout['rects']));rng.shuffle(state['rects'])
   if attempt>40:
    for rect in state['rects']:rect[rng.randrange(2)]+=rng.choice((-1,0,1))
 if not found:return {'frame':n,'fits':False,'reason':'initial GPU layout'}
 previous=a/f'packing_{n:03d}.json'
 if previous.exists():
  old=json.loads(previous.read_text())
  try:
   c0,h=encode(old)
   if c0<cost:state=old;cost=c0;rawhash=h
  except (ValueError,KeyError):pass
 initial=cost;best=cost;winner=json.loads(json.dumps(state));besthash=rawhash
 for step in range(18000):
  if best<=q['budget']:break
  if step%3000==0:state=json.loads(json.dumps(winner));cost=best
  r=json.loads(json.dumps(state));kind=rng.randrange(5);gs=[k for k in ('rects','run_rects','shot_rects') if r[k]];key=rng.choice(gs)
  if kind==0:
   if len(r[key])<2:continue
   i,j=rng.sample(range(len(r[key])),2);r[key][i],r[key][j]=r[key][j],r[key][i]
  elif kind==1:
   i=rng.randrange(len(r[key]));r[key][i][rng.randrange(2)]+=rng.choice((-2,-1,1,2))
  elif kind==2:
   if len(w)<2:continue
   i,j=map(str,rng.sample(w,2));r['mapping'][i],r['mapping'][j]=r['mapping'][j],r['mapping'][i]
  elif kind==3:
   i=str(rng.choice(w));r['flips'][i]=r['flips'].get(i,0)^rng.choice((64,128,192))
  else:
   i=str(rng.choice(w));v=r['shifts'].get(i,[0,0]).copy();v[rng.randrange(2)]+=rng.choice((-1,1));r['shifts'][i]=v
  try:value,h=encode(r)
  except (ValueError,IndexError):continue
  temp=.2+2*(1-(step%3000)/3000)
  if value<=cost or rng.random()<math.exp((cost-value)/temp):state=r;cost=value
  if value<best:best=value;winner=r;besthash=h
 packed,rp,sp,blank,_=pack_variant_pair(raw,f['tile_count'],target,other,winner['rects'],winner['run_rects'],winner['shot_rects'],set(w));assert sha256(packed)==besthash
 winner.update(frame=n,kind=q['kind'],writable=w,run_records=rp,shot_records=sp,blank=blank,raw_sha256=besthash,encoded_bytes=best,budget=q['budget'],initial=initial,fits=best<=q['budget']);previous.write_text(json.dumps(winner,indent=2));return {k:winner[k] for k in ('frame','initial','encoded_bytes','budget','fits')}

if __name__=='__main__':
 art=json.loads((a/'art.json').read_text());ns=[r['frame'] for r in art['groups']]
 if len(sys.argv)>1:ns=[int(v) for v in sys.argv[1:]]
 with ProcessPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(run,n):n for n in ns}
  for f in as_completed(jobs):
   try:print(f.result(),flush=True)
   except Exception as e:print({'frame':jobs[f],'error':repr(e)},flush=True)
