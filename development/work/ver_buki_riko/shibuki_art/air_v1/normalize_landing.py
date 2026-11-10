import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'normalized02';out.mkdir(exist_ok=True)
for f in (d/'normalized01').glob('air_*.png'):shutil.copyfile(f,out/f.name)
art=json.loads((d/'normalized01/art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
im=Image.open(d/'landing_generated.png').convert('RGBA');crops=[]
for i in range(3):
 c=im.crop((im.width*i//3,0,im.width*(i+1)//3,im.height));a=np.array(c);yy,xx=np.nonzero(a[:,:,3]>=128);crops.append(c.crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1)))
scale=47/crops[0].height
for n,c in zip((49,51,53),crops):
 size=tuple(round(v*scale) for v in c.size);a=quantize(c,size,rgb,64);ey,ex=np.nonzero(a==7);x=round(47-np.median(ex));y=63-size[1];canvas=np.zeros((80,96),np.uint8);canvas[y:y+size[1],x:x+size[0]]=a;save_image(canvas.tobytes(),(96,80),pal,out/f'air_{n:03d}.png')
 r=next(r for r in art['frames'] if r['frame']==n);r.update(source='landing_generated.png',scale=scale,native_size=size,canvas_offset=[x,y],eye_world=[float(np.median(ex)+x-48),float(np.median(ey)+y-40)]);print({k:r[k] for k in ('frame','native_size','eye_world')})
(out/'art.json').write_text(json.dumps(art,indent=2))
