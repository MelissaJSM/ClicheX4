from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component,geometry,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent;B=ROOT/'out/ver_buki_riko/riko_bank1_20261025T134737617192Z'
im=Image.open(D/'generated_keys.png');scale=float(sys.argv[1]) if len(sys.argv)>1 else .105
def feet(a):
    ys,xs=np.nonzero(a);floor=int(ys.max());xx=np.flatnonzero(np.any(a[floor-2:floor+1]!=0,axis=0));groups=np.split(xx,np.where(np.diff(xx)>1)[0]+1)
    if len(groups)!=2:raise ValueError(('Ambiguous feet',[(int(g.min()),int(g.max())) for g in groups]))
    return [float((g.min()+g.max())/2) for g in groups],floor
idle=np.array(Image.open(B/'idle_147.png'));target,fy=feet(idle);target=[v-24 for v in target];print('idle feet',target,fy-24)
board=Image.new('RGBA',(6*270,330),(32,36,48));draw=ImageDraw.Draw(board);records=[];worlds={}
for i,n in enumerate(range(249,254)):
    source=Image.open(D/'generated_compact.png') if i==0 else im
    cell=source.crop((round(i*source.width/5),0,round((i+1)*source.width/5),source.height));a,hp=normalize(sample(cell,scale),front);a[:hp[1]]=0
    for group in component(a!=0)[1:]:
        if len(group)>3:raise ValueError(('Detached',n,len(group)))
        for y,x in group:a[y,x]=0
    f,floor=feet(a);x=round(sum(t-v for t,v in zip(target,f))/2);y=23-floor
    h,w=a.shape;world=np.zeros((192,192),np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a
    safe=geometry(n)[2];bad=int(np.count_nonzero((world!=0)&~safe));worlds[str(n)]=world
    rec={'frame':n,'head_local':hp,'position':[x,y],'head_world':[x+hp[0],y+hp[1]],'floor':23,'feet_world':[v+x for v in f],
         'feet_center_error':(sum(v+x for v in f)-sum(target))/2,'feet_separation_error':(f[1]-f[0])-(target[1]-target[0]),
         'body_pixels':int(np.count_nonzero(a))-309,'outside':bad,'source_scale':scale};records.append(rec)
    size,b,_=geometry(n);crop=world[96+b[1]:96+b[3],96+b[0]:96+b[2]];save_image(crop.tobytes(),size,pal,D/f'key_{n:03d}.png')
    panel=rgba(world).crop((51,46,141,142)).resize((270,288),Image.Resampling.NEAREST);board.alpha_composite(panel,(270*i,24));draw.text((270*i+3,3),str(n)+' outside='+str(bad),fill='white')
idlew=np.zeros((192,192),np.uint8);idlew[72:120,72:128]=idle;worlds['idle']=idlew
board.alpha_composite(rgba(idlew).crop((51,46,141,142)).resize((270,288),Image.Resampling.NEAREST),(1350,24));draw.text((1353,3),'APPROVED IDLE',fill='white')
board.save(D/'key_review.png');np.savez(D/'key_worlds.npz',**worlds);(D/'key_registration.json').write_text(json.dumps({'idle_feet':target,'keys':records},indent=2),'utf8');print(json.dumps(records))
