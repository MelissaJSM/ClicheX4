from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent;im=Image.open(D/'generated_keys.png');scale=float(sys.argv[1]) if len(sys.argv)>1 else .10
poses={};records=[];board=Image.new('RGBA',(4*360,430),(32,36,48));dr=ImageDraw.Draw(board)
for i,n in enumerate((177,179,181,182)):
 cell=im.crop((i%2*768,i//2*512,(i%2+1)*768,(i//2+1)*512));a,hp=normalize(sample(cell,scale),front)
 groups=component(a!=0)
 for c in groups[1:]:
  if len(c)>3:raise ValueError(('Detached',n,[len(c) for c in groups]))
  for y,x in c:a[y,x]=0
 h,w=a.shape;safe=original(n)[2];opts=[]
 for y in range(-40,0):
  for x in range(-32,1):
   bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]));opts.append((bad*10000+abs(y+h-24)*12+abs(x+hp[0]+15),bad,x,y))
 _,bad,x,y=min(opts);poses[str(n)]=a;save_image(a.tobytes(),(w,h),pal,D/f'key_{n:03d}.png');records.append({'frame':n,'scale':scale,'head_local':hp,'head_world':[x+hp[0],y+hp[1]],'position':[x,y],'size':[w,h],'outside':bad,'body_pixels':int(np.count_nonzero(a))-int(np.count_nonzero(front)),'foot_world':y+h-1})
 board.alpha_composite(rgba(a).resize((w*6,h*6),Image.Resampling.NEAREST),(i*360,35));dr.text((i*360+4,4),str(n)+' area='+str(records[-1]['body_pixels'])+' bad='+str(bad),fill='white')
np.savez(D/'key_pixels.npz',**poses);(D/'key_registration.json').write_text(json.dumps(records,indent=2),'utf8');board.save(D/'key_review.png');print(json.dumps(records))
