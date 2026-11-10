"""기존/신규 접점의 색인 좌표를 확대해 등록 마스크를 고른다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,write,helper
from check_first_geometry import full
from audit_current_bodies import source
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'contact_grids_v1';out.mkdir(exist_ok=False);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11)
 for n in(33,35,37,39,41,43,47,51):
  ims=[full(a,n),np.array(Image.open(source(n)))];roi=(-14,0,22,25);w,h=roi[2]-roi[0],roi[3]-roi[1];canvas=Image.new('RGB',(w*20*2,h*20+30),'#bec9d0');dr=ImageDraw.Draw(canvas)
  for j,idx in enumerate(ims):
   im=a.rgba(idx,16).crop(tuple(q+160 for q in roi)).resize((w*20,h*20),Image.Resampling.NEAREST);canvas.paste(im,(j*w*20,30),im)
   dr.text((j*w*20+4,3),f'{n} '+('old'if j==0 else'new'),fill='black')
   for y in range(h):
    for x in range(w):
     value=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*20+x*20;py=30+y*20
     dr.rectangle((px,py,px+19,py+19),outline='#809099')
     if value:dr.text((px+2,py+2),str(value),font=font,fill='white'if value in(1,2,3,5,6,7)else'black')
   for x in range(0,w,2):dr.text((j*w*20+x*20,15),str(roi[0]+x),font=font,fill='black')
  canvas.save(out/f'{n:03}.png')
 print(str(out))
if __name__=='__main__':main()
