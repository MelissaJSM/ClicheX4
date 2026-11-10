import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;a=d/'native04';shutil.copytree(d/'production02',a,dirs_exist_ok=True);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32);src=Image.open(d/'compact_generated.png').convert('RGBA');ns=[162,166,170,174,94,100,102,103,205,234]
for i,n in enumerate(ns):
 box=(round(i%5*src.width/5),[0,520][i//5],round((i%5+1)*src.width/5),[520,src.height][i//5]);im=src.crop(box);v=np.array(im);yy,xx=np.nonzero(v[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));im=im.crop(bb);v=np.array(im);gold=(v[:,:,0]>140)&(v[:,:,1]>75)&(v[:,:,1]<205)&(v[:,:,2]<105)&(v[:,:,3]>160);gold[int(im.height*.6):]=False;gy,gx=np.nonzero(gold);ear_y=20 if n==102 else 0;scale={162:40,166:36,170:42,174:46,94:39,100:41,102:50,103:47,205:47,234:44}[n]/im.height;size=tuple(round(k*scale) for k in im.size);arr=quantize(im,size,rgb,128);ey,ex=np.nonzero((arr==7)&(np.indices(arr.shape)[0]<size[1]*.6));left=round(43-float(np.median(ex[ey<=ey.min()+1]))) if len(ex) else round(48-size[0]/2);foot={162:56,166:56,170:60,174:66,94:64,100:64,102:65,103:64,205:62,234:63}[n];yy,xx=np.nonzero(arr);top=foot-int(yy.max());canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr;save_image(canvas.tobytes(),(96,80),pal,a/f'frame_{n:03d}.png');q=next(r for r in art['frames'] if r['frame']==n);q.update(source='compact_generated.png',source_cell=box,source_box=bb,scale=scale,size=size,offset=[left,top]);print(n,size,'ear-eye',16,'foot',foot)
(a/'art.json').write_text(json.dumps(art,indent=2));s=(d/'assemble03.py').read_text(encoding='utf-8').replace("a=d/'production03'","a=d/'production04'").replace("d/'production02", "d/'native04")
(d/'assemble04.py').write_text(s,encoding='utf-8')
