"""新しい前後衣装の色インデックスを目視照合するだけのシート。"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/'costume_grids_v1';out.mkdir(exist_ok=False);f=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10);roi=(-9,-24,22,8);s=20;w=roi[2]-roi[0];h=roi[3]-roi[1]
 for n in range(55,66,2):
  bp=D/'canonical_cases_probe_v2'/f'before_{n:03}.png';ap=D/('after_a_registered_v1'if n<61 else'after_b_registered_v1')/f'after_{n:03}.png';c=Image.new('RGB',(w*s*2,h*s+50),'#bdc7cf');dr=ImageDraw.Draw(c)
  for j,p in enumerate((bp,ap)):
   idx=np.array(Image.open(p));im=a.rgba(idx,16 if j==0 else 0).crop(tuple(q+160 for q in roi)).resize((w*s,h*s),Image.Resampling.NEAREST);c.paste(im,(j*w*s,50),im);dr.text((j*w*s+3,3),f'{n} '+('before body'if j==0 else'after new source'),fill='black')
   for y in range(h):
    for x in range(w):
     v=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*s+x*s;py=50+y*s;dr.rectangle((px,py,px+s-1,py+s-1),outline='#89969c')
     if v:dr.text((px+2,py+2),str(v),font=f,fill='white'if v in(1,2,3,5,6,7)else'black')
   for x in range(0,w,2):dr.text((j*w*s+x*s,29),str(roi[0]+x),font=f,fill='black')
   for y in range(0,h,2):dr.text((j*w*s+2,50+y*s),str(roi[1]+y),font=f,fill='#b01818')
  c.save(out/f'{n:03}.png')
 print(out)
if __name__=='__main__':main()
