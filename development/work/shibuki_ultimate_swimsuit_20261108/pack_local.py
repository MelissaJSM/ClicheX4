"""현재 ARC의 명시적 레이어만 교체하고 나머지 디코딩 결과를 대조한다."""
from pathlib import Path
import sys,struct,importlib.util
import numpy as np
H=Path(__file__).resolve().parent; ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry,entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable,resize_tile_storage
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from src.psx_player import decode_stream,bank_offsets,composition_frame,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream
from scripts.discover_inputs import psx_arc
from common import sha,write
spec=importlib.util.spec_from_file_location('native_pack_helpers',ROOT/'work/sprite_style_unification_20261107/shibuki_audit/native_pose_pack.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
def compact_parts(c,b,changes):
 try:return repack_parts(c,b,changes)
 except ValueError as original_error:
  starts=bank_offsets(c);start=starts[b];end=starts[b+1] if b+1<len(starts) else len(c)
  count=composition_frame(c,b,0)['bank_frame_count'];rr=[changes.get(n,records(c,b,n)) for n in range(count)]
  unique=list(dict.fromkeys(rr));unique=[v for v in unique if not any(len(w)>len(v) and any(w[i:i+len(v)]==v for i in range(0,len(w)-len(v)+1,4)) for w in unique)]
  while len(unique)>1:
   best=(0,0,1)
   for i,x in enumerate(unique):
    for j,y in enumerate(unique):
     if i==j:continue
     ov=next((k for k in range(min(len(x),len(y)),0,-4) if x[-k:]==y[:k]),0)
     if ov>best[0]:best=(ov,i,j)
   ov,i,j=best;v=unique[i]+unique[j][ov:];unique=[v]+[s for k,s in enumerate(unique) if k not in (i,j)]
  packed=unique[0]
  if not packed.startswith(rr[0]):
   overlap=next((k for k in range(min(len(rr[0]),len(packed)),0,-4) if rr[0][-k:]==packed[:k]),0)
   packed=rr[0]+packed[overlap:]
  if count*4+len(packed)>end-start:raise original_error
  out=bytearray(c);out[start+count*4:start+count*4+len(packed)]=packed
  for n,v in enumerate(rr):
   pos=next(i for i in range(0,len(packed)-len(v)+1,4) if packed[i:i+len(v)]==v)
   struct.pack_into('<I',out,start+n*4,((count+pos//4)<<16)|len(v)//4)
  for n,v in enumerate(rr):assert records(out,b,n)==v
  return bytes(out),end-start-count*4-len(packed)
def pack(data,targets,pbs,preserve_tiles=False):
 a=Archive(data);selected={n for n,b in targets};groups={}
 for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 changes={b:{} for b in pbs};repl={};counts={};expected={};reports=[]
 def group(refs,preserve=preserve_tiles):
  planes=[];keys=[];values={};retained={}
  fixed={b for b in pbs if all((n,b) not in targets or np.array_equal(targets[n,b],a.layer(n,b)[0]) for n in refs)} if preserve else set()
  keep={q['tile'] for n in refs for b in fixed for q in composition_frame(a.c,b,n)['parts']}
  f=a.banks[0]['frames'][refs[0]];original=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
  for n in refs:
   for b in pbs:
    v=targets.get((n,b),a.layer(n,b)[0]).copy();values[n,b]=v
    assert v.shape==(384,384)
    if b in fixed:continue
    residual=v.copy();retained[n,b]=[]
    if preserve:
     for q in composition_frame(a.c,b,n)['parts']:
      part=canvas_from_parts(original,f['tile_count'],{'parts':[{**q,'clut':0}]},(384,384),(160,160))
      plane=q['clut'] if b==0 else 0
      part=np.where(part>0,part%16+plane*16,0).astype('uint8');m=part>0
      if m.any() and np.array_equal(part[m],v[m]):
       retained[n,b].append((q['tile'],q['x']+80,q['y']+80,q['flags']));keep.add(q['tile']);residual[m]=0
    assert not residual[:80].any() and not residual[240:].any() and not residual[:,:80].any() and not residual[:,240:].any(), ('Unretained effect outside crop',n,b)
    for p in range(4):
     w=np.where((residual[80:240,80:240]//16==p)&(residual[80:240,80:240]>0),residual[80:240,80:240]%16,0).astype('uint8')
     if w.any():planes.append(w);keys.append((n,b,p))
  if not planes:
   for n in refs:repl[n]=original;counts[n]=f['tile_count']
   return
  try:
   if preserve:
    raw,parts=pack_many_patterns(resize_tile_storage(original,f['tile_count'],32),32,planes,set(range(1,32))-{16}-keep,[24]*len(planes));method='preserve_unchanged_layer_tiles'
   else:raw,parts,method=helper.lossless_pack(planes)
  except ValueError as problem:
   print('pack retry',refs,'preserve',preserve,str(problem),flush=True)
   if preserve:
    group(refs,False);return
   if len(refs)==1:raise
   for n in refs:group([n])
   return
  rr={(n,b):list(retained.get((n,b),[])) for n in refs for b in pbs}
  for (n,b,p),pp in zip(keys,parts):rr[n,b].extend((t,x,y,fl|(p<<2)) for t,x,y,fl in pp)
  used={t for pp in rr.values() for t,x,y,fl in pp}|{q['tile'] for n in refs for b in fixed for q in composition_frame(a.c,b,n)['parts']}
  _,loc,_=indexed_atlas(raw,32);raw=bytearray(raw)
  for t in set(range(32))-used:
   for ty in range(16):
    for tx in range(16):
     pos,shift=loc[(t//16*16+ty)*256+t%16*16+tx];raw[pos]&=~(15<<shift)
  raw=bytes(raw)
  for n in refs:
   for b in pbs:
    if b in fixed:
     expected[n,b]=values[n,b];continue
    pp=rr[n,b] or [(0,72,72,0)];assert len(pp)<=24
    changes[b][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80) for t,x,y,fl in pp)
    expected[n,b]=values[n,b]
   repl[n]=raw;counts[n]=32
  atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
  if atlas[:,0].any():
   original_atlas=np.frombuffer(indexed_atlas(resize_tile_storage(original,f['tile_count'],32),32)[0],np.uint8).reshape(32,256)
   assert np.array_equal(atlas[:,0],original_atlas[:,0]), 'New GPU edge pixels'
  reports.append({'refs':refs,'method':method,'encoded':len(encode_stream(raw)),'old_encoded':decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).end-f['offset']})
 for refs in groups.values():
  if selected.intersection(refs):group(refs)
 c=a.c;slack={}
 write(H/'pack_debug.json',{'groups':reports,'changes':{str(b):{str(n):[len(records(a.c,b,n))//4,len(v)//4] for n,v in ch.items()} for b,ch in changes.items()}})
 for b,ch in changes.items():
  if ch:c,slack[b]=compact_parts(c,b,ch)
 g,gr=repack_variable(a.g,repl,counts)
 result=replace_entry(replace_entry(data,2,g),3,c);out=Archive(result)
 for k,v in expected.items():assert np.array_equal(out.layer(*k)[0],v),k
 rawchecks=0
 for gb,bb in enumerate(a.banks):
  for f in bb['frames']:
   n=f['index'];nf=out.banks[gb]['frames'][n]
   old=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
   new=decode_stream(g,nf['offset'],nf['limit'],nf['tile_count']*128).data
   assert new==(repl[n] if gb==0 and n in repl else old),(gb,n)
   rawchecks+=1
 preserved=0
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if (n,b) in expected:continue
   assert records(a.c,b,n)==records(c,b,n),(b,n)
   preserved+=1
 for e in psx_arc(data):
  t=int(e['type'],16)
  if t not in (2,3):assert entry(result,t)==entry(data,t)
 assert len(result)==len(data)
 return result,{'parent':sha(data),'result':sha(result),'groups':reports,'target_layers':len(targets),'exact_layers_checked':len(expected),'decoded_streams_checked':rawchecks,'untouched_part_records':preserved,'parts_slack':slack,'graphics':gr,'other_entries_unchanged':True}
if __name__=='__main__':
 from PIL import Image
 p=H/'ver_rin_nana';targets={(n,0):np.array(Image.open(p/f'rin_flutter/{n:03}_indices.png')) for n in (46,47,48)}
 data,proof=pack((p/'PL01_U.ARC').read_bytes(),targets,(0,))
 (p/'PL01_fixed.ARC').write_bytes(data);write(p/'rin_pack.json',proof)
 print(proof)
