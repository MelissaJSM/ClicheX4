from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive
from src.psx_player import composition_frame
m=json.loads((D/'inputs01/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());Y,X=np.indices((384,384));Y-=160;X-=160
for n in (90,91):
 for form,mask in (('base',0),('fourth',15)):
  z=np.array(Image.open(D/'registered01'/f'{form}_{n:03}_indices.png'));old=a.layer(n)[0];eye=lambda v:[[int(x-160),int(y-160)]for y,x in np.argwhere((v==14)&(Y<-5)&(X<5))]
  print(json.dumps({'n':n,'form':form,'eyes':eye(z),'old_eye':eye(old),'parts':{pb:len(composition_frame(a.c,pb,n)['parts']) for pb in (0,5,6,7,8)},'left_edge_rows':[(y-160,[(int(x-160),int(z[y,x]))for x in np.flatnonzero(z[y]*(X[y]<=-15))])for y in range(138,153)]}))
