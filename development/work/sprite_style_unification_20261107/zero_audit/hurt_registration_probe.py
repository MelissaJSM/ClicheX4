from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';S=D/'hurt_lowhp01';O=D/'hurt_registration_probe';O.mkdir(exist_ok=True)
a=(D/'prepared_movement_finish_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(a,9))
for n in (135,139,149,152):
 old=render(a,0,0,n)[0];new=np.array(Image.open(S/'native'/f'b0_{n:03}_indices.png'))
 box=(120,125,195,188);scale=12;pad=30;w=(box[2]-box[0])*scale+pad;h=(box[3]-box[1])*scale+pad
 im=Image.new('RGB',(w*2,h),(27,34,44));dr=ImageDraw.Draw(im)
 for k,(label,z)in enumerate([('before',old),('new',new)]):
  rgb=rgba(z,pal).crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);im.paste(rgb,(k*w+pad,pad),rgb)
  dr.text((k*w+pad,3),f'{n} {label}',fill='white')
  for x in range(box[0],box[2]+1):
   if x%5==0:
    px=k*w+pad+(x-box[0])*scale;dr.line((px,pad,px,h),fill=(65,65,70));dr.text((px-6,14),str(x),fill='white')
  for y in range(box[1],box[3]+1):
   if y%5==0:
    py=pad+(y-box[1])*scale;dr.line((k*w+pad,py,(k+1)*w,py),fill=(65,65,70));dr.text((k*w,py),str(y),fill='white')
 im.save(O/f'{n}_grid.png')
print(str(O))
