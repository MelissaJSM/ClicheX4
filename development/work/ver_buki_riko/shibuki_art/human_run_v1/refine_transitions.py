from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.project import digest
d=Path(__file__).parent;out=d/'production03';shutil.copytree(d/'production02',out)
art=json.loads((out/'art.json').read_text());words=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
im=Image.open(d/'transitions_generated.png').convert('RGBA');crops=[]
for i in range(3):
 cell=im.crop((round(i*im.width/3),0,round((i+1)*im.width/3),im.height));ys,xs=np.nonzero(np.array(cell)[:,:,3]>=128)
 crops.append(cell.crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))))
scale=47/max(c.height for c in crops)
for n,crop in zip([3,27,29],crops):
 size=(round(crop.width*scale),round(crop.height*scale));a=quantize(crop,size,rgb)
 old=np.array(Image.open(out/f'run_{n:03d}.png'));mask=old==7;mask[40:]=False;ey,ex=np.nonzero(mask);ny,nx=np.nonzero(a==7)
 x=round(float(np.median(ex)-np.median(nx)));y=int(np.nonzero(old)[0].max())+1-size[1];result=np.zeros_like(old);result[y:y+size[1],x:x+size[0]]=a
 save_image(result.tobytes(),(96,80),words,out/f'run_{n:03d}.png')
 for r in art['frames']:
  if r['frame']==n:r.update(native_size=list(size),world_position=[x-48,y-40],opaque_pixels=int(np.count_nonzero(result)),replacement_source='transitions_generated.png',replacement_sha256=digest(d/'transitions_generated.png'))
 print({'frame':n,'size':size,'eye_distance':float(np.median(ny)),'opaque':int(np.count_nonzero(result))})
(out/'art.json').write_text(json.dumps(art,indent=2))
source=(d/'prepare_pairs.py').read_text().replace("body=d/'production02'","body=d/'production03'").replace("out=d/'paired'","out=d/'paired02'")
exec(compile(source,str(d/'prepare_pairs.py'),'exec'))
shutil.copy2(d/'paired/packing.json',d/'paired02/packing.json')
shutil.copy2(d/'joint_layout.json',d/'layout03.json')
