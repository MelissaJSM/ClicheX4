import sys,json,shutil,random,math
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production12';shutil.copytree(d/'production11',a);rows=json.loads((a/'packing.json').read_text());r=next(r for r in rows if r['frame']==154);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32);target=np.array(Image.open(a/'frame_154.png'));original=np.array(Image.open(d/'production04/frame_154.png'));arc=(ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][154];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128);w=set(r['writable']);raw,rp,_,*_=pack_variant_pair(dec.data,desc['tile_count'],target,target,r['rects'],[],[],w);m={int(k):v for k,v in r['mapping'].items()};f={int(k):v for k,v in r['flips'].items()};s={int(k):v for k,v in r['shifts'].items()};raw=remap_tiles(raw,desc['tile_count'],m,f,s);records=[(m[t],x-s.get(t,(0,0))[0],y-s.get(t,(0,0))[1],f.get(t,0)) for t,x,y in rp];raw=fill_redundant_pixels(raw,desc['tile_count'],{154:records},{154:target},r.get('overlap_fill',[]),w);pm={int(k):v for k,v in r['post_mapping'].items()};pf={int(k):v for k,v in r['post_flips'].items()};raw=remap_tiles(raw,desc['tile_count'],pm,pf);final=[(pm[t],x,y,flag^pf.get(t,0)) for t,x,y,flag in records];atlas,pos,_=indexed_atlas(raw,desc['tile_count']);locations={}
for t,left,top,flag in final:
 for y in range(16):
  for x in range(16):
   idx=(t//16*16+y)*256+t%16*16+x
   if not atlas[idx]:continue
   px=left+(15-x if flag&64 else x);py=top+(15-y if flag&128 else y);locations.setdefault((py,px),[]).append(pos[idx])
choices=[]
for (y,x),loc in locations.items():
 old=int(original[y,x])
 if y<44 or old not in (5,6,8,9,14) or not np.all(original[y-1:y+2,x-1:x+2]):continue
 colors=[v for v in set(map(int,original[y-1:y+2,x-1:x+2].ravel()))&{5,6,8,9,14} if int(((rgb[old]-rgb[v])**2).sum())<=7000]
 if len(colors)>1:choices.append((y,x,colors,loc))
current=bytearray(raw);cost=encoded_cost(bytes(current));best=cost;win=current.copy();wt=target.copy();rng=random.Random(15412)
for step in range(60000):
 if best<=906:break
 if step%3000==0:current=win.copy();target=wt.copy();cost=best
 y,x,colors,loc=rng.choice(choices);v=rng.choice(colors);old=int(target[y,x]);trial=current.copy()
 for off,shift in loc:trial[off]=(trial[off]&~(15<<shift))|(v<<shift)
 target[y,x]=v
 if np.count_nonzero(target!=original)>40:target[y,x]=old;continue
 c=encoded_cost(bytes(trial));temp=.2+2*(1-step%3000/3000)
 if c<=cost or rng.random()<math.exp((cost-c)/temp):current=trial;cost=c
 else:target[y,x]=old
 if c<best:best=c;win=trial.copy();wt=target.copy()
save_image(wt.tobytes(),(96,80),pal,a/'frame_154.png');raw2,*_=pack_variant_pair(dec.data,desc['tile_count'],wt,wt,r['rects'],[],[],w);r['raw_sha256']=sha256(raw2)
for ch in r.get('overlap_fill',[]):
 t,x,y,_=ch;row=next(q for q in records if q[0]==t);_,left,top,flag=row;ch[3]=int(wt[top+(15-y if flag&128 else y),left+(15-x if flag&64 else x)])
r.update(encoded_bytes=best,fits=best<=906);(a/'packing.json').write_text(json.dumps(rows,indent=2));yy,xx=np.nonzero(wt!=original);changes=[{'x':int(x),'y':int(y),'from':int(original[y,x]),'to':int(wt[y,x])} for y,x in zip(yy,xx)];(a/'palette_consolidation.json').write_text(json.dumps({'frame':154,'geometry_alpha_head_outline_preserved':True,'changes':changes,'encoded_bytes':best},indent=2));print({'encoded':best,'changes':len(changes),'fits':r['fits']})
