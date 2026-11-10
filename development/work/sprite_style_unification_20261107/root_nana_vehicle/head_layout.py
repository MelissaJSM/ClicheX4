"""Reuse existing head rectangle records while retaining every new art pixel."""
import struct
import numpy as np
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame

def choose_head(a,target,dys):
 existing=set()
 for n in range(composition_frame(a.c,5,0)['bank_frame_count']):
  for q in struct.iter_unpack('<BBbb',records(a.c,5,n)):
   fl,t,x,y=q
   if not fl and 0<t<32 and t!=16:existing.add(q)
 points=[(int(x-160),int(y-160))for y,x in np.argwhere(target)]
 full=(1<<len(points))-1;pool=[]
 for q in sorted(existing):
  fl,t,x,y=q;mask=sum(1<<i for i,(px,py)in enumerate(points)if x<=px<x+16 and y<=py<y+16)
  if mask:
   score=sum((fl,t,x,y+dy)in existing for dy in dys)
   pool.append((q,mask,score))
 best=None
 for q,mask,score in pool:
  for r,rm,rs in pool:
   if q[1]==r[1] or mask|rm!=full:continue
   rank=(score+rs,mask.bit_count()+rm.bit_count(),-abs(q[2])-abs(r[2]))
   if best is None or rank>best[0]:best=(rank,q,r)
 if best is None:raise ValueError('No exact two existing head rectangles')
 return b''.join(struct.pack('<BBbb',*q)for q in best[1:]),{'existing_record_matches':best[0][0],'possible_matches':2*len(dys),'records':best[1:]}
