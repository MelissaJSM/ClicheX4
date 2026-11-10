from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
import prepare_targets as t
D=Path(__file__).resolve().parent;m=json.loads((D/'joint_targets01/manifest.json').read_text('utf8'));a=t.Archive((t.ROOT/m['parent_arc']).read_bytes());rows=[]
for n in (87,92):
 ls={pb:np.array(Image.open(D/'joint_targets01'/f'layer{pb}_{n:03}.png'))for pb in t.PBS}
 for mask in range(16):
  z=np.array(t.composite(a,ls,mask))[:,:,3];lab,count=label(z>0,np.ones((3,3)))
  if count>1:
   parts=[]
   for c in range(1,count+1):
    ys,xs=np.where(lab==c)
    if len(xs)<15:parts.append({'count':len(xs),'cells':[[int(x-160),int(y-160)]for y,x in zip(ys,xs)]})
   rows.append({'ref':n,'mask':mask,'small_parts':parts})
print(json.dumps(rows))
