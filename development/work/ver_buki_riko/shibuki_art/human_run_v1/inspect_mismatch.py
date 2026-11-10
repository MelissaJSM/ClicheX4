from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[4];p=root/sys.argv[1];frames=list(map(int,sys.argv[2:]));right=json.loads((p/'verification.local.json').read_text())['direction']=='right';reports=[]
for n in frames:
 im=Image.open(p/f'expected_{n:03d}.png').convert('RGBA');v=np.array(im);v=v[:,::-1] if right else v;yy,xx=np.nonzero(v[:,:,3]);best=None
 for page in (0,256):
  path=p/f'diagnostic_{n:03d}_{page}.png'
  if not path.exists():continue
  a=np.array(Image.open(path).convert('RGB'));height=a.shape[0]-v.shape[0]+1;width=a.shape[1]-v.shape[1]+1;score=np.zeros((height,width),np.uint16)
  for i in np.linspace(0,len(xx)-1,80,dtype=int):
   x,y=int(xx[i]),int(yy[i]);score+=np.all(a[y:y+height,x:x+width]==v[y,x,:3],axis=2)
  for flat in np.argpartition(score.ravel(),-8)[-8:]:
   y,x=np.unravel_index(flat,score.shape);match=np.all(a[y+yy,x+xx]==v[yy,xx,:3],axis=1);hits=int(match.sum())
   if best is None or hits>best['hits']:best={'frame':n,'page':page,'x':int(x),'y':int(y),'hits':hits,'opaque':len(xx),'mismatch_local':[[int(xx[i]),int(yy[i])] for i in np.flatnonzero(~match)]};crop=a[y:y+v.shape[0],x:x+v.shape[1]].copy()
 if best:
  sheet=Image.new('RGB',(v.shape[1]*12,v.shape[0]*6),'#26394a');ref=Image.fromarray(v).resize((v.shape[1]*6,v.shape[0]*6),Image.Resampling.NEAREST);sheet.paste(ref,(0,0),ref);actual=Image.fromarray(crop).resize(ref.size,Image.Resampling.NEAREST);sheet.paste(actual,(ref.width,0));sheet.save(p/f'mismatch_{n:03d}.png');reports.append(best)
print(json.dumps(reports));(p/'mismatch_audit.json').write_text(json.dumps(reports,indent=2))
