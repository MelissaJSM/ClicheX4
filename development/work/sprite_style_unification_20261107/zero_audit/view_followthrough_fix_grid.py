"""국소생성 하체 원화와 새 상체 접합 좌표를 표시한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension/followthrough_contacts_fix01';O=D/'contact_grid';O.mkdir(exist_ok=True);pal=json.loads((D/'inputs.json').read_text('utf8'))['palette_words'];crop=(128,144,208,192);sc=12;w,h=960,576
for key in ['b1_146','b1_156','b1_158','b0_197']:
 sheet=Image.new('RGB',(w*2,h+40),'#374650');dr=ImageDraw.Draw(sheet)
 for c,(label,p)in enumerate([('first source',D/(key+'_source_indices.png')),('new legs',D/'native_fixed'/(key+'_indices.png'))]):
  a=np.array(Image.open(p));pic=rgba(a,pal).crop(crop).resize((w,h),Image.Resampling.NEAREST);sheet.paste(pic,(c*w,40),pic)
  for x in range(80):
   xx=c*w+x*sc;dr.line((xx,40,xx,h+40),fill='#505d64')
   if x%4==0:dr.text((xx,24),str(x+128),fill='white')
  for y in range(48):
   yy=40+y*sc;dr.line((c*w,yy,(c+1)*w,yy),fill='#505d64')
   if y%4==0:dr.text((c*w,yy),str(y+144),fill='white')
  dr.text((c*w+4,2),key+' '+label,fill='white')
 sheet.save(O/(key+'.png'))
print(O)
