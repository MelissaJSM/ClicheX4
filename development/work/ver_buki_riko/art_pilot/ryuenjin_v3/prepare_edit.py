from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal,zpal
from work.ver_buki_riko.art_pilot.sword_v1.inspect_sword import epal
D=Path(__file__).parent;P=D.parent/'ryuenjin_v2'
for n in (144,146,148,156,158):
 a,b,_=original(n);r=np.array(Image.open(P/f'bank1_{n:03d}.png'));e,eb,_=original(n+1)
 sheet=Image.new('RGBA',(1440,640),(32,36,48));dr=ImageDraw.Draw(sheet)
 for i,(im,colors) in enumerate(((a,zpal),(r,pal),(e,epal))):
  pos=b if i<2 else eb;cell=Image.new('RGBA',(80,100));cell.alpha_composite(rgba(im,colors),(40+pos[0],60+pos[1]));sheet.alpha_composite(cell.resize((480,600),Image.Resampling.NEAREST),(i*480,20))
  for x in range(-35,36,5):dr.line(((40+x)*6+i*480,20,(40+x)*6+i*480,620),fill=(70,70,70));dr.text(((40+x)*6+i*480,2),str(x),fill='white')
  for y in range(-55,36,5):dr.line((i*480,20+(60+y)*6,(i+1)*480,20+(60+y)*6),fill=(70,70,70));dr.text((i*480,20+(60+y)*6),str(y),fill='yellow')
 sheet.save(D/f'grid_{n}.png')
 if n in (148,156):
  cell=Image.new('RGBA',(64,80));cell.alpha_composite(rgba(r),(32+b[0],44+b[1]));cell.resize((768,960),Image.Resampling.NEAREST).save(D/f'edit_{n}.png')
