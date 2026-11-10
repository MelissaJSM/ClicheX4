from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'ground_contact_probe';O.mkdir(exist_ok=True)
arc=(D/'prepared_hurt_lowhp_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));rows=[]
box=(128,128,196,188);scale=12;pad=32;w=(box[2]-box[0])*scale+pad;h=(box[3]-box[1])*scale+pad
for n in(62,63,65,67):
 old=render(arc,0,0,n)[0];new=np.array(Image.open(D/'ground_first01/native'/f'b0_{n:03}_indices.png'));im=Image.new('RGB',(w*2,h),(28,34,44));dr=ImageDraw.Draw(im);rec={'ref':n}
 for k,(label,z)in enumerate([('old',old),('new',new)]):
  rgb=rgba(z,pal).crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);im.paste(rgb,(k*w+pad,pad),rgb);dr.text((k*w+pad,3),f'{n} {label}',fill='white')
  for x in range(box[0],box[2]+1):
   if x%5==0:
    px=k*w+pad+(x-box[0])*scale;dr.line((px,pad,px,h),fill=(64,64,72));dr.text((px-7,15),str(x),fill='white')
  for y in range(box[1],box[3]+1):
   if y%5==0:
    py=pad+(y-box[1])*scale;dr.line((k*w+pad,py,(k+1)*w,py),fill=(64,64,72));dr.text((k*w,py),str(y),fill='white')
  yy,xx=np.nonzero(z==15);skin_y,skin_x=np.nonzero(np.isin(z,[12,13,14])&(np.indices(z.shape)[0]<160))
  rec[label]={'cyan':[list(map(int,p))for p in zip(xx,yy)],'upper_skin_xy':[list(map(int,p))for p in zip(skin_x,skin_y)],'bottom':int(np.nonzero(z)[0].max())}
 im.save(O/f'{n}.png');rows.append(rec)
(O/'pixel_coordinates.json').write_text(json.dumps(rows,indent=2)+'\n','utf8');print(str(O))
