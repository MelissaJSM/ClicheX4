from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent
im=Image.open(D/'generated_keys.png').convert('RGBA');arr=np.array(im);groups=component(arr[:,:,3]>=220)[:2];groups.sort(key=lambda g:min(x for y,x in g))
records=[];poses={};review=Image.new('RGBA',(800,360),(32,36,48));dr=ImageDraw.Draw(review)
for i,(n,group) in enumerate(zip((134,140),groups)):
 mask=np.zeros(arr.shape[:2],bool)
 for y,x in group:mask[y,x]=True
 cell=arr.copy();cell[~mask,3]=0
 a,hp=normalize(sample(Image.fromarray(cell),.063),front)
 for c in component(a!=0)[1:]:
  for y,x in c:a[y,x]=0
 poses[str(n)]=a;save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,D/f'key_{n:03d}.png')
 _,bounds,safe=original(n);h,w=a.shape;choices=[]
 for y in range(-40,1):
  for x in range(-28,1):
   bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]));target=-30 if n==134 else -18
   choices.append((bad*10000+abs(x+hp[0]+12)+abs(y+hp[1]-target)*2,bad,x,y))
 _,bad,x,y=min(choices);world=np.zeros((192,192),np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a
 records.append({'frame':n,'source_scale':.063,'position':[x,y],'head_world':[x+hp[0],y+hp[1]],'head_local':hp,'size':[w,h],'outside':bad,'body_pixels':int(np.count_nonzero(a))-309})
 review.alpha_composite(rgba(world).crop((48,40,144,128)).resize((384,352),Image.Resampling.NEAREST),(i*400,8));dr.text((i*400+4,4),str(n)+' outside '+str(bad),fill='white')
np.savez(D/'key_pixels.npz',**poses);(D/'key_registration.json').write_text(json.dumps(records,indent=2),'utf8');review.save(D/'key_review.png');print(json.dumps(records))
