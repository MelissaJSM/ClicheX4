from storage_common import *
from psx_variant_search import VariantSearch
import itertools
from concurrent.futures import ProcessPoolExecutor,as_completed
a=Path(__file__).parent/'production06'
def run(n):
 art,q,r,f,_,_,_,w=load(a,n)
 if q['kind']!='body':return {'frame':n,'skip':True}
 arc=(ROOT/art['parent']/'modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 old=np.array(Image.open(a/f'frame_{n:03}.png'));v=old.copy();search=VariantSearch(raw,f['tile_count'],v,v,w)
 m={int(k):v for k,v in r['mapping'].items()};fl={int(k):v for k,v in r['flips'].items()};sh={int(k):v for k,v in r['shifts'].items()};rgb=np.array([[(z>>s&31)*255//31 for s in (0,5,10)] for z in art['palette_words']],np.int32)
 choices=[(2,[2,15]),(3,[3,6]),(6,[6,9]),(5,[5,9]),(10,[10,11]),(11,[11,4]),(14,[14,5]),(8,[8,14])];best=None;fits=[]
 for vs in itertools.product(*(options for k,options in choices)):
  mp={k:z for (k,_),z in zip(choices,vs) if k!=z};v[:]=old
  for c,z in mp.items():v[(old==c)&(np.indices(v.shape)[0]>=77)]=z
  r0,data=search.pack(r['rects'],r['run_rects'],r['shot_rects'],m,fl,sh);cost=encoded_cost(data);dist=int(((rgb[v]-rgb[old])**2).sum());record={'frame':n,'mapping':mp,'cost':cost,'budget':q['budget'],'changed_pixels':int(np.count_nonzero(old!=v)),'distortion':dist}
  if best is None or (cost,dist)<(best['cost'],best['distortion']):best=record
  if cost<=q['budget']:fits.append(record)
 result={'frame':n,'best':best,'fitting':min(fits,key=lambda x:x['distortion']) if fits else None};(a/f'body_palette_probe_{n:03}.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 ns=[int(n) for n in sys.argv[1:]] or [135,136,137,138,139,204,205,206,207,141,142]
 with ProcessPoolExecutor(max_workers=3) as pool:
  for result in pool.map(run,ns):print(result,flush=True)
