"""사격 팔/접힌 손 영역의 색인과 원점을 출력한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive
def main():
 a=Archive((N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC').read_bytes());out=D/'firing_before_grids_v1';out.mkdir(exist_ok=False);f=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10)
 for page in('a','b'):
  for q in json.loads((D/f'firing_{page}_before_registered_v1/registration.json').read_text('utf8'))['frames']:
   n=q['ref'];ex,ey=q['eye_world'];roi=(-45,ey,ex+24,ey+24);w,h=roi[2]-roi[0],24;s=18;c=Image.new('RGB',(w*s*2,h*s+50),'#bdc7cf');dr=ImageDraw.Draw(c)
   for j,p in enumerate((ROOT/q['body_path'],D/f'firing_{page}_before_registered_v1/before_{n:03}.png')):
    v=np.array(Image.open(p));im=a.rgba(v,16).crop(tuple(x+160 for x in roi)).resize((w*s,h*s),Image.Resampling.NEAREST);c.paste(im,(j*w*s,50),im);dr.text((j*w*s+3,3),f'{n} '+('new fixed body'if j==0 else'new firing source'),fill='black')
    for y in range(h):
     for x in range(w):
      z=int(v[roi[1]+y+160,roi[0]+x+160]);px=j*w*s+x*s;py=50+y*s;dr.rectangle((px,py,px+s-1,py+s-1),outline='#89969c')
      if z:dr.text((px+3,py+1),str(z),font=f,fill='white'if z in(1,2,3,5,6,7)else'black')
    for x in range(0,w,3):dr.text((j*w*s+x*s,29),str(roi[0]+x),font=f,fill='black')
    for y in range(0,h,2):dr.text((j*w*s+2,50+y*s),str(roi[1]+y),font=f,fill='#b01818')
   c.save(out/f'{n:03}.png')
 print(out)
if __name__=='__main__':main()
