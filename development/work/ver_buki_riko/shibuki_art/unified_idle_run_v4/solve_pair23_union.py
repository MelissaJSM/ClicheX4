from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent;a=np.array(Image.open(d/'paired_body/run_023.png'))
p=next(r for r in json.loads((d/'paired/pairs.json').read_text())['frames'] if r['run']==23)
shot=np.array(Image.open(d/'paired/shoot_023.png'));different=a!=shot
yy,xx=np.nonzero(different);x0,x1=int(xx.min()),int(xx.max());y0,y1=int(yy.min()),int(yy.max())
print(json.dumps({'difference_bounds':[x0,y0,x1,y1]}),flush=True)
for gx in (18,17,19):
 for gy in (22,23,24,25,26,27,28):
  for ax in (31,30,29,32,28,33):
   for ay in (31,30,32,29,33):
    left=different.copy()
    for x,y in ((gx,gy),(ax,ay)):left[y:y+16,x:x+16]=False
    if np.any(left):continue
    m=a!=0
    for x,y in ((gx,gy),(ax,ay)):m[y:y+16,x:x+16]=False
    test=cover(m,5,.7)
    if test['fits']:
     record={**test,'unique_rects':[[gx,gy],[ax,ay]]};print(json.dumps(record),flush=True)
     (d/'pair23_union_layout.json').write_text(json.dumps(record,indent=2));sys.exit(0)
raise RuntimeError('Uncovered union body')
