from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from collections import deque
P=Path(__file__).parent

def groups(im):
 a=np.array(im);mask=a[:,:,3]>=128;found=[];small=[]
 for yy,xx in np.argwhere(mask):
  if not mask[yy,xx]:continue
  mask[yy,xx]=False;q=deque([(int(xx),int(yy))]);points=[]
  while q:
   x,y=q.popleft();points.append((x,y))
   for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx]:mask[ny,nx]=False;q.append((nx,ny))
  if len(points)<1000:small.append(len(points));continue
  pts=np.array(points);x0,y0=pts.min(0);x1,y1=pts.max(0)+1
  crop=im.crop((x0,y0,x1,y1));found.append(([int(x0),int(y0),int(x1),int(y1)],crop))
 found.sort(key=lambda q:(round(q[0][1]/400),q[0][0]))
 return found,small

if __name__=='__main__':
 info={}
 for kind,rows in [('run',3),('jump',2)]:
  im=Image.open(P/f'generated_{kind}_v1.png').convert('RGBA');found,small=groups(im)
  found.sort(key=lambda q:q[0][1]);ordered=[]
  for r in range(rows):ordered.extend(sorted(found[r*4:(r+1)*4],key=lambda q:q[0][0]))
  print(kind,len(found),'small',len(small),sum(small));items=[]
  for j,(box,crop) in enumerate(ordered):
   a=np.array(crop).astype(np.int32);mask=(a[:,:,3]>=128)&(a[:,:,1]>a[:,:,0]+10)&(a[:,:,1]>a[:,:,2]+10)&(a[:,:,0]>a[:,:,2]-10)
   y,x=np.nonzero(mask);hb=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)];items.append({'box':box,'green_bbox':hb,'green_size':[hb[2]-hb[0],hb[3]-hb[1]]});crop.save(P/f'{kind}_source_{j:02d}.png')
  info[kind]={'items':items,'minor_component_count':len(small),'minor_component_pixels':sum(small)};print(items)
 (P/'source_geometry.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
