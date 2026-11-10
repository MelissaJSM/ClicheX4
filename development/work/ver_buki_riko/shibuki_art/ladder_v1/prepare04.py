import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.solve_sprite_cover import cover
from scripts.solve_paired_cover import paired_cover
d=Path(__file__).parent;a=d/'production04'
if not a.exists():shutil.copytree(d/'production03',a)
art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
im=Image.open(d/'tucked_generated.png').convert('RGBA');c=im.crop((im.width*2//3,450,im.width,830));yy,xx=np.nonzero(np.array(c)[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));c=c.crop(bb);size=tuple(round(v*.14) for v in c.size);arr=quantize(c,size,rgb,128);arr[arr==7]=4;yy,xx=np.nonzero(arr);left=round(48-(xx.min()+xx.max())/2);top=50-int(yy.max());canvas=np.zeros((80,96),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr;save_image(canvas.tobytes(),(96,80),pal,a/'frame_153.png');r=next(r for r in art['frames'] if r['frame']==153);r.update(source='tucked_generated.png',source_box=bb,size=size,canvas_offset=[left,top],registration_shift=[0,0]);(a/'art.json').write_text(json.dumps(art,indent=2))
plan=json.loads((d/'plan.json').read_text());records=[]
for n in (143,144,146,149,151,153,154,155,183):
 q=next(r for r in plan['groups'] if r['frame']==n);arr=np.array(Image.open(a/f'frame_{n:03d}.png'))
 if n==149:
  shot=np.array(Image.open(a/'frame_150.png'))
  for counts in ([6,1,3],[5,2,3],[6,2,2],[5,3,2],[4,3,3]):
   r=paired_cover(arr,shot,counts,12)
   if r['fits']:break
 else:r=cover(arr!=0,min(q['part_count'],len(q['writable'])-(n in (144,146,151))),12)
 r.update(frame=n);records.append(r);print(r,flush=True)
 (a/'layout.json').write_text(json.dumps(records,indent=2))
