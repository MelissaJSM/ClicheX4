from pathlib import Path
import json,collections
import numpy as np
from PIL import Image
D=Path(__file__).parent/'rin_extension';out=[]
for name in ['ground_second01','ground_recovery01','movement_returns01']:
 folder=D/name;info=json.loads((folder/'inputs.json').read_text('utf8'));reg=json.loads((folder/'native/registration.json').read_text('utf8'));im=Image.open(folder/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows'];nw,nh=info['native_cell']
 for f in info['frames']:
  cx,cy=f['cell'];dy=next(q['translate'][1]for q in reg['records']if q['ref']==f['ref']);v=np.array(im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)))).astype(float);r,g,b,a=[v[:,:,k]for k in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0);yy,xx=np.where((a>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15));votes=collections.Counter(zip((info['crop'][0]+xx*nw/cw).astype(int).tolist(),(info['crop'][1]+yy*nh/ch+dy).astype(int).tolist()));votes={p:c for p,c in votes.items()if 135<=p[0]<=175 and 135<=p[1]<=155};best=sorted(votes.items(),key=lambda q:-q[1])[:4];out.append({'ref':f['ref'],'votes':[{'cell':list(p),'actual_cyan_pixels':c}for p,c in best]})
(D/'after141_contact_review/iris.json').write_text(json.dumps(out,indent=2)+'\n','utf8');print(json.dumps(out))
