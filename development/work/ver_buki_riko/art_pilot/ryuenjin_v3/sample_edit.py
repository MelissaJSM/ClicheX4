from pathlib import Path
import sys,shutil,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import rgba,pal
from scripts.extract_zero import save_image
import numpy as np
D=Path(__file__).parent
src=Path('<LOCAL_PATH>')
shutil.copyfile(src,D/'generated_arms.png');im=Image.open(src);print(im.size)
for i,n in enumerate((148,156)):
 a=sample(im.crop((i*im.width//2,0,(i+1)*im.width//2,im.height)),.077);save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,D/f'sampled_{n}.png')
 board=Image.new('RGBA',(a.shape[1]*12+30,a.shape[0]*12+30),(32,36,48));board.alpha_composite(rgba(a).resize((a.shape[1]*12,a.shape[0]*12),Image.Resampling.NEAREST),(30,30));dr=ImageDraw.Draw(board)
 for x in range(0,a.shape[1],2):dr.line((30+x*12,30,30+x*12,board.height),fill=(90,90,90));dr.text((30+x*12,3),str(x),fill='white')
 for y in range(0,a.shape[0],2):dr.line((30,30+y*12,board.width,30+y*12),fill=(90,90,90));dr.text((3,30+y*12),str(y),fill='white')
 board.save(D/f'sampled_grid_{n}.png')
