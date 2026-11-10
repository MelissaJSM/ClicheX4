from storage_common import *
from psx_variant_search import VariantSearch
from src.psx_paired_layout import pack_variant_pair
import random,copy
a=Path(__file__).parent/'production01';n=97
art,q,r,f,_,_,targets,w=load(a,n)
arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g=next(arc[e['offset']:e['offset']+e['size']] for e in es if int(e['type'],16)==2);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
search=VariantSearch(raw,f['tile_count'],targets[n],targets[n],w);rng=random.Random(2877);best=r['encoded_bytes'];winner=None
yy,xx=np.nonzero(targets[n]);positions=[(x,y) for x in range(int(xx.min())-12,int(xx.max())+1) for y in range(int(yy.min())-12,int(yy.max())+1)];rng.shuffle(positions)
for x,y in positions:
    rects=[[x,y]]+r['rects']
    if len(rects)>len(w):continue
    for attempt in range(3):
        m={t:t for t in w};fl={};sh={}
        if attempt:
            ids=list(w);rng.shuffle(ids);m=dict(zip(sorted(w),ids))
        try:raw0,packed=search.pack(rects,[],[],m,fl,sh)
        except ValueError:continue
        cost=encoded_cost(packed)
        if cost<best:best=cost;winner={'rects':rects,'run_rects':[],'shot_rects':[],'mapping':m,'flips':fl,'shifts':sh,'raw_sha256':sha256(raw0)};print(best,flush=True)
        if best<=q['budget']:break
    if best<=q['budget']:break
if winner:
    raw0,rp,sp,blank,_=pack_variant_pair(raw,f['tile_count'],targets[n],targets[n],winner['rects'],[],[],w)
    assert sha256(raw0)==winner['raw_sha256']
    winner.update(frame=n,kind=q['kind'],writable=sorted(w),run_records=rp,shot_records=sp,blank=blank,encoded_bytes=best,budget=q['budget'],initial=r['encoded_bytes'],fits=best<=q['budget'])
    (a/f'packing_{n:03}.json').write_text(json.dumps(winner,indent=2))
print({'final':best,'budget':q['budget']})
