from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent;im=Image.open(D/'generated_floor.png');scale=float(sys.argv[1]) if len(sys.argv)>1 else .036
a,hp=normalize(sample(im,scale),front);h,w=a.shape;safe=original(182)[2];opts=[]
for y in range(-40,0):
 for x in range(-32,1):
  bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]));opts.append((bad*10000+abs(y+h-25)*12+abs(x+hp[0]+21),bad,x,y))
_,bad,x,y=min(opts);save_image(a.tobytes(),(w,h),pal,D/'key_182.png');r={'frame':182,'scale':scale,'head_local':hp,'head_world':[x+hp[0],y+hp[1]],'position':[x,y],'size':[w,h],'outside':bad,'body_pixels':int(np.count_nonzero(a))-int(np.count_nonzero(front)),'foot_world':y+h-1,'components':[len(c) for c in component(a!=0)]};print(json.dumps(r))
k=dict(np.load(D/'key_pixels.npz'));k['182']=a;np.savez(D/'key_pixels.npz',**k);regs=json.loads((D/'key_registration.json').read_text());regs=[v if v['frame']!=182 else r for v in regs];(D/'key_registration.json').write_text(json.dumps(regs,indent=2),'utf8');rgba(a).resize((w*10,h*10),Image.Resampling.NEAREST).save(D/'floor_review.png')
