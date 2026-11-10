"""실루엣·눈·피부·외곽선을 고정하고 가까운 색의 작은 내부 덩어리만 정돈."""
import json,sys,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from scipy.ndimage import label,binary_dilation
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream
from src.psx_sprite_batch import recolor_tiles
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production05'

def run(n):
 art=json.loads((a/'art.json').read_text());q=next(r for r in art['groups'] if r['frame']==n);r=json.loads((a/f'packing_{n:03d}.json').read_text());arc=(ROOT/art['parent']/'modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 if q['effect_tiles']:raw=recolor_tiles(raw,f['tile_count'],q['effect_tiles'],art['effect_index_mapping'])
 old=np.array(Image.open(a/f'frame_{n:03d}.png'));v=old.copy();search=VariantSearch(raw,f['tile_count'],v,v,q['writable']);mp={int(k):v for k,v in r['mapping'].items()};fl={int(k):v for k,v in r['flips'].items()};sh={int(k):v for k,v in r['shifts'].items()}
 def cost():
  raw0,packed=search.pack(r['rects'],r['run_rects'],r['shot_rects'],mp,fl,sh);return encoded_cost(packed),sha256(raw0)
 before,h=cost();best=before;changes=[];budget=q['budget'];opaque=np.count_nonzero(v);limit=round(opaque*.22)
 rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in art['palette_words']],np.int32)
 alpha=v!=0;pad=np.pad(alpha,1);edge=alpha&~(pad[:-2,1:-1]&pad[2:,1:-1]&pad[1:-1,:-2]&pad[1:-1,2:]);protected=edge|(v==15)|binary_dilation(np.isin(v,[7,12,13]),iterations=1)
 families={2:[8,14],3:[6,8],5:[6,9,14],6:[5,9],8:[2,14],9:[5,6],10:[11,4],11:[10,4],14:[5,8]}
 for passes in range(4):
  if best<=budget:break
  operations=[]
  for color,options in families.items():
   labels,count=label(v==color)
   for ident in range(1,count+1):
    yy,xx=np.nonzero(labels==ident)
    if len(xx)>4 or np.any(protected[yy,xx]):continue
    mask=labels==ident;around=binary_dilation(mask)&~mask;adj=set(v[around].tolist())
    for new in options:
     if new not in adj:continue
     distance=float(np.linalg.norm(rgb[color]-rgb[new]))
     if distance>112:continue
     operations.append((distance,len(xx),yy,xx,color,new))
  operations.sort(key=lambda r:(r[0],r[1]));accepted=0
  for dist,sz,yy,xx,color,new in operations:
   if best<=budget or len(changes)+sz>limit:break
   if not np.all(v[yy,xx]==color):continue
   v[yy,xx]=new
   value,h0=cost()
   if value<best:
    best=value;h=h0;accepted+=1;changes.extend([[int(x),int(y),int(color),int(new)] for y,x in zip(yy,xx)])
   else:v[yy,xx]=color
  if not accepted:break
 assert np.array_equal(old!=0,v!=0) and np.array_equal(old[protected],v[protected])
 for k in q['aliases']:
  if not q['part_slots'][str(k)]:continue
  dx,dy=q['translations'][str(k)];pic=np.zeros_like(v);yy,xx=np.nonzero(v);pic[yy+dy,xx+dx]=v[yy,xx];save_image(pic.tobytes(),(160,160),art['palette_words'],a/f'frame_{k:03d}.png')
 r.update(raw_sha256=h,encoded_bytes=best,fits=best<=budget);(a/f'packing_{n:03d}.json').write_text(json.dumps(r,indent=2));record={'frame':n,'initial':before,'final':best,'budget':budget,'fits':best<=budget,'changed_pixels':len(changes),'opaque_pixels':int(opaque),'silhouette_and_protected_pixels_unchanged':True,'operations':changes};(a/f'consolidation_{n:03d}.json').write_text(json.dumps(record,indent=2));return {k:v for k,v in record.items() if k!='operations'}

if __name__=='__main__':
 if not a.exists():shutil.copytree(d/'production04',a)
 art=json.loads((a/'art.json').read_text());ns=[]
 for q in art['groups']:
  p=a/f"packing_{q['frame']:03d}.json"
  if p.exists() and not json.loads(p.read_text())['fits'] and q['kind']=='body':ns.append(q['frame'])
 if len(sys.argv)>1:ns=list(map(int,sys.argv[1:]))
 with ProcessPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(run,n):n for n in ns}
  for job in as_completed(jobs):
   try:print(job.result(),flush=True)
   except Exception as e:print({'frame':jobs[job],'error':repr(e)},flush=True)
