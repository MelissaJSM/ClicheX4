import json
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
from native import decode,world
D=Path(__file__).parent
rs=json.loads((D/'records.json').read_text())
r=next(r for r in rs if r['kind']=='select')
items=[('selection x55 y33',Image.open(D/'frames'/(r['id']+'.png')).crop((55,33,110,70))),('get x70 y25',Image.open(D/'background_st0f_0x_eng.arc.png').crop((70,25,125,65)))]
out=Image.new('RGB',(880,820),'#252d40');d=ImageDraw.Draw(out)
for i,(label,im)in enumerate(items):
    im=im.resize((im.width*10,im.height*10),Image.Resampling.NEAREST);out.paste(im,(0,i*410),im);d.text((560,i*410),label,fill='white')
out.save(D/'select_get_faces.png')
p,_=decode(r)
print('selection',[(int(x),int(y),int(p[y,x]))for y,x in np.argwhere(np.isin(p,[9,10,11,14])) if 70<=x<=95 and 44<=y<=60])
for t in ['cliche_br_st0d_0x.arc','cliche_br_hqx_15.arc','cliche_br_hqx_16.arc','cliche_br_hqx_17.arc']:
    p=world(next(r for r in rs if r['kind']=='hq' and r['target']==t and r['frame']==9))
    print(t,[(int(x),int(y),int(p[y,x]))for y,x in np.argwhere(np.isin(p,[9,10,11,14]))if 63<=x<84 and 48<=y<=60])
