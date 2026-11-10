from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent;a=np.array(Image.open(d/'paired_body/run_023.png'))
yy,xx=np.nonzero(a);ey,ex=np.nonzero(a==7);left=int(xx.min());eye=round(float(np.median(ey)))
layout=json.loads((d/'joint_layout.json').read_text())
for dy in (0,-1,1,-2,2,-3,3,-4,4):
 for dx in (0,1,-1,2,-2,3):
  x,y=left+dx,eye+dy;m=a!=0;m[y:y+16,x:x+16]=False;test=cover(m,5,2)
  print(json.dumps({'x':x,'y':y,**test}),flush=True)
  if test['fits']:
   (d/'joint_layout_before_pair23.json').write_text(json.dumps(layout,indent=2))
   for i,r in enumerate(layout):
    if r['frame']==23:layout[i]={**test,'frame':23,'arm_rect':[x,y]}
   (d/'joint_layout.json').write_text(json.dumps(layout,indent=2));sys.exit(0)
raise RuntimeError('No 5 common + arm layout')
