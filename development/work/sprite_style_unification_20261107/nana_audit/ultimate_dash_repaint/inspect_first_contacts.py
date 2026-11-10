"""대시 첫4의 색인 좌표 격자. 새 그림을 변경하지 않는 비교용."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
from prepare_inputs import SRC,EXPECTED,merged
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'contact_grids_v1';out.mkdir(exist_ok=False);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10)
 records=[]
 for n in(67,71,79,93):
  source=D/f'before_first_registered_v2/before_{n:03}.png';ims=[merged(a,n,15),np.array(Image.open(source))];roi=(-17,1,24,24)if n!=71 else(-17,10,17,24);w,h=roi[2]-roi[0],roi[3]-roi[1];scale=18
  cv=Image.new('RGB',(w*scale*2,h*scale+50),'#bec9d0');dr=ImageDraw.Draw(cv)
  for j,idx in enumerate(ims):
   im=a.rgba(idx,16).crop(tuple(q+160 for q in roi)).resize((w*scale,h*scale),Image.Resampling.NEAREST);cv.paste(im,(j*w*scale,50),im);dr.text((j*w*scale+4,3),f'{n} feet '+('old'if j==0 else'new'),fill='black')
   for y in range(h):
    for x in range(w):
     value=int(idx[roi[1]+y+160,roi[0]+x+160]);px=j*w*scale+x*scale;py=50+y*scale;dr.rectangle((px,py,px+scale-1,py+scale-1),outline='#81929b')
     if value:dr.text((px+2,py+2),str(value),font=font,fill='white'if value in(1,2,3,5,6,7)else'black')
   for x in range(0,w,2):dr.text((j*w*scale+x*scale,28),str(roi[0]+x),font=font,fill='black')
   for y in range(0,h,2):dr.text((j*w*scale+1,50+y*scale),str(roi[1]+y),font=font,fill='#bb2018')
  cv.save(out/f'{n:03}_feet.png');records.append({'ref':n,'source':str(source.relative_to(ROOT)),'source_sha256':digest(source),'roi_world':roi})
 write(out/'manifest.json',{'only_index_visualization':True,'frames':records,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
