from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,zpal,pal
from work.ver_buki_riko.art_pilot.sword_v1.inspect_sword import epal
D=Path(__file__).parent;P=D.parent/'ryuenjin_v2'
sheet=Image.new('RGBA',(8*224,3*264),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,n in enumerate((144,146,148,150,152,154,156,158)):
 a,b,_=original(n);e,eb,_=original(n+1)
 for j in range(3):
  cell=Image.new('RGBA',(112,124));body=a if j==0 else np.array(Image.open(P/f'bank1_{n:03d}.png'))
  cell.alpha_composite(rgba(body,zpal if j==0 else pal),(56+b[0],72+b[1]))
  if j!=1:cell.alpha_composite(rgba(e,epal),(56+eb[0],72+eb[1]))
  cd=ImageDraw.Draw(cell);cd.line((51,72,61,72),fill='red');cd.line((56,67,56,77),fill='red')
  sheet.alpha_composite(cell.resize((224,248),Image.Resampling.NEAREST),(i*224,j*264+16))
  dr.text((i*224+2,j*264+2),str(n)+' '+('ZERO+FX','RIKO','RIKO+FX')[j],fill='white')
sheet.save(D/'alignment_before.png')

