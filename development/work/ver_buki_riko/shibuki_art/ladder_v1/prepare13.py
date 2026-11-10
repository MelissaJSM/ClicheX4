import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent;a=d/'production13';shutil.copytree(d/'production04',a);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32);src=Image.open(d/'tail_generated.png').convert('RGBA');c=src.crop((0,830,src.width//3,src.height));yy,xx=np.nonzero(np.array(c)[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));c=c.crop(bb);size=tuple(round(v*.14) for v in c.size);arr=quantize(c,size,rgb,128);yy,xx=np.nonzero(arr);left=32;top=64-int(yy.max());canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr;save_image(canvas.tobytes(),(96,80),pal,a/'frame_154.png');r=next(r for r in art['frames'] if r['frame']==154);r.update(source='tail_generated.png',source_box=bb,size=size,canvas_offset=[left,top],registration_shift=[0,0]);(a/'art.json').write_text(json.dumps(art,indent=2));layout=json.loads((a/'layout.json').read_text());q=next(r for r in layout if r['frame']==154);q.update(cover(canvas!=0,6,12));(a/'layout.json').write_text(json.dumps(layout,indent=2));packing=json.loads((a/'packing.json').read_text());packing=[r for r in packing if r['frame']!=154];(a/'packing.json').write_text(json.dumps(packing,indent=2));print({'size':size,'opaque':int(np.count_nonzero(arr)),'layout':q})
s=(d/'optimize04.py').read_text().replace('production04','production13');(d/'optimize13.py').write_text(s)
