from storage_common import *
from psx_variant_search import VariantSearch
from scripts.extract_zero import save_image
from scipy.ndimage import binary_dilation
import itertools
from concurrent.futures import ProcessPoolExecutor,as_completed
a=Path(__file__).parent/'production14'
def run(n):
 art,q,r,f,_,_,_,w=load(a,n)
 arc=(ROOT/art['parent']/'modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 if q['effect_tiles']:raw=recolor_tiles(raw,f['tile_count'],q['effect_tiles'],art['effect_index_mapping'])
 old=np.array(Image.open(a/f'frame_{n:03}.png'));v=old.copy();search=VariantSearch(raw,f['tile_count'],v,v,w);protected=binary_dilation(np.isin(old,[7,12,13]),iterations=1)|(old==15)
 mp={int(k):v for k,v in r['mapping'].items()};fl={int(k):v for k,v in r['flips'].items()};sh={int(k):v for k,v in r['shifts'].items()}
 rgb=np.array([[(z>>s&31)*255//31 for s in (0,5,10)] for z in art['palette_words']],np.int32)
 def cost():
  r0,data=search.pack(r['rects'],r['run_rects'],r['shot_rects'],mp,fl,sh);return encoded_cost(data),sha256(r0)
 choices=[(5,9),(6,9),(9,5),(14,5),(8,2),(2,8),(11,4),(10,4),(1,4),(6,5)];winners=[];smallest=(100000,None)
 for k in range(6):
  for combo in itertools.combinations(choices,k):
   m=dict(combo)
   if len(m)!=k:continue
   v[:]=old
   for c,d in m.items():v[(old==c)&~protected]=d
   value,h=cost()
   if value<smallest[0]:smallest=(value,m)
   if value<=q['budget']:
    distortion=int(((rgb[v]-rgb[old])**2).sum());winners.append((distortion,int(np.count_nonzero(v!=old)),m.copy(),value,h,v.copy()))
 if not winners:return {'frame':n,'fits':False,'best':smallest,'budget':q['budget']}
 score,changed,m,value,h,v=min(winners,key=lambda r:r[:2])
 for k in q['aliases']:
  if not q['part_slots'][str(k)]:continue
  dx,dy=q['translations'][str(k)];out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x+dx]=v[y,x];save_image(out.tobytes(),(160,160),art['palette_words'],a/f'frame_{k:03}.png')
 for key in ('post_mapping','post_flips','post_shifts','overlap_fill'):r.pop(key,None)
 r.update(raw_sha256=h,encoded_bytes=value,fits=True);(a/f'packing_{n:03}.json').write_text(json.dumps(r,indent=2));record={'frame':n,'mapping':m,'changed_pixels':changed,'distortion':score,'bytes':value,'budget':q['budget'],'fits':True};(a/f'tone_{n:03}.json').write_text(json.dumps(record,indent=2));return record
if __name__=='__main__':
 ns=list(map(int,sys.argv[1:]))
 with ProcessPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(run,n):n for n in ns}
  for f in as_completed(jobs):
   try:print(f.result(),flush=True)
   except Exception as e:print({'frame':jobs[f],'error':repr(e)},flush=True)
