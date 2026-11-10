from storage_common import *
from psx_variant_search import VariantSearch
import itertools
p=Path(__file__).parent;a=p/'production01';n=97
art,q,r,f,_,_,targets,w=load(a,n);src=targets[n]
arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g=next(arc[e['offset']:e['offset']+e['size']] for e in es if int(e['type'],16)==2);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
ops=[(2,15,0),(6,9,76),(12,13,76),(11,10,76),(14,5,82),(8,14,82)]
records=[]
for flags in itertools.product([False,True],repeat=len(ops)):
    dst=src.copy()
    for use,(old,new,y) in zip(flags,ops):
        if use:dst[y:][src[y:]==old]=new
    search=VariantSearch(raw,f['tile_count'],dst,dst,w)
    raw0,packed=search.pack(r['rects'],[],[],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()})
    records.append({'operations':[v for flag,v in zip(flags,ops) if flag],'cost':encoded_cost(packed),'pixels':int(np.count_nonzero(dst!=src))})
records.sort(key=lambda r:(r['cost'],r['pixels']));(p/'palette_probe.json').write_text(json.dumps(records,indent=2));print(records[:10])
