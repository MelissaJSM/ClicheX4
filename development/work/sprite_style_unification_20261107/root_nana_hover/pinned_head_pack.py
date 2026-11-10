"""Identical head record geometry across hover pairs; artwork remains exact."""
import numpy as np
import struct,json
from scripts.overhaul_sprites_costume_pack import bounded_grid_fit
from src.psx_player import indexed_atlas
from pack_air_targets_probe import pack_pinned
from scripts.prepare_shibuki_ultimate_production import records
from repack_part_records_lossless import repack as global_parts
class HeadPacker:
 def __init__(self,targets,refs,archive):
  union=np.logical_or.reduce([targets[n,5][80:240,80:240]>0 for n in refs])
  seen=set();choices=[]
  for n in range(237):
   rr=list(struct.iter_unpack('<BBbb',records(archive.c,5,n)))
   for length in range(1,min(8,len(rr))+1):
    old=rr[-length:];key=tuple(old)
    if key in seen:continue
    seen.add(key)
    if any(f or t in(0,16)for f,t,x,y in old)or len({t for f,t,x,y in old})!=len(old):continue
    remain=union.copy()
    for f,t,x,y in old:
     if not(0<=x+80<=144 and 0<=y+80<=144):break
     remain[y+80:y+96,x+80:x+96]=False
    else:
     extras=bounded_grid_fit(remain,4)
     if extras is None or len(old)+len(extras)>9:continue
     used={t for f,t,x,y in old};pool=[t for t in range(31,0,-1)if t not in used and t!=16]
     geom=[(t,x+80,y+80)for f,t,x,y in old]+[(t,x,y)for t,(x,y)in zip(pool,extras)]
     changes={}
     for base in refs[::2]:
      heads=[targets[q,5][80:240,80:240]for q in(base,base+1)]
      _,partlists,_=self.head_data(heads,geom)
      for q,parts in zip((base,base+1),partlists):changes[q]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
     try:_,slack,_=global_parts(archive.c,5,changes)
     except ValueError:continue
     choices.append((len(geom),-slack,n,length,geom))
  if not choices:raise ValueError('No existing head suffix fits the fixed composition bank')
  chosen=min(choices);self.geom=chosen[-1];self.rects=[[x,y]for t,x,y in self.geom]
  print(json.dumps({'head_geometry_source_ref':chosen[2],'existing_suffix_records':chosen[3],'common_geometry':self.geom,'bank5_slack':-chosen[1]}),flush=True)
 @staticmethod
 def head_data(images,geom):
  out=bytearray(4096);_,locations,_=indexed_atlas(bytes(out),32);used=set();heads=[];patches={};reserved={t for t,x,y in geom}
  for index,image in enumerate(images):
   remaining=image.copy();rr=[]
   for original,x,y in geom:
    z=remaining[y:y+16,x:x+16].copy();remaining[y:y+16,x:x+16]=0;tile=original
    if index and not np.array_equal(z,patches[tile]):tile=next(t for t in range(1,32)if t!=16 and t not in(reserved|used))
    if tile not in used:
     for yy,xx in np.argwhere(z):
      pos,shift=locations[(tile//16*16+int(yy))*256+tile%16*16+int(xx)];out[pos]|=int(z[yy,xx])<<shift
     patches[tile]=z.copy();used.add(tile)
    rr.append((tile,x,y,0))
   assert not remaining.any();heads.append(rr)
  return bytes(out),heads,used
 def __call__(self,raw,count,images,pool,limits):
  assert count==32;out,heads,used=self.head_data([images[1],images[6]],self.geom)
  order=[i for i in range(10)if i not in(1,6)]
  nr,rr,method=pack_pinned(out,[images[i]for i in order],set(pool)-used)
  result=[None]*10
  for i,r in zip(order,rr):result[i]=r
  result[1],result[6]=heads
  return nr,result
