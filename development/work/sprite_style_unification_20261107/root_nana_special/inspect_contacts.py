from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[2];N=D.parent/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
m=json.loads((D/'inputs01/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'contact_inspection01';out.mkdir(exist_ok=False)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11)
for n in(95,98):
 rows=[]
 for form,mask,pal in(('base',0,0),('fourth',15,16)):
  z=np.array(Image.open(D/'registered01'/f'{form}_{n:03}_indices.png'));im=a.rgba(z,pal);box=(132,128,184,186);s=16;sheet=Image.new('RGB',((box[2]-box[0]+2)*s,(box[3]-box[1]+2)*s),(180,190,198));sheet.paste(im.crop(box).resize(((box[2]-box[0])*s,(box[3]-box[1])*s),Image.Resampling.NEAREST),(2*s,2*s),im.crop(box).resize(((box[2]-box[0])*s,(box[3]-box[1])*s),Image.Resampling.NEAREST));dr=ImageDraw.Draw(sheet)
  for x in range(box[0],box[2]):dr.text(((x-box[0]+2)*s,8),str(x-160),font=font,fill='black');dr.line(((x-box[0]+2)*s,2*s,(x-box[0]+2)*s,sheet.height),fill=(140,150,160))
  for y in range(box[1],box[3]):dr.text((0,(y-box[1]+2)*s),str(y-160),font=font,fill='black');dr.line((2*s,(y-box[1]+2)*s,sheet.width,(y-box[1]+2)*s),fill=(140,150,160))
  sheet.save(out/f'{form}_{n:03}_grid.png')
 rows=[(f'old layer {pb} ref{n}',[('layer',a.rgba(a.layer(n,pb)[0],0 if pb==0 else 16))])for pb in(0,5,6,7,8)]
 helper.grid(rows,out/f'old_layers_{n}.png',4)
print('contact grids written')
