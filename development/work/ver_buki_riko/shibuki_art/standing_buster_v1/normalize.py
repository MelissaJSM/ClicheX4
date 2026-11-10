import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize,ranges
from scripts.extract_zero import save_image
d=Path(__file__).parent
words=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words']
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
im=Image.open(d/'generated.png').convert('RGBA');mask=np.array(im)[:,:,3]>=128
boxes=[]
for l,r in ranges(mask.any(0)):
 yy,xx=np.nonzero(mask[:,l:r]);boxes.append((l,int(yy.min()),r,int(yy.max()+1)))
if len(boxes)!=3:raise ValueError(boxes)
base=np.array(Image.open(d/'parent_000.png'));yy,xx=np.nonzero(base);foot=np.nonzero(base[yy.max()])[0].mean();scale=47/(boxes[0][3]-boxes[0][1])
sheet=Image.new('RGB',(4*384,400),'#222630');draw=ImageDraw.Draw(sheet);reports=[]
for i,bb in enumerate([None]+boxes):
 if bb is None:canvas=base;label='Accepted idle';n=0
 else:
  n=[85,87,92][i-1];crop=im.crop(bb);size=tuple(round(q*scale) for q in crop.size);a=quantize(crop,size,rgb,64)
  ay,ax=np.nonzero(a);af=np.nonzero(a[ay.max()])[0].mean();left=round(foot-af);top=int(yy.min())
  canvas=np.zeros_like(base);canvas[top:top+a.shape[0],left:left+a.shape[1]]=a;label=f'Generated {n}'
  reports.append({'frame':n,'box':bb,'scale':scale,'left':left,'top':top,'size':size})
 pic=save_image(canvas.tobytes(),(96,80),words,d/f'normalized_{n:03d}.png').convert('RGBA').resize((384,320),Image.Resampling.NEAREST)
 sheet.paste(pic,(i*384,30),pic);draw.text((i*384+24,10),label,fill='white')
sheet.save(d/'normalized_review.png');(d/'normalization.json').write_text(json.dumps(reports,indent=2))
print(reports)
