from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.project import digest
d=Path(__file__).parent;out=d/'production02';shutil.copytree(d/'production',out)
art=json.loads((out/'art.json').read_text());words=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
im=Image.open(d/'passing13_generated.png').convert('RGBA');ys,xs=np.nonzero(np.array(im)[:,:,3]>=128)
crop=im.crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)));size=(round(crop.width*47/crop.height),47);a=quantize(crop,size,rgb)
old=np.array(Image.open(out/'run_013.png'));ey,ex=np.nonzero(old==7);ny,nx=np.nonzero(a==7)
x=round(float(np.median(ex)-np.median(nx)));y=int(np.nonzero(old)[0].min());result=np.zeros_like(old);result[y:y+47,x:x+size[0]]=a
save_image(result.tobytes(),(96,80),words,out/'run_013.png')
for r in art['frames']:
 if r['frame']==13:r.update(native_size=list(size),world_position=[x-48,y-40],opaque_pixels=int(np.count_nonzero(result)),replacement_source='passing13_generated.png',replacement_sha256=digest(d/'passing13_generated.png'))
(out/'art.json').write_text(json.dumps(art,indent=2));print({'size':size,'eye_distance':float(np.median(ny)),'opaque':int(np.count_nonzero(result))})
