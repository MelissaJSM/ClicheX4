from storage_common import *
from psx_variant_search import VariantSearch
import itertools,random,math
a=Path(__file__).parent/'production01';n=97
art,q,r,f,_,_,targets,w=load(a,n);arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g=next(arc[e['offset']:e['offset']+e['size']] for e in es if int(e['type'],16)==2);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;search=VariantSearch(raw,f['tile_count'],targets[n],targets[n],w)
yy,xx=np.nonzero(targets[n]);best=r['encoded_bytes'];winner=None;rng=random.Random(9104)
for top in range(int(yy.max())-47,int(yy.min())+1):
 for left in range(int(xx.max())-31,int(xx.min())+1):
  rects=[[left+x,top+y] for y in [0,16,32] for x in [0,16]];mapping={t:t for t in w};flips={};shifts={}
  cost=9999
  for ids in itertools.permutations([1,2,3,4,5,6]):
   m={0:0,**dict(zip(range(1,7),ids))};raw0,packed=search.pack(rects,[],[],m,{},{});value=encoded_cost(packed)
   if value<cost:cost=value;mapping=m
  current=cost;cm=dict(mapping);cf={};cs={}
  for step in range(9000):
   if best<=q['budget']:break
   m=dict(cm);fl=dict(cf);sh=dict(cs);kind=rng.randrange(3)
   if kind==0:
    u,v=rng.sample(sorted(w),2);m[u],m[v]=m[v],m[u]
   elif kind==1:
    t=rng.choice(sorted(w));fl[t]=fl.get(t,0)^rng.choice([64,128,192])
   else:
    t=rng.choice(sorted(w));v=list(sh.get(t,[0,0]));v[rng.randrange(2)]+=rng.choice([-1,1]);sh[t]=v
   try:raw0,packed=search.pack(rects,[],[],m,fl,sh);value=encoded_cost(packed)
   except ValueError:continue
   temp=.1+2.8*(1-step/9000)
   if value<=current or rng.random()<math.exp((current-value)/temp):current,cm,cf,cs=value,m,fl,sh
   if value<best:best=value;winner={'rects':rects,'run_rects':[],'shot_rects':[],'mapping':m,'flips':fl,'shifts':sh,'raw_sha256':sha256(raw0)};print({'best':best,'grid':[left,top]},flush=True)
  if best<=q['budget']:break
 if best<=q['budget']:break
if winner:
 raw0,rp,sp,blank,_=pack_variant_pair(raw,f['tile_count'],targets[n],targets[n],winner['rects'],[],[],w);assert sha256(raw0)==winner['raw_sha256'];winner.update(frame=n,kind=q['kind'],writable=sorted(w),run_records=rp,shot_records=sp,blank=blank,encoded_bytes=best,budget=q['budget'],initial=r['encoded_bytes'],fits=best<=q['budget']);(a/f'packing_{n:03}.json').write_text(json.dumps(winner,indent=2))
print({'final':best,'fits':best<=q['budget']})
