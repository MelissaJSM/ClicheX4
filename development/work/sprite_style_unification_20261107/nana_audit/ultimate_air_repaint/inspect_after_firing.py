from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive
from register_firing_arms_v3 import getpage
a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'firing_after_grids_v1';out.mkdir(exist_ok=False);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11)
roi=(-30,-18,10,13);w,h=40,31;s=19
for n in range(34,55,2):
 idx=np.array(Image.open(D/f'firing_{getpage(n)}_after_registered_v1'/f'after_{n:03}.png'));canvas=Image.new('RGB',(w*s+40,h*s+44),'#b8c4cf');dr=ImageDraw.Draw(canvas);im=a.rgba(idx,0).crop(tuple(q+160 for q in roi)).resize((w*s,h*s),Image.Resampling.NEAREST);canvas.paste(im,(36,44),im);dr.text((4,4),f'new after source {n}',fill='black')
 for y in range(h):
  dr.text((4,y*s+44),str(y+roi[1]),font=font,fill='black')
  for x in range(w):
   px=x*s+36;py=y*s+44;v=int(idx[y+roi[1]+160,x+roi[0]+160]);dr.rectangle((px,py,px+s-1,py+s-1),outline='#809099')
   if v:dr.text((px+2,py+2),hex(v)[2:].upper(),font=font,fill='white'if v in(1,2,3,5,6,7)else'black')
 for x in range(w):dr.text((x*s+37,23),str(x+roi[0]),font=font,fill='black')
 canvas.save(out/f'{n:03}.png')
