import sys,json,random,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production10';shutil.copytree(d/'production08',a);arc=(ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];bank=graphics_bank(gfx,0,allow_bank_aliases=True);records=json.loads((a/'packing.json').read_text());r=next(r for r in records if r['frame']==154);n=154;desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);normal=np.array(Image.open(a/'frame_154.png'));writable=set(r['writable']);raw,rp,_,*_=pack_variant_pair(dec.data,desc['tile_count'],normal,normal,r['rects'],[],[],writable);assert sha256(raw)==r['raw_sha256'];mapping={int(k):v for k,v in r['mapping'].items()};flips={int(k):v for k,v in r['flips'].items()};shifts={int(k):v for k,v in r['shifts'].items()};packed=remap_tiles(raw,desc['tile_count'],mapping,flips,shifts);assignments={n:[(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,x,y in rp]};targets={n:normal};best=encoded_cost(packed);chosen=[];atlas,positions,_=indexed_atlas(packed,desc['tile_count']);options=[]
for t,left,top,flag in assignments[n]:
 for y in range(16):
  for x in range(16):
   idx=(t//16*16+y)*256+t%16*16+x
   if atlas[idx]:continue
   px=left+(15-x if flag&64 else x);py=top+(15-y if flag&128 else y)
   if not (0<=py<80 and 0<=px<96) or not normal[py,px]:continue
   change=[t,x,y,int(normal[py,px])]
   try:fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,[change],writable)
   except ValueError:continue
   off,shift=positions[idx];options.append((change,off,shift))
current=bytearray(packed);rng=random.Random(958)
for step in range(100):
 if best<=r['budget'] or not options:break
 scores=[]
 for change,off,shift in options:
  trial=current.copy();trial[off]|=change[3]<<shift;scores.append((encoded_cost(bytes(trial)),rng.random(),change,off,shift))
 cost,_,change,off,shift=min(scores)
 if cost>best:break
 chosen.append(change);current[off]|=change[3]<<shift;best=cost;options=[q for q in options if q[0]!=change]
assert bytes(current)==fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,chosen,writable)
r.update(encoded_bytes=best,fits=best<=r['budget'],overlap_fill=chosen);(a/'packing.json').write_text(json.dumps(records,indent=2));print(json.dumps({'cost':best,'budget':r['budget'],'duplicate_pixels':len(chosen),'fits':r['fits']}))
