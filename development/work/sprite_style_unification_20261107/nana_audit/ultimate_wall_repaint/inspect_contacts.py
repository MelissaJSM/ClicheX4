"""기존/새 벽손과 발의 실제 색인 좌표를 정합 전에 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3];N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,write,digest,need
from check_first_geometry import full
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/'contact_grids_v1';out.mkdir(exist_ok=False);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10);reports=[]
 for n in(55,57,59,61,63,65):
  source=D/('before_a_registered_v1'if n<61 else'before_b_registered_v1')/f'before_{n:03}.png';ims=[full(a,n),np.array(Image.open(source))]
  for name,roi,scale in [('hand',(6,-27,23,-5),22),('feet',(-15,0,26,24),17)]:
   w,h=roi[2]-roi[0],roi[3]-roi[1];canvas=Image.new('RGB',(w*scale*2,h*scale+50),'#bec9d0');dr=ImageDraw.Draw(canvas)
   for j,idx in enumerate(ims):
    im=a.rgba(idx,16).crop(tuple(q+160 for q in roi)).resize((w*scale,h*scale),Image.Resampling.NEAREST);canvas.paste(im,(j*w*scale,50),im);dr.text((j*w*scale+5,3),f'{n} {name} '+('old'if j==0 else'new'),fill='black')
    for y in range(h):
     for x in range(w):
      value=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*scale+x*scale;py=50+y*scale;dr.rectangle((px,py,px+scale-1,py+scale-1),outline='#81929b')
      if value:dr.text((px+2,py+2),str(value),font=font,fill='white'if value in(1,2,3,5,6,7)else'black')
    for x in range(0,w,2):dr.text((j*w*scale+x*scale,28),str(roi[0]+x),font=font,fill='black')
    for y in range(0,h,2):dr.text((j*w*scale+1,50+y*scale),str(roi[1]+y),font=font,fill='#bb2018')
   canvas.save(out/f'{n:03}_{name}.png')
  reports.append({'ref':n,'candidate_source':source.relative_to(ROOT).as_posix(),'candidate_sha256':digest(source)})
 write(out/'manifest.json',{'frames':reports,'only_index_visualization':True,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
