from pathlib import Path
import numpy as np,json
from PIL import Image
H=Path(__file__).resolve().parent
for n in (6,10,30):
 b=np.array(Image.open(H/f'shot_registered01/before/{n:03}_indices.png'));old=np.array(Image.open(H/f'shot_registered01/after/{n:03}_raw_generated.png'));m=np.array(Image.open(H/f'shot_registered01/after/{n:03}_edit_mask.png'))>0
 candidates=[]
 for dy in range(-4,5):
  for dx in range(-4,5):
   a=np.roll(np.roll(old,dx,1),dy,0);count=int(np.count_nonzero(m&(a>0)&(b==0)));valid=int(np.count_nonzero(m&(a>0)&(b>0)));candidates.append((count,-valid,abs(dx)+abs(dy),dx,dy))
 print(n,sorted(candidates)[:12])
