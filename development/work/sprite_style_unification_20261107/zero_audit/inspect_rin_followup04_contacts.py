"""현재 원화와 원검기의 고정 원점 접점 참고. 게임 객체 합성 재현 아님."""
from pathlib import Path
import sys,struct,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'saber_followup04';arc=(D/'prepared_saber_followup03/PL01_U.ARC').read_bytes()
words=struct.unpack_from('<64H',entry(arc,9));crop=(124,120,200,192);scale=5;w,h=380,360
sheet=Image.new('RGB',(w*4,(h+25)*4),'#64717b');dr=ImageDraw.Draw(sheet)
for row,n in enumerate((236,238,240,242)):
 old=render(arc,0,0,n)[0];new=np.array(Image.open(A/'native'/f'b0_{n:03}_indices.png'));effect=render(arc,0,0,n+1)[0]
 for col,(arr,label)in enumerate(((old,'old'),(np.where(effect,effect,old),'old + effect'),(new,'new'),(np.where(effect,effect,new),'new + effect'))):
  im=rgba(arr,words).crop(crop).resize((w,h),Image.Resampling.NEAREST);sheet.paste(im,(col*w,row*(h+25)+25),im);dr.text((col*w+5,row*(h+25)+5),f'{n} {label}',fill='white')
sheet.save(A/'contacts_initial.png');print(A/'contacts_initial.png')
