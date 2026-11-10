import json,sys,shutil,random,math
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production08';shutil.copytree(d/'production07',a);packing=json.loads((a/'packing.json').read_text());r=next(r for r in packing if r['frame']==154);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
arc=(ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][154];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128);target=np.array(Image.open(a/'frame_154.png'));before=np.array(Image.open(d/'production04/frame_154.png'));choices=[]
for y,x in zip(*np.nonzero(np.isin(before,[5,6,9,14,8]))):
 if y<44 or not np.all(before[y-1:y+2,x-1:x+2]):continue
 old=int(before[y,x]);neighbors=set(map(int,before[y-1:y+2,x-1:x+2].ravel()));colors=[v for v in neighbors&{5,6,9,14,8} if int(((rgb[old]-rgb[v])**2).sum())<=7000]
 if len(colors)>1:choices.append((y,x,colors))
def cost(t):
 search=VariantSearch(dec.data,desc['tile_count'],t,t,r['writable']);raw,packed=search.pack(r['rects'],[],[],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});return encoded_cost(packed),sha256(raw)
current,_=cost(target);best=current;winner=target.copy();rng=random.Random(1548)
for step in range(24000):
 if best<=906:break
 if step%1000==0:target=winner.copy();current=best
 y,x,colors=rng.choice(choices);old=target[y,x];target[y,x]=rng.choice(colors)
 if np.count_nonzero(target!=before)>28:target[y,x]=old;continue
 c,_=cost(target);temp=.2+1.5*(1-(step%1000)/1000)
 if c<=current or rng.random()<math.exp((current-c)/temp):current=c
 else:target[y,x]=old
 if c<best:best=c;winner=target.copy()
save_image(winner.tobytes(),(96,80),pal,a/'frame_154.png');r['encoded_bytes'],r['raw_sha256']=cost(winner);r['fits']=r['encoded_bytes']<=r['budget'];(a/'packing.json').write_text(json.dumps(packing,indent=2));yy,xx=np.nonzero(winner!=before);changes=[{'x':int(x),'y':int(y),'from':int(before[y,x]),'to':int(winner[y,x])} for y,x in zip(yy,xx)];(a/'palette_consolidation.json').write_text(json.dumps({'frame':154,'geometry_alpha_head_outline_preserved':True,'changes':changes,'encoded_bytes':best},indent=2));print(json.dumps({'choices':len(choices),'changes':len(changes),'encoded':best,'fits':r['fits']}))
