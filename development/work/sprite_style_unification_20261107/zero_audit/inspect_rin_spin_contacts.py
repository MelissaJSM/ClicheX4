"""새 회전 원화와 기존 접점의 좌표 격자. 표시용 진단만 작성한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension/ice_spin02';O=D/'contact_review';O.mkdir(exist_ok=True)
pal=json.loads((D/'inputs.json').read_text('utf8'))['palette_words']
crop=(132,140,196,188);scale=15
for n in (144,161,163):
 sheet=Image.new('RGB',(64*scale*2,48*scale+40),'#374650');dr=ImageDraw.Draw(sheet)
 for c,(tag,p) in enumerate((('old',D/f'b1_{n:03}_before_indices.png'),('new',D/'native'/f'b1_{n:03}_indices.png'))):
  a=np.array(Image.open(p));pic=rgba(a,pal).crop(crop).resize((64*scale,48*scale),Image.Resampling.NEAREST);sheet.paste(pic,(c*64*scale,40),pic)
  for x in range(64):
   xx=c*64*scale+x*scale;dr.line((xx,40,xx,760),fill='#505d64')
   if x%4==0:dr.text((xx,24),str(x+132),fill='white')
  for y in range(48):
   yy=40+y*scale;dr.line((c*64*scale,yy,(c+1)*64*scale,yy),fill='#505d64')
   if y%4==0:dr.text((c*64*scale,yy),str(y+140),fill='white')
  dr.text((c*64*scale+4,2),f'{n} {tag}',fill='white')
 sheet.save(O/f'{n}_grid.png')
print(O)
