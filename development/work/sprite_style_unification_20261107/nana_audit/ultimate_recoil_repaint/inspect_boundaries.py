"""원화 양폼의 새 의미영역 좌표를 읽기 격자로 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'semantic_grids_v1';out.mkdir(exist_ok=False);box=(-23,-18,12,11);step=23
 for n in(90,91):
  w=(box[2]-box[0])*step+42;h=(box[3]-box[1])*step+50;sheet=Image.new('RGB',(w*2,h),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for col,(form,start)in enumerate((('before',16),('after',0))):
   z=np.array(Image.open(D/f'first_registered_v1/{form}_{n:03}_indices.png'));im=a.rgba(z,start);dr.text((col*w+5,3),f'{n} {form}',fill='black')
   for x in range(box[0],box[2]):dr.text((col*w+36+(x-box[0])*step,23),str(x),fill='black')
   for y in range(box[1],box[3]):
    dr.text((col*w+2,43+(y-box[1])*step),str(y),fill='black')
    for x in range(box[0],box[2]):
     px=col*w+36+(x-box[0])*step;py=43+(y-box[1])*step;c=im.getpixel((x+160,y+160));dr.rectangle((px,py,px+step,py+step),fill=c[:3]if c[3]else'#b6c0c7',outline='#8a969d')
  sheet.save(out/f'grid_{n:03}.png')
 print(out)
if __name__=='__main__':main()
