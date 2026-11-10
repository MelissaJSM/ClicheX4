import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;a=d/'production01';a.mkdir(exist_ok=True)
pal=json.loads((d.parent/'idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
records=[]
def sheet(name,cols,rows,scale,ns,feet):
 src=Image.open(d/(name+'_generated.png')).convert('RGBA')
 # Generated sheet rows are separated at actual gutters, rather than clipping to equal cells.
 cuts=[0,385,719,src.height] if name=='ready' else [0,365,720,src.height] if name=='special' else [0,510,src.height]
 for i,n in enumerate(ns):
  box=(round(i%cols*src.width/cols),cuts[i//cols],round((i%cols+1)*src.width/cols),cuts[i//cols+1]);im=src.crop(box);alpha=np.array(im)[:,:,3];yy,xx=np.nonzero(alpha>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));im=im.crop(bb);size=tuple(round(v*scale) for v in im.size);arr=quantize(im,size,rgb,128);yy,xx=np.nonzero(arr);ey,ex=np.nonzero((arr==7)&(np.indices(arr.shape)[0]<arr.shape[0]*.6));left=round(43-float(np.median(ex))) if len(ex) else round(48-(xx.min()+xx.max())/2);top=feet[i]-int(yy.max())
  if name=='ready' and i in (8,9):left=round(48-(xx.min()+xx.max())/2)
  canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr
  save_image(canvas.tobytes(),(96,80),pal,a/f'frame_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','source':name+'_generated.png','source_cell':box,'source_box':bb,'scale':scale,'size':size,'offset':[left,top]})
sheet('special',4,3,.18,[89,90,91,95,97,98,100,101,102,103,104,231],[62,62,62,62,62,62,64,65,65,64,65,62])
sheet('ready',4,3,.16,[133,135,137,138,204,205,206,207,156,158,233,234],[62,62,62,62,62,62,62,62,62,62,63,63])
sheet('vehicle',3,2,.115,[162,166,170,174,217,94],[56,56,60,66,59,64])
(a/'art.json').write_text(json.dumps({'frames':records,'palette_words':pal,'source_inventory':'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'},indent=2))
review=Image.new('RGB',(6*288,6*264),'#28394b');dr=ImageDraw.Draw(review)
im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);review.paste(im,(0,24),im);dr.text((8,5),'ACCEPTED IDLE',fill='white')
for i,r in enumerate(records,1):
 im=Image.open(a/r['image']).convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=i%6*288;y=i//6*264;review.paste(im,(x,y+24),im);dr.text((x+8,y+5),str(r['frame']),fill='white')
review.save(a/'normalized_review.png');print([(r['frame'],r['size'],r['offset']) for r in records])
