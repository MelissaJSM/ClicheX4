import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;a=d/'production06';shutil.copytree(d/'production05',a,dirs_exist_ok=True);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in pal],np.int32);src=Image.open(d/'compact2_generated.png').convert('RGBA');refs=json.loads((d/'compact2_reference.json').read_text());records=[];changed=set()
def save(n,v):save_image(v.tobytes(),(160,160),pal,a/f'frame_{n:03d}.png');changed.add(n)
def move(v,dx=0,dy=0):
 out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x+dx]=v[y,x];return out
def outline(v,color):
 mask=v!=0;p=np.pad(mask,1);edge=(p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:])&~mask;out=v.copy();out[edge]=color;return out
for i,r in enumerate(refs):
 n=r['frame'];box=(round(i%4*src.width/4),round(i//4*src.height/4),round((i%4+1)*src.width/4),round((i//4+1)*src.height/4));im=src.crop(box);v=np.array(im);yy,xx=np.nonzero(v[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));im=im.crop(bb)
 height={95:47,204:47,206:47,138:55,156:47}.get(n,r['old_native_size'][1]);scale=height/im.height;size=tuple(round(k*scale) for k in im.size);arr=quantize(im,size,rgb,128);yy,xx=np.nonzero(arr);ey,ex=np.nonzero((arr==7)&(np.indices(arr.shape)[0]<size[1]*.6));left=round(75-float(np.median(ex[ey<=ey.min()+1]))) if len(ex) else round(80-(xx.min()+xx.max())/2);foot={101:105,104:105,233:103}.get(n,102);top=foot-int(yy.max())
 if n==156:left=round(80-(xx.min()+xx.max())/2)
 out=np.zeros((160,160),np.uint8);out[top:top+size[1],left:left+size[0]]=arr;save(n,out);q=next(q for q in art['groups'] if q['frame']==n)
 for k in q['aliases']:
  if k!=n and q['part_slots'][str(k)]:save(k,move(out,*q['translations'][str(k)]))
 if n==135:save(136,out)
 if n==138:save(139,move(out,dy=-1))
 if n==231:save(232,move(out,dy=1))
 if n==156:save(157,outline(outline(move(out,dy=-1),14),6))
 if n==101:save(215,out);save(216,out)
 records.append({'frame':n,'source_box':box,'alpha_box':bb,'scale':scale,'size':size,'offset':[left,top],'opaque_pixels':int(np.count_nonzero(arr))});print(n,size,records[-1]['opaque_pixels'])
layout=json.loads((a/'layout.json').read_text());(a/'layout.json').write_text(json.dumps([r for r in layout if r['frame'] not in changed],indent=2));(a/'compact2_normalization.json').write_text(json.dumps(records,indent=2))
s=(d/'layout04.py').read_text().replace('production04','production06').replace("q['kind']=='effect'","q['kind'] in ('effect','original_grid')");(d/'layout06.py').write_text(s)
s=(d/'optimize04.py').read_text().replace('production04','production06');(d/'optimize06.py').write_text(s)
