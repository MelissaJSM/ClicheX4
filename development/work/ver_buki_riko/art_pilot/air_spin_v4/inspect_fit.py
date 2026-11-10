from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,gfx,parts,pal,profile,bank
from src.psx_player import graphics_bank
D=Path(__file__).parent
BODY=[132,160,161,163,165,167,169,171,173,175]
EFFECT=[133,162,164,166,168,170,172,174,176]

def run():
 im=Image.open(D/'generated_spin.png');a,hp=normalize(sample(im,.0335),front)
 protected=np.zeros_like(a,bool);protected[hp[1]:hp[1]+19,hp[0]:hp[0]+23]=front!=0
 for group in component(a!=0)[1:]:
  if any(protected[y,x] for y,x in group):raise ValueError('Detached approved head pixel')
  for y,x in group:a[y,x]=0
 np.savez(D/'base_sample.npz',pixels=a,head=hp)
 board=Image.new('RGBA',(5*320,2*320),(32,36,48));draw=ImageDraw.Draw(board)
 record=[]
 for i,n in enumerate(BODY):
  o,b,safe=original(n);layer=np.zeros((192,192),np.uint8)
  if n in (132,160):
   source=ROOT/'out/ver_buki_riko/riko_bank1_20261025T090314908139Z'/('frame_229.png' if n==132 else 'frame_213.png')
   p=np.array(Image.open(source));yy,xx=np.nonzero(p);p=p[yy.min():yy.max()+1,xx.min():xx.max()+1];head=None
  else:
   angle=(n-161)//2*45;p=np.array(Image.fromarray(a).rotate(angle,resample=Image.Resampling.NEAREST,expand=True));head=None
  h,w=p.shape;options=[]
  for y in range(-32,9):
   for x in range(-32,9):
    bad=int(np.count_nonzero((p!=0)&~safe[96+y:96+y+h,96+x:96+x+w]))
    options.append((bad*10000+(x+w/2)**2+(y+h/2+3)**2,bad,x,y))
  _,bad,x,y=min(options);layer[96+y:96+y+h,96+x:96+x+w]=p
  overlay=np.zeros((192,192,4),np.uint8);overlay[safe]=[50,54,68,255];cell=Image.fromarray(overlay);cell.alpha_composite(rgba(layer))
  board.alpha_composite(cell.crop((56,48,136,124)).resize((320,304),Image.Resampling.NEAREST),(i%5*320,i//5*320+16));draw.text((i%5*320+3,i//5*320+2),f'{n} outside {bad} pos {x},{y}',fill='white')
  offsets={bank['frames'][k]['offset'] for k in [n]}
  shared=[f['index'] if 'index' in f else k for k,f in enumerate(bank['frames']) if f['offset'] in offsets]
  record.append({'frame':n,'bounds':b,'position':[x,y],'shape':[w,h],'outside':bad,'shared':shared,'head_sample':hp})
 board.save(D/'fit_review.png');(D/'fit.json').write_text(json.dumps(record,indent=2),'utf8');print(json.dumps(record))
if __name__=='__main__':run()
