from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'semantic_grids_v1';out.mkdir(exist_ok=False)
 for n in(95,98):
  srcs=[('first',D/f'first_registered_v1/before_{n:03}_indices.png'),('local',D/f'geometry_registered_v1/before_{n:03}_indices.png')];cv=Image.new('RGB',(1536,1050),'#9aa6ad');d=ImageDraw.Draw(cv)
  for col,(tag,p)in enumerate(srcs):
   z=np.array(Image.open(p));dx,dy=(0,-4)if n==95 else(1,0)
   if tag=='local':z=np.roll(np.roll(z,dy,0),dx,1)
   x0,y0,x1,y1=(-30,-36,28,26);sc=12;pic=a.rgba(z,16).crop((x0+160,y0+160,x1+160,y1+160)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.Resampling.NEAREST);cv.paste(pic,(col*768+38,44),pic);d.text((col*768+38,8),f'{n} {tag} / local delta {dx},{dy}',fill='black')
   for y in range(y0,y1):
    d.text((col*768+5,44+(y-y0)*sc),str(y),fill='black')
    for x in range(x0,x1):
     val=int(z[y+160,x+160]);sx=col*768+38+(x-x0)*sc;sy=44+(y-y0)*sc
     if y==y0 and x%4==0:d.text((sx,28),str(x),fill='black')
     if val:d.text((sx+2,sy),hex(val)[2:].upper(),fill='white'if val<7 else'black')
  cv.save(out/f'grid_{n}.png')
if __name__=='__main__':main()
