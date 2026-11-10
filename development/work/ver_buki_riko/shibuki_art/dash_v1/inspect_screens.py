from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];d=ROOT/sys.argv[1]
r=json.loads((d/'verification.local.json').read_text());rows=[]
for n in map(int,sys.argv[2:]):
 v=np.array(Image.open(d/f'expected_{n:03d}.png').convert('RGBA'))
 if r['direction']=='right':v=v[:,::-1]
 yy,xx=np.nonzero(v[:,:,3]);best=None
 for meta in json.loads((d/'diagnostic_screens.json').read_text()):
  a=np.array(Image.open(d/meta['image']).convert('RGB'));h=a.shape[0]-v.shape[0]+1;w=a.shape[1]-v.shape[1]+1
  score=np.zeros((h,w),np.uint16)
  for i in np.linspace(0,len(xx)-1,64,dtype=int):
   x,y=int(xx[i]),int(yy[i]);score+=np.all(a[y:y+h,x:x+w]==v[y,x,:3],axis=2)
  for flat in np.argpartition(score.ravel(),-4)[-4:]:
   y,x=np.unravel_index(flat,score.shape);eq=np.all(a[y+yy,x+xx]==v[yy,xx,:3],axis=1);hits=int(eq.sum())
   if best is None or hits>best['hits']:
    dif=np.flatnonzero(~eq);best={'frame':n,'direction':r['direction'],'image':meta['image'],'x':int(x),'y':int(y),'hits':hits,'opaque':len(xx),'mismatch_xy':[[int(xx[i]),int(yy[i])] for i in dif],'actual_colors':a[y+yy[dif],x+xx[dif]].tolist()};crop=a[y:y+v.shape[0],x:x+v.shape[1]].copy()
 if best:
  s=Image.new('RGB',(v.shape[1]*12,v.shape[0]*6),'#26394a');ref=Image.fromarray(v).resize((v.shape[1]*6,v.shape[0]*6),Image.Resampling.NEAREST);s.paste(ref,(0,0),ref);s.paste(Image.fromarray(crop).resize(ref.size,Image.Resampling.NEAREST),(ref.width,0));s.save(d/f'best_{n:03d}.png');rows.append(best)
(d/'best_mismatch.json').write_text(json.dumps(rows,indent=2));print(json.dumps([{k:v for k,v in q.items() if k not in ('mismatch_xy','actual_colors')} for q in rows]))
