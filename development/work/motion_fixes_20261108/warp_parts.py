"""기존 파츠 단위 좌표 보정. 바뀐 작은 타일만 재등록한다."""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sprite_style_unification_20261107/shibuki_audit'))
from optimize_hurt_tile_storage import optimize
import numpy as np
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,decode_stream,indexed_atlas,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from scripts.prepare_riko_ui import replace_entry,entry
from scripts.overhaul_sprites_costume_pack import repack_variable,resize_tile_storage
from pack import compact_parts,records
from common import sha
def warp(data,refs,pbs,transform):
 a=Archive(data);groups={};repl={};counts={};changes={b:{} for b in pbs};expected={};reports=[]
 for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 for off,ns in groups.items():
  if not set(ns)&set(refs):continue
  f=a.banks[0]['frames'][ns[0]];old=decode_stream(a.g,off,f['limit'],f['tile_count']*128).data
  raw=resize_tile_storage(old,f['tile_count'],32);atlas,loc,_=indexed_atlas(raw,32);atlas=np.frombuffer(atlas,np.uint8).reshape(32,256)
  tiles={t:atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy() for t in range(32)}
  parts={};tasks=[];keep={0}
  for n in ns:
   for b in pbs:
    rr=[];want=np.zeros((384,384),np.uint8)
    for q in composition_frame(a.c,b,n)['parts']:
     pic=canvas_from_parts(old,f['tile_count'],{'parts':[{**q,'clut':0}]},(384,384),(160,160))%16
     dest=transform(pic,n,b) if n in refs else pic
     plane=q['clut'] if b==0 else 0;mask=dest>0;want[mask]=dest[mask]+plane*16
     if np.array_equal(pic,dest):
      rr.append((q['flags'],q['tile'],q['x'],q['y']));keep.add(q['tile'])
     else:
      yy,xx=np.nonzero(dest)
      assert len(xx)
      for y in range(int(yy.min()),int(yy.max())+1,16):
       for x in range(int(xx.min()),int(xx.max())+1,16):
        patch=dest[y:y+16,x:x+16].copy()
        if not patch.any():continue
        k=len(rr);rr.append(None);tasks.append((n,b,k,q['flags']&~192,x-160,y-160,patch))
    parts[n,b]=rr;expected[n,b]=want
  # Reuse untouched canonical patterns before allocating an unused old tile.
  for n,b,k,flags,x,y,patch in tasks:
   t=next((t for t,v in tiles.items() if np.array_equal(v,patch) and t%16!=0),None)
   if t is None:
    t=next((t for t in range(1,32) if t%16!=0 and t not in keep),None)
    assert t is not None,('no free tile',ns)
    tiles[t]=patch.copy()
   keep.add(t);parts[n,b][k]=(flags,t,x,y)
  nr=bytearray(raw)
  for t,v in tiles.items():
   if t not in keep:v=np.zeros((16,16),np.uint8)
   for y in range(16):
    for x in range(16):
     pos,sh=loc[(t//16*16+y)*256+t%16*16+x];nr[pos]=(nr[pos]&~(15<<sh))|int(v[y,x])<<sh
  nr,mp,optimization=optimize(bytes(nr),{0,16},5)
  for n in ns:
   repl[n]=bytes(nr);counts[n]=32
   for b in pbs:
    rr=b''.join(struct.pack('<BBbb',fl,mp[t],x,y) for fl,t,x,y in parts[n,b])
    if rr!=records(a.c,b,n):changes[b][n]=rr
  reports.append({'refs':ns,'changed_parts':len(tasks),'tiles':len(keep),'lossless_storage_optimization':optimization})
  print('native warp packed',ns,'saved',optimization['saved'],flush=True)
 c=a.c;slack={}
 for b,ch in changes.items():
  if ch:c,slack[b]=compact_parts(c,b,ch)
 g,gr=repack_variable(a.g,repl,counts);out=replace_entry(replace_entry(data,2,g),3,c);aa=Archive(out)
 for (n,b),v in expected.items():assert np.array_equal(aa.layer(n,b)[0],v),(n,b)
 checks=0
 for gb,bb in enumerate(a.banks):
  for f in bb['frames']:
   n=f['index'];ff=aa.banks[gb]['frames'][n];v=decode_stream(g,ff['offset'],ff['limit'],ff['tile_count']*128).data
   assert v==(repl[n] if gb==0 and n in repl else decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data);checks+=1
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if n not in changes.get(b,{}):assert records(c,b,n)==records(a.c,b,n)
 assert entry(out,9)==entry(data,9) and len(out)==len(data)
 return out,{'parent':sha(data),'result':sha(out),'groups':reports,'graphics':gr,'parts_slack':slack,'exact_layers':len(expected),'decoded_checks':checks}
