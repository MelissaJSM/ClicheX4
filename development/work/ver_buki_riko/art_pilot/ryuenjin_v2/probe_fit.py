from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent
heads=[np.array(Image.open(D.parent/'wall_v1/rear_head_indexed.png')),np.array(Image.open(D.parent/'ladder_v1/rear_head_indexed.png')),front]
im=Image.open(D/'generated_turn.png').convert('RGBA');arr=np.array(im);groups=component(arr[:,:,3]>=220)[:3];groups.sort(key=lambda g:min(x for y,x in g));cells=[]
for group in groups:
 mask=np.zeros(arr.shape[:2],bool)
 for y,x in group:mask[y,x]=True
 cell=arr.copy();cell[~mask,3]=0;cells.append(Image.fromarray(cell))
if __name__=='__main__':
 for scale in (.065,.068,.070,.072):
  board=Image.new('RGBA',(900,420),(32,36,48));dr=ImageDraw.Draw(board)
  for i,n in enumerate((146,148,156)):
   a,hp=normalize(sample(cells[i],scale),heads[i])
   for c in component(a!=0)[1:]:
    for y,x in c:a[y,x]=0
   h,w=a.shape;s=original(n)[2];opts=[]
   for y in range(-40,-5):
    for x in range(-32,1):
     bad=int(np.count_nonzero((a!=0)&~s[96+y:96+y+h,96+x:96+x+w]));opts.append((bad*10000+abs(x+hp[0]+15)*2+abs(y+h-24 if n==146 else y+hp[1]+25)*2,bad,x,y))
   best=min(opts);print(scale,n,(w,h),hp,'body',int(np.count_nonzero(a))-int(np.count_nonzero(heads[i])),'best',best)
   board.alpha_composite(rgba(a).resize((w*5,h*5),Image.Resampling.NEAREST),(i*300,35));dr.text((i*300+3,5),str(n)+' '+str(best[1]),fill='white')
  board.save(D/f'probe_{scale:.3f}.png')
