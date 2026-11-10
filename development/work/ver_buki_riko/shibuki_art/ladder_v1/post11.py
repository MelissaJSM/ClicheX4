import sys,json,random,shutil,math
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production11';shutil.copytree(d/'production10',a,dirs_exist_ok=True);arc=(ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][154];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128);rows=json.loads((a/'packing.json').read_text());r=next(r for r in rows if r['frame']==154);w=r['writable'];target=np.array(Image.open(a/'frame_154.png'));raw,rp,_,*_=pack_variant_pair(dec.data,desc['tile_count'],target,target,r['rects'],[],[],set(w));m={int(k):v for k,v in r['mapping'].items()};f={int(k):v for k,v in r['flips'].items()};s={int(k):v for k,v in r['shifts'].items()};raw=remap_tiles(raw,desc['tile_count'],m,f,s);records=[(m[t],x-s.get(t,(0,0))[0],y-s.get(t,(0,0))[1],f.get(t,0)) for t,x,y in rp];raw=fill_redundant_pixels(raw,desc['tile_count'],{154:records},{154:target},r.get('overlap_fill',[]),set(w));atlas,pos,_=indexed_atlas(raw,desc['tile_count']);tiles={t:np.array([list(atlas[(t//16*16+y)*256+t%16*16:(t//16*16+y)*256+t%16*16+16]) for y in range(16)],np.uint8) for t in w};off={t:np.array([[pos[(t//16*16+y)*256+t%16*16+x][0] for x in range(0,16,2)] for y in range(16)]) for t in w};base=np.frombuffer(raw,np.uint8).copy()
def cost(mapping,flips):
 out=base.copy()
 for t in w:
  tile=tiles[t];flag=flips[t];dest=mapping[t]
  if flag&64:tile=tile[:,::-1]
  if flag&128:tile=tile[::-1,:]
  if dest%16==0 and (flag&64 or tile[:,0].any()):return 99999
  if flag&128 and dest//16%16==0 and tile[0].any():return 99999
  out[off[dest]]=tile[:,::2]|(tile[:,1::2]<<4)
 return encoded_cost(out.tobytes())
mapping={t:t for t in w};flips={t:0 for t in w};current=cost(mapping,flips);best=current;win=(mapping.copy(),flips.copy());rng=random.Random(15411)
for step in range(12000):
 if best<=906:break
 if step%1000==0:mapping=win[0].copy();flips=win[1].copy();current=best
 mm=mapping.copy();ff=flips.copy()
 if rng.randrange(2):i,j=rng.sample(w[1:],2);mm[i],mm[j]=mm[j],mm[i]
 else:i=rng.choice(w[1:]);ff[i]^=rng.choice((64,128,192))
 c=cost(mm,ff)
 if c<=current or rng.random()<math.exp((current-c)/2):mapping=mm;flips=ff;current=c
 if c<best:best=c;win=(mm,ff)
assert encoded_cost(remap_tiles(raw,desc['tile_count'],win[0],win[1]))==best
r.update(post_mapping=win[0],post_flips=win[1],encoded_bytes=best,fits=best<=906);(a/'packing.json').write_text(json.dumps(rows,indent=2));print({'cost':best,'fits':r['fits']})
