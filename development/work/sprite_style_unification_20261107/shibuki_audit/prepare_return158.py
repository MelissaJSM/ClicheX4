"""귀환158의 별도 구형 몸을 최신156 몸으로 동기화. 빛/표/팔레트 보존."""
from pathlib import Path
import json,sys,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from src.psx_player import composition_frame,decode_stream,bank_offsets,indexed_atlas
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,crop,lossless_pack,write
from src.psx_disc import file_hash
from scripts.discover_inputs import psx_arc
ARC_SHA='b6a4f2a5a321e8c37575e6593c3b86f396151c16a16690e16054c86e75f3fd59'
PARTS=(0,5,6,7,8)

def shift(v,dy):
 out=np.zeros_like(v);y,x=np.nonzero(v);need((y+dy).min()>=0,'Shift clips');out[y+dy,x]=v[y,x];return out

def targets(arc):
 # This file is the documented old body before composing the historical ring.
 p=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/native04/frame_158.png'
 oldbody=np.zeros((384,384),np.uint8);oldbody[110:190,112:208]=np.array(Image.open(p))
 old=arc.layer(158)[0];ring=arc.layer(159)[0]
 need(np.array_equal(old[oldbody>0],oldbody[oldbody>0]),'Historical body does not match current158')
 # 158 retained its original-grid clipping: retain its two different outer pixels.
 bg=old.copy();bg[oldbody>0]=ring[oldbody>0]
 body=shift(arc.layer(156)[0],-10);new=bg.copy();new[body>0]=body[body>0]
 layers={0:new,**{b:shift(arc.layer(156,b)[0],-10)for b in(5,6,7,8)}}
 allowed=(oldbody>0)|(body>0)
 for b in(5,6,7,8):allowed|=layers[b]>0
 need(np.array_equal(new[~allowed],old[~allowed]),'Outside body effects changed')
 proof={'historical_source':p.relative_to(ROOT).as_posix(),'historical_source_sha256':sha(p.read_bytes()),'old_body_pixels_exact':int((oldbody>0).sum()),'old158_ring_vs159_outside_body_different_pixels':int(np.count_nonzero((old!=ring)&(oldbody==0))),'old158_outer_clipping_preserved':True,'body_source_ref':156,'body_translation':[0,-10],'body_resized':False,'foreground_order':'native ring first, body on top, then existing leg/head/arm/body armor order','changed_base_pixels':int(np.count_nonzero(new!=old))}
 return layers,bg,allowed,proof

def pack(data):
 need(sha(data)==ARC_SHA,'Wrong current PL00 input');src=Archive(data);g,c=src.g,src.c
 desired,bg,allowed,proof=targets(src);off=src.banks[0]['frames'][158]['offset'];refs=[f['index']for f in src.banks[0]['frames']if f['offset']==off]
 planes=[];keys=[];expected={}
 for n in refs:
  for b in PARTS:
   v=desired[b]if n==158 else src.layer(n,b)[0];expected[n,b]=v;cv=crop(v)
   for p in range(4):
    v=np.where((cv>0)&(cv//16==p),cv%16,0).astype(np.uint8)
    if v.any():keys.append((n,b,p));planes.append(v)
 raw,parts,method=lossless_pack(planes);rr={(n,b):[]for n in refs for b in PARTS}
 for(n,b,p),records_ in zip(keys,parts):rr[n,b].extend((t,x,y,f|(p<<2))for t,x,y,f in records_)
 changes={b:{}for b in PARTS};slack={};nc=c
 for b in PARTS:
  for n in refs:
   r=rr[n,b]or[(0,72,72,0)];need(len(r)<=24,'Too many parts')
   changes[b][n]=b''.join(struct.pack('<BBbb',f,t,x-80,y-80)for t,x,y,f in r)
  nc,slack[b]=repack_parts(nc,b,changes[b])
 ng,gr=repack_variable(g,{n:raw for n in refs},{n:32 for n in refs});result=replace_entry(replace_entry(data,2,ng),3,nc);out=Archive(result)
 atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'GPU first column')
 for(n,b),v in expected.items():need(np.array_equal(out.layer(n,b)[0],v),'Layer exact mismatch')
 rawchecks=0
 for gb,bank in enumerate(src.banks):
  for f in bank['frames']:
   n=f['index'];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nf=out.banks[gb]['frames'][n];new=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   need(new==(raw if gb==0 and n in refs else old),'Unrelated raw changed');rawchecks+=1
 partschecks=0
 for b in range(len(bank_offsets(c))):
  for n in range(composition_frame(c,b,0)['bank_frame_count']):
   if n in changes.get(b,{}):continue
   need(records(c,b,n)==records(nc,b,n),'Other part changed');partschecks+=1
 for e in psx_arc(data):
  t=int(e['type'],16)
  if t not in(2,3):need(entry(data,t)==entry(result,t),'Other entry changed')
 need(len(result)==len(data),'ARC size changed')
 for mask in range(16):
  for arm in(1,2):
   body=src.composite(156,mask,arm)[0];arr=np.array(body);moved=np.zeros_like(arr);moved[:-10]=arr[10:];want=src.rgba(bg);want.alpha_composite(Image.fromarray(moved))
   need(out.composite(158,mask,arm)[0].tobytes()==want.tobytes(),'All-parts156 translation mismatch')
 preserved=0
 for n in range(237):
  if n in{105,158,*range(175,183)}:continue
  for mask in(0,15):need(out.composite(n,mask)[0].tobytes()==src.composite(n,mask)[0].tobytes(),'Other composite changed');preserved+=1
 proof.update({'passed':True,'source_arc_sha256':sha(data),'packed_arc_sha256':sha(result),'refs':refs,'packing_method':method,'used_tiles':len({t for r in parts for t,x,y,f in r}),'part_counts':{str(n):{str(b):len(rr[n,b])for b in PARTS}for n in refs},'parts_slack':slack,'graphics':gr,'decoded_references':rawchecks,'preserved_part_records':partschecks,'all_mask_arm_checks':32,'other_composites':preserved,'palette_timing_sound_entries_exact':True,'not_game_runtime_test':True})
 return result,proof

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed');data=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];src=Archive(data);desired,bg,allowed,proof=targets(src)
 out=H/'prepared_return158_01';need(not out.exists(),'Output exists');out.mkdir()
 result,proof=pack(data);(out/'PL00_U.ARC').write_bytes(result);write(out/'verification.json',proof);write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':sha(data),'after':sha(result)}}})
 a=Archive(result);items=[]
 for mask,label in((0,'base'),(15,'fourth')):
  for n in(156,157,158,159):items.append((f'{label} {n} current',src.composite(n,mask)[0]));items.append((f'{label} {n} prepared',a.composite(n,mask)[0]))
 page(items,a.composite(0,15)[0],out/'comparison.png',cols=4,scale=3)
 Image.fromarray(allowed.astype(np.uint8)*255).save(out/'allowed_body_mask.png');src.rgba(bg).save(out/'preserved_ring.png')
 print(json.dumps({k:v for k,v in proof.items()if k!='graphics'}))
if __name__=='__main__':main()
