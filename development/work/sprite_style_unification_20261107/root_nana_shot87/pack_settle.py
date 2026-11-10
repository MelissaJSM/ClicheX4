"""Pack new return-pose art without altering other native resources or geometry."""
from pathlib import Path
import sys,json,hashlib,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';H=W/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(H),str(W/'root_nana_ladder')]
from preview_restore import Archive,helper
from pack_cycle import raw,PLACEHOLDERS
from pack_air_targets_probe import pack_pinned
from pack_reserved_edge import shared_reserved,fit_two
from repack_part_records_lossless import repack as repack_global
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from scripts.discover_inputs import psx_arc
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));PBS=(0,5,6,7,8)
BEFORE='d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61'
def need(x,msg):
 if not x:raise ValueError(msg)
def composite(a,ls,mask,arm):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im

def pin_head(a,target,pin):
 # Reuse an existing record sequence, not its pixels. The new head is
 # partitioned without loss into those fixed tile rectangles.
 parts=list(struct.iter_unpack('<BBbb',pin))
 need(1<=len(parts)<=9 and all(fl==0 and t not in(0,16)for fl,t,x,y in parts),'Safe pinned head records')
 need(len({p[1]for p in parts})==len(parts),'Distinct pinned head tiles')
 remaining=target.copy();seed=bytearray(4096);_,locations,_=indexed_atlas(bytes(seed),32)
 for fl,t,x,y in parts:
  patch=remaining[160+y:176+y,160+x:176+x].copy();remaining[160+y:176+y,160+x:176+x]=0
  for yy,xx in np.argwhere(patch):
   pos,shift=locations[(t//16*16+int(yy))*256+t%16*16+int(xx)]
   seed[pos]|=int(patch[yy,xx])<<shift
 need(not remaining.any(),'Pinned head coverage')
 return bytes(seed),pin,{p[1]for p in parts}

def common_tall_head(a,targets):
 mask=np.logical_or.reduce([targets[n,5]>0 for n in(87,92)])
 candidates=[];seen=set()
 for n in range(composition_frame(a.c,5,0)['bank_frame_count']):
  rr=records(a.c,5,n)
  if not rr:continue
  for count in range(1,min(7,len(rr)//4)+1):
   one=rr[-4*count:]
   if one in seen:continue
   seen.add(one);parts=list(struct.iter_unpack('<BBbb',one))
   if any(fl or t in(0,16)for fl,t,x,y in parts)or len({t for fl,t,x,y in parts})!=len(parts):continue
   left=mask.copy()
   for fl,t,x,y in parts:left[160+y:176+y,160+x:176+x]=False
   covered=int(mask.sum()-left.sum())
   if covered:candidates.append((-covered,n,one,left))
 for _,ref,one,left in sorted(candidates,key=lambda q:q[:3]):
  rects=fit_two(left[80:240,80:240])
  if rects is None:continue
  used={t for fl,t,x,y in struct.iter_unpack('<BBbb',one)};slots=[s for s in range(31,0,-1)if s not in({16}|used)][:len(rects)]
  pin=one+b''.join(struct.pack('<BBbb',0,s,x-80,y-80)for s,(x,y)in zip(slots,rects))
  change={n:pin for n in(87,92)}
  try:_,_,_=repack_global(a.c,5,change)
  except ValueError:continue
  for n in(87,92):pin_head(a,targets[n,5],pin)
  return pin,{'source_tail_ref':ref,'shared_existing_tail':one.hex(),'new_common_head_records':pin.hex(),'method':'existing record suffix plus exact residual tile rectangles; common across87/92; pixels all new','additional_records':len(rects)}
 raise ValueError('No lossless common head prefix cover')
def build(parent,td):
 need(sha(parent)==BEFORE,'Parent SHA');a=Archive(parent);m=read(td/'manifest.json');need(m['parent_sha256']==BEFORE,'Target parent');refs=tuple(sorted(m['refs']));need(refs==(87,92),'Exact refs')
 targets={};changes={pb:{}for pb in PBS};raws={};groups={};reports=[]
 for q in m['frames']:
  for pb in PBS:
   z=np.array(Image.open(td/f'layer{pb}_{q["ref"]:03}.png'));need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16,'Index format');need(sha(z.tobytes())==q['layer_hashes'][str(pb)],'Target hash');targets[q['ref'],pb]=z
 need(set(targets)=={(n,pb)for n in refs for pb in PBS},'Exact target layer set')
 import scripts.prepare_shibuki_armor_remaining as remaining
 old_fit=remaining.fit
 def fewer_rectangles(mask,count):
  rr=old_fit(mask,count)
  if rr is not None and len(rr)>2:
   two=fit_two(mask)
   if two is not None:return two
  return rr
 remaining.fit=fewer_rectangles
 common_pin,common_proof=common_tall_head(a,targets);print(json.dumps(common_proof),flush=True)
 for n in refs:groups[n]=[n]
 for off,ns in groups.items():
  order=[(n,pb)for n in ns for pb in PBS if targets[n,pb].any()]
  n=ns[0];pin=None;seed=bytes(4096);tiles=set()
  if targets[n,5].any():
   seed,pin,tiles=pin_head(a,targets[n,5],common_pin);order=[k for k in order if k[1]!=5]
  nr,rr,method=pack_pinned(seed,[targets[k][80:240,80:240]for k in order],set(range(1,32))-{16}-tiles)
  method+='; exact head tiles in reused/common record sequence'
  for n in ns:
   raws[n]=nr
   for pb in PBS:changes[pb][n]=struct.pack('<BBbb',0,0,-8,-8)
  for (n,pb),parts in zip(order,rr):changes[pb][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
  if pin is not None:changes[5][ns[0]]=pin
  atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'U boundary')
  for n in ns:
   for pb in PBS:
    need(len(changes[pb][n])//4<=24,'Parts overflow')
    for fl,t,x,y in struct.iter_unpack('<BBbb',changes[pb][n]):
     if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'V boundary')
  reports.append({'refs':ns,'method':method,'parts':{f'{n}/{pb}':len(changes[pb][n])//4 for n in ns for pb in PBS}});print(json.dumps(reports[-1]),flush=True)
 nc=a.c;slack={}
 for pb in PBS:
  try:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
  except ValueError:
   nc,slack[pb],details=repack_global(nc,pb,changes[pb]);print(json.dumps({'bank':pb,'lossless_record_packing':details}),flush=True)
 counts={n:32 for n in refs}
 ng,packing=repack_variable(a.g,raws,counts);result=replace_entry(replace_entry(parent,2,ng),3,nc);b=Archive(result);need(bank_offsets(a.c)==bank_offsets(b.c),'Part bank boundary')
 rc=nr=nl=pc=rg=target_rg=0
 for gb,bank in enumerate(a.banks):
  bb=b.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(bb['base'],bb['end'],len(bb['frames'])),'Graphics bank boundary')
  for q in bank['frames']:
   n=q['index'];isnew=gb==0 and n in refs;need(raw(b,gb,n)==(raws[n]if isnew else raw(a,gb,n)),f'Raw{gb}/{n}');rc+=1;nr+=not isnew
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for pb in PBS:
   expected=targets[n,pb]if n in refs else a.layer(n,pb)[0];need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer{n}/{pb}');nl+=n not in refs
  for mask in range(16):
   for arm in(1,2):
    expected=composite(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in refs else a.composite(n,mask,arm)[0]
    need(b.composite(n,mask,arm)[0].tobytes()==expected.tobytes(),f'RGBA{n}/{mask}/{arm}');rg+=1;target_rg+=n in refs
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if pb in PBS and n in refs:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Parts{n}/{pb}');pc+=1
 need(a.p==b.p,'Palette')
 for e in psx_arc(parent):
  if int(e['type'],16)in(2,3):continue
  sl=slice(e['offset'],e['offset']+e['size']);need(parent[sl]==result[sl],'Other entry')
 return result,{'passed':True,'before':BEFORE,'after':sha(result),'refs':refs,'groups':reports,'head_record_sharing':common_proof,'raw_checked':rc,'nonselected_raw_exact':nr,'nonselected_layers_exact':nl,'target_layers_exact':len(refs)*5,'nonselected_compositions_exact':pc,'rgba_combinations':rg,'target_rgba_combinations':target_rg,'packing':packing,'composition_slack':slack,'palette_other_entries_exact':True,'native_cpu_verified':False,'runtime_verified':False,'targets_manifest_sha256':sha((td/'manifest.json').read_bytes())}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='packed_settle01');ap.add_argument('--targets',default='joint_targets02');args=ap.parse_args();out=(D/args.out).resolve();need(out.is_relative_to(D)and not out.exists(),'Fresh owned output');out.mkdir()
 td=(D/args.targets).resolve();need(td.is_relative_to(D),'Owned targets');m=read(td/'manifest.json')
 try:result,report=build((ROOT/m['parent_arc']).read_bytes(),td)
 except ValueError as e:
  (out/'report.json').write_text(json.dumps({'passed':False,'error':str(e)},ensure_ascii=False,indent=2)+'\n','utf8');raise
 (out/'PL00_U.ARC').write_bytes(result);b=Archive(result)
 refs=report['refs']
 for i in range(0,len(refs),3):helper.grid([(f'shot {n}',[('base idle',b.composite(0)[0]),('new base',b.composite(n)[0]),('Fourth idle',b.composite(0,15)[0]),('new Fourth',b.composite(n,15)[0])])for n in refs[i:i+3]],out/f'readback_{i//3+1}.png',5)
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:report[k]for k in('after','raw_checked','target_layers_exact','target_rgba_combinations','composition_slack')}))
if __name__=='__main__':main()
