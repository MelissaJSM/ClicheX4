from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component,geometry
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba
D=Path(__file__).parent
def run():
 rear=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/wall_v1/rear_head_indexed.png'))
 worlds={};records=[];im=Image.open(D/'generated_wall.png')
 scale=.078
 for i,n in enumerate([50,54,61]):
  cell=im.crop((i*724,0,(i+1)*724,724));a,hp=normalize(sample(cell,scale),rear)
  hx,hy=(-12,-26);x,y=hx-hp[0],hy-hp[1];w=np.zeros((192,192),np.uint8);w[96+y:96+y+a.shape[0],96+x:96+x+a.shape[1]]=a
  worlds[str(n)]=w;records.append({'frame':n,'head_world':[hx,hy],'uniform_scale':scale,'outside':int(np.count_nonzero((w!=0)&~original(n)[2]))})
 np.savez(D/'sample_worlds.npz',**worlds);(D/'sample_registration.json').write_text(json.dumps(records,indent=2))
 old=np.load(ROOT/'work/ver_buki_riko/art_pilot/wall_v1/final_worlds.npz')['39'];w=np.zeros((192,192),np.uint8);w[32:160,32:160]=old;worlds={'old39':w,**worlds}
 board=Image.new('RGBA',(4*320,360),(32,36,48));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w).crop((56,52,136,137)).resize((320,340),Image.Resampling.NEAREST),(i*320,20));draw.text((i*320+5,4),n,fill='white')
 board.save(D/'sample_review.png');print(json.dumps(records))
 ld=ROOT/'work/ver_buki_riko/art_pilot/low_hp_v1';im=Image.open(ld/'generated_low_hp.png');worlds={};records=[];board=Image.new('RGBA',(6*256,300),(32,36,48));draw=ImageDraw.Draw(board)
 for i,n in enumerate(range(149,155)):
  a,hp=normalize(sample(im.crop((i%3*512,i//3*512,(i%3+1)*512,(i//3+1)*512)),.115),front)
  h,wi=a.shape;hx=-13;x=hx-hp[0];y=24-h;w=np.zeros((192,192),np.uint8);w[96+y:96+y+h,96+x:96+x+wi]=a
  worlds[str(n)]=w;records.append({'frame':n,'head_world':[hx,y+hp[1]],'uniform_scale':.115,'outside':int(np.count_nonzero((w!=0)&~geometry(n)[2]))})
  board.alpha_composite(rgba(w).crop((64,52,128,122)).resize((256,280),Image.Resampling.NEAREST),(i*256,20));draw.text((i*256+5,4),str(n),fill='white')
 np.savez(ld/'sample_worlds.npz',**worlds);(ld/'sample_registration.json').write_text(json.dumps(records,indent=2));board.save(ld/'sample_review.png');print(json.dumps(records))
if __name__=='__main__':run()
