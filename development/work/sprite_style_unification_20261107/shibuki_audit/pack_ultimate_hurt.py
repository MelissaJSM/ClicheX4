"""Ultimate 피격13 고정은행 시험 패킹. 모든 비대상raw/조립/표시 보호."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_ultimate_hurt_effects import P,PARENT,PBS,REFS,AUDIT
from prepare_shibuki_hurt_effects import render
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records,repack_parts,pack_shared
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
from src.psx_ui_atlas import tile_pixels,write_tile
from pack_shibuki_hurt import raw,repack_fixed_global,tile_seed
from repack_part_records_lossless import repack as repack_global
from pack_air_targets_probe import pack_pinned
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
D=H/'ultimate_hurt_effect_probe02';MANIFEST='7e1310d1e8411d66d539d2520e36413a978ed5dd0ca5b2650ad0f87f0a84cc4d'
LOCK=H/'ultimate_hurt_locked_inputs02/LOCK.json';LOCK_SHA='8f8aa96148e0a98a392dd2495a57d229c4684c6023596c175ca16373110b675c'
FINAL='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94'

def validate(data,read=lambda p:p.read_bytes()):
 need(sha(data)==PARENT,'Wrong parent');blob=read(LOCK);need(sha(blob)==LOCK_SHA,'Input lock changed');lk=json.loads(blob)
 need(lk['parent_sha256']==PARENT and lk['candidate_sha256']==FINAL and lk['refs']==list(REFS),'Wrong locked scope')
 for name,h in lk['files'].items():
  p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Source escapes workspace');need(sha(read(p))==h,'Source changed '+name)
 return lk

def build(data,progress):
 lock=validate(data);need(sha((D/'manifest.json').read_bytes())==MANIFEST,'Changed targets');meta=json.loads((D/'manifest.json').read_text('utf8'));a=Archive(data);targets={n:{b:np.array(Image.open(D/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS}
 for n,ll in targets.items():
  for b,v in ll.items():need(sha(v.tobytes())==meta['targets'][str(n)][str(b)],'Target changed')
 source=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());need(sha(source.data)=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','Frozen original-spark source changed')
 audit=json.loads((AUDIT/'report.json').read_text('utf8'))['archives'][1];effects={q['ref']:q for q in audit['effects']};changes={b:{}for b in PBS};raws={};groups=[];gpu=0
 for ns in((106,107,108),(110,111),(109,),(112,),(113,),(114,),(233,),(234,235),(236,)):
  core=ns[0];extras={};keep=set();seed_a=a;seed_ref=core
  if core==106:
   seed_a=source;keep={6,7}
   for n in(107,108):
    ps=effects[n]['original_effect_parts'];fx=render(source,n,0,ps);need(np.array_equal(fx,np.load(ROOT/effects[n]['effect_npy'])),'Original spark source not exact');extras[n]={0:ps,5:ps}
  elif core==110:
   ps=effects[111]['actual_CLUT2_records'];keep={int(p['tile'])for p in ps};extras[111]={0:ps,5:ps}
  seed=tile_seed(seed_a,seed_ref,keep);imgs=[crop(targets[core][b])for b in PBS];pool=set(range(32))-{0,16}-keep;variants=None
  if core==234:
   effect=np.array(Image.open(D/'235_historical_effect.png'));need(np.array_equal(np.where(targets[234][0],targets[234][0],effect),targets[235][0]),'Aura order')
   nr,rr,mode=pack_pinned(seed,imgs+[crop(effect)],pool);variants={(n,b):list(rr[i])for n in ns for i,b in enumerate(PBS)};variants[235,0]=rr[5]+variants[235,0]
  elif keep:nr,rr=pack_shared(seed,32,imgs,pool,[24]*5);mode='shared_with_original_effect_tiles'
  else:nr,rr=pack_planes(seed,32,imgs,pool,[24]*5);mode='separate_CLUT_planes'
  duplicate=None
  if core==110:
   used={t for parts in rr for t,x,y,fl in parts}|keep|{0,16};available=sorted(set(range(1,32))-used,reverse=True);need(available,'No safe effect duplicate tile');safe=available[0]
   copied=bytearray(nr);write_tile(copied,safe,tile_pixels(nr,16));nr=bytes(copied)
   extras[111][5]=[{**p,'tile':safe if p['tile']==16 else p['tile']}for p in extras[111][5]]
   need(tile_pixels(nr,safe)==tile_pixels(seed,16),'Copied effect pixels differ')
   duplicate={'ref':111,'parts_bank':5,'original_tile':16,'safe_duplicate_tile':safe,'whole_256_nibbles_exact':True,'original_base_record_tile16_unchanged':True,'reason':'원base의U첫열예외를새layer5로확대하지않기위한동일타일복제'}
  atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);original=np.frombuffer(indexed_atlas(seed,32)[0],np.uint8).reshape(32,256)
  for t in keep:
   sl=(slice(t//16*16,t//16*16+16),slice(t%16*16,t%16*16+16));need(np.array_equal(atlas[sl],original[sl]),'Whole source effect tile changed')
  for n in ns:
   owner=[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']];need(set(owner)<=set(REFS),'Shared non-target raw owner');raws[n]=nr
   for i,b in enumerate(PBS):
    ps=variants[n,b]if variants is not None else rr[i];record=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)
    if not record:need(not atlas[:16,:16].any(),'Blank tile occupied');record=struct.pack('<BBbb',0,0,-8,-8)
    record+=b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in extras.get(n,{}).get(b,[]));need(len(record)//4<=24,f'Parts overflow {n}/{b}')
    for fl,t,x,y in struct.iter_unpack('<BBbb',record):
     if t not in keep:
      if t%16==0:need(not atlas[t//16*16:t//16*16+16,0].any(),'New U boundary')
      if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'New V boundary')
     gpu+=1
    changes[b][n]=record
  groups.append({'refs':list(ns),'source_effect_tiles_preserved':sorted(keep),'effect_source_sha256':sha(seed_a.data)if keep else None,'safe_effect_tile_duplicate':duplicate,'method':mode,'parts':{str(n):{str(b):len(changes[b][n])//4 for b in PBS}for n in ns},'raw_sha256':sha(nr)});progress(groups[-1])
 nc=a.c;slack={};methods={}
 for b,rr in changes.items():
  try:nc,slack[b]=repack_parts(nc,b,rr);methods[b]='existing_exact_record_repack'
  except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,rr)
 progress({'part_slack':slack});ng,graphics=repack_fixed_global(a,raws,{n:32 for n in raws});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Part bank boundaries moved')
 total=nonraw=kept=layers=partial=parts=0
 for gb,bank in enumerate(a.banks):
  nb=actual.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundaries moved')
  for f in bank['frames']:
   n=f['index'];target=raws[n]if gb==0 and n in raws else raw(a,gb,n);need(raw(actual,gb,n)==target,f'Raw mismatch{gb}/{n}');total+=1;nonraw+=not(gb==0 and n in raws)
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in PBS:
   want=targets[n][b]if n in targets else a.layer(n,b)[0];need(np.array_equal(actual.layer(n,b)[0],want),f'Layer mismatch {n}/{b}');layers+=1;kept+=n not in targets
  if n in targets:
   for arm in(1,2):
    for mask in range(16):need(actual.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'Partial RGBA');partial+=1
 for b in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if b in PBS and n in REFS:continue
   need(records(actual.c,b,n)==records(a.c,b,n),'Other records changed');parts+=1
 need(sha(new)==FINAL,'Candidate hash differs')
 return new,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(new),'target_manifest_sha256':MANIFEST,'target_lock_sha256':LOCK_SHA,'locked_inputs':len(lock['files']),'groups':groups,'part_slack':slack,'part_storage_methods':methods,'graphics':graphics,'counts':{'raw':total,'non_target_raw':nonraw,'layers':layers,'non_target_layers':kept,'partial_RGBA':partial,'non_target_records':parts,'GPU_parts':gpu},'preserved_entries':protected_entries(data,new),'art_pixel_loss':False,'scope':'고정은행/32타일 시험후보.독립/최종미술/원MIPS/실기미검증.','runtime_verified':False}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='ultimate_hurt_pack_probe02');z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh own output');o.mkdir();progress=[]
 def log(v):progress.append(v);write(o/'progress.json',progress);print(json.dumps(v),flush=True)
 try:new,proof=build(P.read_bytes(),log)
 except Exception as e:write(o/'report.json',{'passed':False,'error':str(e),'arc_written':False,'progress':progress});raise
 (o/'PL02_U.ARC').write_bytes(new);actual=Archive(new)
 for form,mask in(('before',15),('after',0)):
  for i,refs in enumerate(((106,110,233,234),(107,108,109),(111,112,113),(114,235,236))):page([(f'{n} actual {form}',actual.composite(n,mask)[0])for n in refs],actual.composite(0,mask)[0],o/f'{form}_readback_{i:02}.png',cols=2,scale=5)
 write(o/'report.json',proof);print(json.dumps({'candidate':sha(new),'graphics':proof['graphics'],'counts':proof['counts']}))
if __name__=='__main__':main()
