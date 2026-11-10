"""새 후폼 의상 의미영역을 정하기 위한 좌표/색인 비교만 출력."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive
from prepare_inputs import SRC
from collect_before_bodies import SOURCES
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',default='a');args=p.parse_args();page=args.page;assert page in('a','b','c');a=Archive(SRC.read_bytes());out=D/f'after_{page}_grids_v1';out.mkdir(exist_ok=False);f=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10);meta=json.loads((D/f'after_inputs_v1/{page}_poses.json').read_text('utf8'))
 for q in meta:
  n=q['ref'];ex,ey=map(int,q['eye_world']);roi=(ex-3,ey,ex+29,ey+25);s=22;w,h=32,25;c=Image.new('RGB',(w*s*2,h*s+50),'#bdc7cf');dr=ImageDraw.Draw(c)
  for j,p in enumerate((D/SOURCES[n]/f'before_{n:03}.png',D/f'after_{page}_registered_v2'/f'after_{n:03}.png')):
   idx=np.array(Image.open(p));im=a.rgba(idx,16 if j==0 else 0).crop(tuple(v+160 for v in roi)).resize((w*s,h*s),Image.Resampling.NEAREST);c.paste(im,(j*w*s,50),im);dr.text((j*w*s+3,3),f'{n} '+('new before'if j==0 else'after donor'),fill='black')
   for y in range(h):
    for x in range(w):
     v=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*s+x*s;py=50+y*s;dr.rectangle((px,py,px+s-1,py+s-1),outline='#89969c')
     if v:dr.text((px+3,py+2),str(v),font=f,fill='white'if v in(1,2,3,5,6,7)else'black')
   for x in range(0,w,2):dr.text((j*w*s+x*s,29),str(roi[0]+x),font=f,fill='black')
   for y in range(0,h,2):dr.text((j*w*s+2,50+y*s),str(roi[1]+y),font=f,fill='#b01818')
  c.save(out/f'{n:03}.png')
 print(out)
if __name__=='__main__':main()
