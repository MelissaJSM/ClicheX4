"""의상·손발 의미영역 판독용 좌표판. 원그림을 변경하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'semantic_grids_v1';out.mkdir(exist_ok=False)
 for n in(162,166,170,174):
  cv=Image.new('RGB',(1536,750),'#9aa6ad');d=ImageDraw.Draw(cv);x0,y0,x1,y1=-25,-23,19,18;sc=16;folder='a_registered_v1'if n<170 else'b_registered_v1'
  for col,(form,start)in enumerate((('before',16),('after',0))):
   z=np.array(Image.open(D/f'{folder}/{form}_{n:03}_indices.png'));pic=a.rgba(z,start).crop((x0+160,y0+160,x1+160,y1+160)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.Resampling.NEAREST);cv.paste(pic,(col*768+38,44),pic);d.text((col*768+38,8),f'{n} {form}',fill='black')
   for y in range(y0,y1):
    d.text((col*768+5,44+(y-y0)*sc),str(y),fill='black')
    for x in range(x0,x1):
     val=int(z[y+160,x+160]);sx=col*768+38+(x-x0)*sc;sy=44+(y-y0)*sc
     if y==y0 and x%4==0:d.text((sx,28),str(x),fill='black')
     if val:d.text((sx+3,sy+1),hex(val)[2:].upper(),fill='white'if val<7 else'black')
  cv.save(out/f'grid_{n}.png')
if __name__=='__main__':main()
