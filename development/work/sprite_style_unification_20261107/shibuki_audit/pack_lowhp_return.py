"""확정된 포스 저체력 의상 블록만 원래 gfx0 고정 범위에 무손실 등록한다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from src.psx_player import composition_frame,decode_stream,bank_offsets,indexed_atlas
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,crop,lossless_pack,write
from src.psx_disc import file_hash
from scripts.discover_inputs import psx_arc
from prepare_lowhp_final import make_targets,compose
ARC_SHA='7385562e35ef46b450153690f0ba1b209e85d53022cfd3763e3975d5d1a9dda3'
PARTS=(0,5,6,7,8);SELECTED=set(range(120,126))

def pack(data,desired):
 need(sha(data)==ARC_SHA,'Wrong current PL00 input')
 need(set(desired)==SELECTED,'Only lowHP120..125 allowed')
 src=Archive(data);g,c=src.g,src.c;byoff={}
 for f in src.banks[0]['frames']:byoff.setdefault(f['offset'],[]).append(f['index'])
 changes={b:{}for b in PARTS};raws={};counts={};expected={};logs=[]
 for off,refs in byoff.items():
  if not SELECTED.intersection(refs):continue
  keys=[];images=[];targets={}
  for n in refs:
   for b in PARTS:
    v=src.layer(n,b)[0].copy()
    if n in SELECTED:
     v=desired[n][b].copy();need(v.shape==(384,384)and v.dtype==np.uint8 and int(v.max())<16,'Wrong indexed garment target')
    targets[n,b]=v;cv=crop(v)
    for p in range(4):
     plane=np.where((cv>0)&(cv//16==p),cv%16,0).astype(np.uint8)
     if plane.any():keys.append((n,b,p));images.append(plane)
  raw,assigned,method=lossless_pack(images)
  rr={(n,b):[]for n in refs for b in PARTS}
  for (n,b,p),parts in zip(keys,assigned):rr[n,b].extend((t,x,y,fl|(p<<2))for t,x,y,fl in parts)
  for n in refs:
   for b in PARTS:
    parts=rr[n,b]or[(0,72,72,0)];need(len(parts)<=24,'Native part count exceeded')
    changes[b][n]=b''.join(struct.pack('<BBbb',f,t,x-80,y-80)for t,x,y,f in parts);expected[n,b]=targets[n,b]
   raws[n]=raw;counts[n]=32
  atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'GPU boundary0/16 first column not transparent')
  logs.append({'refs':refs,'packing':method,'parts':{str(n):{str(b):len(rr[n,b])for b in PARTS}for n in refs},'exact_tiles':len({t for p in assigned for t,x,y,f in p})})
 nc=c;slack={}
 for b,rec in changes.items():nc,slack[b]=repack_parts(nc,b,rec)
 ng,gr=repack_variable(g,raws,counts)
 result=replace_entry(replace_entry(data,2,ng),3,nc);out=Archive(result)
 for (n,b),want in expected.items():need(np.array_equal(out.layer(n,b)[0],want),f'Exact layer mismatch{n}/{b}')
 rawchecks=partchecks=0
 for gb,bank in enumerate(src.banks):
  for f in bank['frames']:
   n=f['index'];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nf=out.banks[gb]['frames'][n];new=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   need(new==(raws[n]if gb==0 and n in raws else old),'Nonselected raw changed');rawchecks+=1
 for b in range(len(bank_offsets(c))):
  for n in range(composition_frame(c,b,0)['bank_frame_count']):
   if n in changes.get(b,{}):continue
   need(records(c,b,n)==records(nc,b,n),'Other part record changed');partchecks+=1
 for e in psx_arc(data):
  t=int(e['type'],16)
  if t not in(2,3):need(entry(data,t)==entry(result,t),'Other entry changed')
 need(len(result)==len(data),'Size changed')
 composites=0
 for n in SELECTED:
  for mask in range(16):
   for arm in(1,2):
    target=src.rgba(desired[n][0])
    for bit,b in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:target.alpha_composite(src.rgba(desired[n].get(b,src.layer(n,b)[0]),32 if b==7 and arm==2 else 16))
    need(target.tobytes()==out.composite(n,mask,arm)[0].tobytes(),f'Partial mask target mismatch{n}/{mask}/{arm}');composites+=1
 preserved=0
 for n in range(237):
  if n in SELECTED|{105,*range(175,183)}:continue
  for mask in(0,15):need(out.composite(n,mask)[0].tobytes()==src.composite(n,mask)[0].tobytes(),'Nonselected form changed');preserved+=1
 return result,{'passed':True,'source_arc_sha256':sha(data),'result_arc_sha256':sha(result),'selected_refs':sorted(SELECTED),'changed_layers':list(PARTS),'new_body_and_accepted_idle_head':True,'partial_mask_arm_comparisons':composites,'nonselected_composites':preserved,'decoded_references':rawchecks,'preserved_part_records':partchecks,'groups':logs,'parts_slack':slack,'graphics':gr,'palette_timing_sound_and_other_entries_unchanged':True,'not_full_style_completion':True,'game_runtime_verified':False}

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed')
 baseline=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC'))[0]
 previous=H/'prepared_return158_01';data=(previous/'PL00_U.ARC').read_bytes();original=Archive(baseline['PL00_U.ARC'])
 desired,provenance,owner,common=make_targets(original);result,proof=pack(data,desired)
 out=H/'prepared_lowhp_return01';need(not out.exists(),'Output exists');out.mkdir()
 (out/'PL00_U.ARC').write_bytes(result)
 selection=(previous/'ST0E_U1.ARC').read_bytes();need(sha(selection)=='b15319740e54a2a5fabd6039502cc82d220e50eb40db61584a61d499a814a4df','Selection dependency changed')
 (out/'ST0E_U1.ARC').write_bytes(selection)
 proof.update(combined_return158=True,parent_bin_sha256=SOURCE_SHA,parent_arc_sha256=sha(baseline['PL00_U.ARC']),return158_input_arc_sha256=sha(data),selection_copy_unchanged_from_frozen_return_patch=True)
 write(out/'verification.json',proof);write(out/'provenance.json',provenance)
 write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{name:{'path':(out/name).relative_to(ROOT).as_posix(),'before':sha(baseline[name]),'after':sha(new)}for name,new in [('PL00_U.ARC',result),('ST0E_U1.ARC',selection)]}})
 a=Archive(result)
 for mask,name in((0,'base'),(15,'fourth')):
  items=[]
  for n in sorted(SELECTED):items.extend([(f'{name} {n} old',original.composite(n,mask)[0]),(f'{name} {n} actual',a.composite(n,mask)[0])])
  page(items,a.composite(0,mask)[0],out/f'actual_{name}.png',cols=2,scale=4)
 for n in (120,122,124):page([(f'{n} mask{m:02X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],out/f'partial_{n}.png',cols=4,scale=3)
 page([(f'base return{n}',a.composite(n,0)[0])for n in(156,157,158,159)]+[(f'fourth return{n}',a.composite(n,15)[0])for n in(156,157,158,159)],a.composite(0,15)[0],out/'combined_return.png',cols=4,scale=3)
 print(json.dumps({'passed':True,'sha256':sha(result),'groups':proof['groups'],'parts_slack':proof['parts_slack'],'graphics_slack':proof['graphics']['remaining_slack']}))
if __name__=='__main__':main()
