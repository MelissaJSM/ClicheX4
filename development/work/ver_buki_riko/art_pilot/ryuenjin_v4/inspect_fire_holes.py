from pathlib import Path
import sys,struct,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,zpal,pal
D=Path(__file__).parent;R=ROOT/'work/ver_buki_riko/rise_runtime/20261025T121843451304Z';V=ROOT/'work/ver_buki_riko/rise_alignment/20261025T120817448635Z/vram_04.bin'
epal=struct.unpack_from('<16H',V.read_bytes(),480*2048+32)
board=Image.new('RGBA',(4*400,3*360),(32,36,48));dr=ImageDraw.Draw(board)
for i,n in enumerate((148,150,154,156)):
 a,b,_=original(n);e,eb,_=original(n+1)
 for j in range(2):
  body=a if j==0 else np.array(Image.open(D/f'bank1_{n:03d}.png'));im=Image.new('RGBA',(100,86));im.alpha_composite(rgba(body,zpal if j==0 else pal),(65+b[0],65+b[1]));im.alpha_composite(rgba(e,epal),(65+eb[0],65+eb[1]));board.alpha_composite(im.resize((400,344),Image.Resampling.NEAREST),(i*400,j*360+16));dr.text((i*400+3,j*360+2),str(n)+(' ZERO + SAME FIRE STATIC' if j==0 else ' RIKO + SAME FIRE STATIC'),fill='white')
 im=Image.open(R/f'diagnostic_{n:03d}_0.png').convert('RGBA');board.alpha_composite(im.crop((110,30,210,116)).resize((400,344),Image.Resampling.NEAREST),(i*400,736));dr.text((i*400+3,722),str(n)+' ACTUAL CAPTURE (sampling may differ)',fill='white')
board.save(D/'fire_hole_comparison.png')
print(json.dumps({'effect_palette_from':str(V),'clut':'0x7801','effect_images_modified':False}))
