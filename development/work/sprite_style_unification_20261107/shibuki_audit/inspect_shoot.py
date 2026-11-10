from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE
a=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'])
out=H/'shot_diagnosis';out.mkdir(exist_ok=True)
items=[]
for n in (3,7,11,15,19,23,27,31):
 b=Image.open(H/'run_registered02/before'/f'{n:03}.png')
 items += [(f'{n} new run',b),(f'{n+1} current shot',a.composite(n+1,15)[0])]
for k in range(0,len(items),8):page(items[k:k+8],a.composite(0,15)[0],out/f'comparison_{k//8:02}.png',cols=2,scale=5)
b=np.array(Image.open(ROOT/'work/sprite_style_unification_20261107/shibuki/ultimate_run_detail05/native/085_indices.png'))
im=a.rgba(b,16).crop((128,140,171,175)).resize((688,560),Image.Resampling.NEAREST)
bg=Image.new('RGBA',im.size,(35,43,55,255));bg.alpha_composite(im);d=ImageDraw.Draw(bg)
for x in range(43):d.text((x*16,0),str((x+128)%10),fill='red')
for y in range(35):d.text((0,y*16),str(y+140),fill='red')
bg.save(out/'new85_grid.png')
report=[]
for n in (4,8,12,16,20,24,28,32):
 p=np.array(a.composite(n,15)[0]);ys,xs=np.nonzero(p[:,:,3]);report.append({'ref':n,'min_x':int(xs.min()),'left_rows':{str(y):''.join('X'if c else'.'for c in p[y,128:161,3])for y in range(143,164)}})
(out/'rows.json').write_text(json.dumps(report,indent=2),'utf8')
