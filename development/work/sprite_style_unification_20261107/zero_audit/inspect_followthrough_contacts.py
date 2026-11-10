"""고정 셀 새 원화의 접점을 이전 표시와 좌표 격자로 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension/followthrough01';O=D/'contact_review';O.mkdir(exist_ok=True);info=json.loads((D/'inputs.json').read_text('utf8'));reg=json.loads((D/'native/registration.json').read_text('utf8'));pal=info['palette_words']
crop=(128,120,208,192);scale=12;w,h=80*scale,72*scale
for r in reg['records']:
 k=r['key'];old=np.array(Image.open(D/(k+'_before_indices.png')));a=np.array(Image.open(D/'native'/(k+'_indices.png')));a=np.roll(a,-r['translate'][1],0)
 sheet=Image.new('RGB',(w*2,h+40),'#374650');dr=ImageDraw.Draw(sheet)
 for c,(tag,z)in enumerate([('old',old),('new fixed cell',a)]):
  pic=rgba(z,pal).crop(crop).resize((w,h),Image.Resampling.NEAREST);sheet.paste(pic,(c*w,40),pic)
  for x in range(80):
   xx=c*w+x*scale;dr.line((xx,40,xx,h+40),fill='#505d64')
   if x%4==0:dr.text((xx,24),str(x+128),fill='white')
  for y in range(72):
   yy=40+y*scale;dr.line((c*w,yy,(c+1)*w,yy),fill='#505d64')
   if y%4==0:dr.text((c*w,yy),str(y+120),fill='white')
  dr.text((c*w+4,2),f'{k} {tag}',fill='white')
 sheet.save(O/(k+'_fixed_grid.png'))
print(O)
