"""머리 원형·총구·효과를 고정하고 몸통과 접힌 다리의 등록 비례를 보정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from common import write,board
from scripts.export_x_consistency import Archive
from pack import pack
S=H/'ver_rin_nana';OLD=ROOT/'work/sprite_style_unification_20261107/nana_audit';PBS=(0,5,6,7,8)
EYES={33:(-4,-13),35:(-4,-14),37:(-4,-13),39:(-4,-15),41:(-4,-15),43:(-5,-13),45:(-5,-13),47:(-4,-13),49:(-4,-9),51:(-5,-4),53:(-5,-11),67:(-7,-7),69:(-14,-2),71:(-18,6),73:(-18,6),75:(-19,7),77:(-7,-6),79:(-3,-8),81:(8,-12),83:(-3,-12)}
def main(do_pack=False):
 out=S/'body_registration';out.mkdir(exist_ok=True)
 for file,forms in [('PL00_U.ARC',[('base',0),('fourth',15)]),('PL02_U.ARC',[('ultimate_before',15),('ultimate_after',0)])]:
  a=Archive((S/file).read_bytes());targets={};rows=[]
  for n in [*range(33,55),*range(67,85)]:
   base=n if n%2 else n-1;ex,ey=EYES[base];chin=ey+5;ground=22
   sy=1.12 if base<49 else 1.08
   sx=1.12
   if base>=67:sy=1.25 if base in (71,73,75) else 1.15 if base in (69,77,79) else 1.08
   dy=0 if base<49 else -round((ground-chin)*(sy-1))
   # Piecewise inverse registration preserves the original head scale.
   yy,xx=np.indices((384,384));x=xx.astype(float)-160;y=yy.astype(float)-160
   oldy=np.where(y<chin+dy,y-dy,chin+(y-chin-dy)/sy)
   blend=np.clip((oldy-chin)/5,0,1)
   oldx=x/(1+(sx-1)*blend)
   if n%2==0:
    folder='air_repaint' if n<55 else 'dash_repaint'
    gun=np.array(Image.open(OLD/folder/f'fire_constraints/barrel_{n:03}.png'))
    gy,gx=np.nonzero(gun);assert len(gx)
    distance=np.maximum.reduce([gx.min()-xx,xx-gx.max(),gy.min()-yy,yy-gy.max(),np.zeros_like(xx)])
    weight=np.clip((distance-1)/6,0,1)
    oldx=x+(oldx-x)*weight;oldy=y+(oldy-y)*weight
   mapx=np.rint(oldx+160).astype(int).clip(0,383);mapy=np.rint(oldy+160).astype(int).clip(0,383)
   for b in PBS:
    v=a.layer(n,b)[0];body=v.copy();effect=np.zeros_like(v)
    if n in (73,74):
     plain=a.layer(n-2,b)[0];m=(v>0)&(plain==0);effect[m]=v[m];body[m]=0
    dest=body[mapy,mapx];dest[effect>0]=effect[effect>0]
    targets[n,b]=dest;Image.fromarray(dest).save(out/f'{file[:4]}_layer{b}_{n:03}.png')
   rows.append({'ref':n,'head_eye':(ex,ey),'body_x_scale':sx,'body_y_scale':sy,'vertical_registration':dy,'gun_anchored':n%2==0,'head_scale':1})
  if do_pack:
   data,proof=pack(a.data,targets,PBS);(S/(file[:4]+'_fixed.ARC')).write_bytes(data);write(out/(file[:4]+'_pack.json'),proof)
  def rendered(n,mask):
   v=targets[n,0].copy();im=a.rgba(v)
   if mask:
    for b in (8,5,7,6):im.alpha_composite(a.rgba(targets[n,b],32 if b==7 else 16))
   return im
  for form,mask in forms:
   for kind,refs in [('air',[33,37,43,47,49,51]),('dash',[67,69,71,75,77,83]),('shot',[34,38,44,68,72,80])]:
    pics=[('idle reference',a.composite(0,mask)[0]),('idle unchanged',a.composite(0,mask)[0])]
    for n in refs:pics.extend([(f'{form} {n} before',a.composite(n,mask)[0]),(f'{form} {n} registered',rendered(n,mask))])
    board(pics,out/(form+'_'+kind+'.png'),cols=4)
  write(out/(file[:4]+'_registration.json'),rows)
 print('nana registration targets ready',flush=True)
if __name__=='__main__':main('--pack' in sys.argv)
