from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension/detail_priority_singles';O=D/'body_review';O.mkdir(exist_ok=True)
arc=(D.parent/'prepared_air_continuation2_v2/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9))
items={'idle147':render(arc,0,0,147)[0]}
for b,n in[(0,61),(1,5),(1,183)]:
 key=f'b{b}_{n:03}';items[key+'_old']=render(arc,b,b*5,n)[0];items[key+'_new']=np.array(Image.open(D/'registered_v2'/f'{key}_indices.png'))
crop=(128,128,192,192);scale=12
for k,a in items.items():
 pic=rgba(a,pal).crop(crop).resize((768,768),Image.Resampling.NEAREST);sheet=Image.new('RGB',(816,800),'#626c78');sheet.paste(pic,(48,32),pic);draw=ImageDraw.Draw(sheet)
 for x in range(128,192):
  if x%4==0:draw.text((48+(x-128)*12,12),str(x),fill='white');draw.line((48+(x-128)*12,32,48+(x-128)*12,800),fill='#7c8794')
 for y in range(128,192):
  if y%2==0:draw.text((12,32+(y-128)*12),str(y),fill='white')
 sheet.save(O/f'{k}.png')
(O/'indices.json').write_text(json.dumps({k:{str(y):''.join(format(int(x),'x')for x in a[y,128:192])for y in range(128,192)}for k,a in items.items()},indent=2)+'\n','utf8')
print(O)
