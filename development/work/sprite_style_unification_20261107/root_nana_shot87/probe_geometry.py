from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive
m=json.loads((D/'inputs01/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());Y,X=np.indices((384,384));Y-=160;X-=160
rows=[]
for n in (87,92):
 b=np.array(Image.open(D/'registered01'/f'base_{n:03}_indices.png'));f=np.array(Image.open(D/'registered01'/f'fourth_{n:03}_indices.png'))
 for form,z in [('base',b),('fourth',f)]:
  old=a.layer(n,0 if form=='base'else 5)[0]
  rows.append({'ref':n,'form':form,'new_eyes':[[int(x-160),int(y-160)]for y,x in np.argwhere((z==14)&(Y<-5))],'old_eyes':[[int(x-160),int(y-160)]for y,x in np.argwhere((old==14)&(Y<-5))],'new_low_bbox':a.rgba(np.where(Y>=6,z,0)).getbbox(),'old_low_bbox':a.rgba(np.where(Y>=6,old,0)).getbbox(),'uncovered_base_leg':[[int(x-160),int(y-160)]for y,x in np.argwhere((b>0)&(f==0)&(Y>=6))]if form=='fourth'else[]})
print(json.dumps(rows))
