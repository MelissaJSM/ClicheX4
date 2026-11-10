"""몸 크기·알파·얼굴·외곽을 고정한 채 의상 내부 근접 팔레트 명암만 정리."""
import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production06';shutil.copytree(d/'production05',a);packing=json.loads((a/'packing.json').read_text());r=next(r for r in packing if r['frame']==154);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
arc=(ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][154];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128);target=np.array(Image.open(a/'frame_154.png'));before=target.copy();changes=[]
def cost(t):
 search=VariantSearch(dec.data,desc['tile_count'],t,t,r['writable']);raw,packed=search.pack(r['rects'],[],[],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});return encoded_cost(packed),sha256(raw)
current,_=cost(target)
for step in range(24):
 if current<=r['budget']:break
 candidates=[]
 for y,x in zip(*np.nonzero(np.isin(target,[5,6,9,14,8]))):
  if y<44 or not np.all(target[y-1:y+2,x-1:x+2]):continue
  old=int(target[y,x]);neighbors={int(target[y-1,x]),int(target[y+1,x]),int(target[y,x-1]),int(target[y,x+1])}
  for new in neighbors&{5,6,9,14,8}-{old}:
   distance=int(((rgb[old]-rgb[new])**2).sum())
   if distance>7000:continue
   target[y,x]=new;c,_=cost(target);target[y,x]=old
   if c<current:candidates.append((c,distance,int(y),int(x),old,new))
 if not candidates:break
 c,dist,y,x,old,new=min(candidates);target[y,x]=new;changes.append({'x':x,'y':y,'from':old,'to':new,'encoded_bytes':c});current=c
save_image(target.tobytes(),(96,80),pal,a/'frame_154.png');assert np.array_equal(before!=0,target!=0) and np.array_equal(before[:44],target[:44]);r['encoded_bytes'],r['raw_sha256']=cost(target);r['fits']=r['encoded_bytes']<=r['budget'];(a/'packing.json').write_text(json.dumps(packing,indent=2));(a/'palette_consolidation.json').write_text(json.dumps({'frame':154,'geometry_alpha_head_outline_preserved':True,'changes':changes,'encoded_bytes':current},indent=2));print(json.dumps({'changes':len(changes),'encoded':current,'budget':r['budget'],'fits':r['fits']}))
