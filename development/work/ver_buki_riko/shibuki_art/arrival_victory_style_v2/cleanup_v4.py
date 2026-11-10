from storage_common import *
from scipy.ndimage import binary_dilation
from psx_variant_search import VariantSearch
from scripts.extract_zero import save_image
from concurrent.futures import ProcessPoolExecutor,as_completed
import random
a=Path(__file__).parent/'production04'

def run(n):
 art,q,r,f,_,_,_,w=load(a,n)
 arc=(ROOT/art['parent']/'modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 if q['effect_tiles']:raw=recolor_tiles(raw,f['tile_count'],q['effect_tiles'],art['effect_index_mapping'])
 old=np.array(Image.open(a/f'frame_{n:03}.png'));v=old.copy();search=VariantSearch(raw,f['tile_count'],v,v,w)
 mp={int(k):v for k,v in r['mapping'].items()};fl={int(k):v for k,v in r['flips'].items()};sh={int(k):v for k,v in r['shifts'].items()}
 # Keep the geometry search; rebuild color data and overlap ownership from scratch.
 for k in ('post_mapping','post_flips','post_shifts','overlap_fill'):r.pop(k,None)
 def cost():
  raw0,data=search.pack(r['rects'],r['run_rects'],r['shot_rects'],mp,fl,sh);return encoded_cost(data),sha256(raw0)
 initial,h=cost();best=initial;limit=round(np.count_nonzero(v)*.22);rng=random.Random(28000+n)
 rgb=np.array([[(z>>s&31)*255//31 for s in (0,5,10)] for z in art['palette_words']],np.int32)
 mask=v!=0;p=np.pad(mask,1);edge=mask&~(p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:])
 protected=edge|(v==15)|binary_dilation(np.isin(v,[7,12,13]),iterations=1)
 families=[{2,5,8,14},{3,6,9},{1,4,10,11}];family={i:s for s in families for i in s};yy,xx=np.nonzero(mask&~protected)
 history=[]
 for sweep in range(12):
  if best<=q['budget']:break
  options=[]
  for y,x in zip(yy,xx):
   color=int(v[y,x]);neigh=v[y-1:y+2,x-1:x+2].flatten();cross=[v[y-1,x],v[y+1,x],v[y,x-1],v[y,x+1]]
   for new in set(neigh.tolist())&family.get(color,set()):
    if new==color or np.count_nonzero(neigh==new)<3 or cross.count(new)<1:continue
    dist=float(np.linalg.norm(rgb[new]-rgb[int(old[y,x])]))
    if dist>120:continue
    options.append((dist,rng.random(),int(y),int(x),color,new))
  accepted=0
  for dist,_,y,x,color,new in sorted(options):
   if best<=q['budget']:break
   if v[y,x]!=color:continue
   v[y,x]=new
   if np.count_nonzero(v!=old)>limit:v[y,x]=color;continue
   value,h0=cost()
   if value<best or (value==best and np.count_nonzero(v[y-1:y+2,x-1:x+2]==new)>=4):
    best=value;h=h0;history.append([x,y,color,new]);accepted+=1
   else:v[y,x]=color
  if not accepted:break
 assert np.array_equal(old[protected],v[protected]) and np.array_equal(old!=0,v!=0)
 for k in q['aliases']:
  if not q['part_slots'][str(k)]:continue
  dx,dy=q['translations'][str(k)];out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x+dx]=v[y,x];save_image(out.tobytes(),(160,160),art['palette_words'],a/f'frame_{k:03}.png')
 r.update(raw_sha256=h,encoded_bytes=best,fits=best<=q['budget']);(a/f'packing_{n:03}.json').write_text(json.dumps(r,indent=2))
 record={'frame':n,'initial':initial,'final':best,'budget':q['budget'],'fits':r['fits'],'changed_pixels':int(np.count_nonzero(v!=old)),'opaque':int(np.count_nonzero(v)),'silhouette_face_outline_preserved':True,'operations':history};(a/f'cluster_cleanup_{n:03}.json').write_text(json.dumps(record,indent=2));return {k:v for k,v in record.items() if k!='operations'}

if __name__=='__main__':
 ns=list(map(int,sys.argv[1:]))
 if not ns:ns=[q['frame'] for q in json.loads((a/'art.json').read_text())['groups'] if q['kind']=='body' and not json.loads((a/f"packing_{q['frame']:03}.json").read_text())['fits']]
 with ProcessPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(run,n):n for n in ns}
  for f in as_completed(jobs):
   try:print(f.result(),flush=True)
   except Exception as e:print({'frame':jobs[f],'error':repr(e)},flush=True)
