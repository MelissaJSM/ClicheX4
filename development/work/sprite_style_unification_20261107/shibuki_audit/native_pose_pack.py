"""새 native 그림을 옛 머리/윤곽으로 덮지 않고 등록하는 실험 패커.

before/after 둘 다 준비되지 않은 pilot은 용량 조사만 하고 ARC를 쓰지 않는다.
입력은 384px canvas, origin(160,160), palette-index PNG(0..15)이다.
"""
from pathlib import Path
import argparse, hashlib, json, struct, sys
H=Path(__file__).resolve().parent; ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from src.psx_player import composition_frame,graphics_bank,decode_stream,bank_offsets,indexed_atlas
from src.psx_compress import encode_stream
from src.psx_disc import file_hash
from scripts.discover_inputs import psx_arc

SOURCE=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
SOURCE_SHA='21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'
ARC_SHA='98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e'
PARTS=(0,5,6,7,8);IDLE={0,115,116,117,118,119};PILOT=(1,11,13,17,33,71)
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def crop(a):
 c=a[80:240,80:240].copy();need(np.count_nonzero(c)==np.count_nonzero(a),'160x160 staging canvas clips source');return c
def load(path):
 im=Image.open(path);a=np.array(im);need(a.shape==(384,384) and a.dtype==np.uint8 and int(a.max())<16,'Wrong native input');crop(a);return a
def same_rgba(arc,a,b):return np.all(np.array(arc.rgba(a,16))==np.array(arc.rgba(b,0)),axis=2)

def shared_components(images):
 """동일 좌표의 동일 texel만 분리 공유한다. 재색상/크기변환 없음."""
 unique=[];lookup=[]
 for a in images:
  k=next((i for i,b in enumerate(unique)if np.array_equal(a,b)),None)
  if k is None:k=len(unique);unique.append(a.copy())
  lookup.append(k)
 residual=[a.copy()for a in unique];pieces=[];owners=[]
 # Primarily catches body vs firing-arm and body vs native dust variants.
 for _ in range(32):
  candidates=[]
  for i,a in enumerate(residual):
   for j in range(i+1,len(residual)):
    b=residual[j];m=(a==b)&(a>0);area=int(m.sum())
    if area<128:continue
    # Require a dense enough common section to avoid highly fragmented parts.
    yy,xx=np.nonzero(m)
    if area/((yy.max()-yy.min()+1)*(xx.max()-xx.min()+1))<0.25:continue
    candidates.append((area,i,j,m))
  if not candidates:break
  _,i,j,m=max(candidates,key=lambda q:q[:3]);p=np.where(m,residual[i],0).astype(np.uint8)
  use=[k for k,a in enumerate(residual)if np.array_equal(a[m],p[m])]
  pieces.append(p);owners.append(use)
  for k in use:residual[k][m]=0
 for k,a in enumerate(residual):
  if a.any():pieces.append(a);owners.append([k])
 return pieces,[[i for i,use in enumerate(owners)if k in use]for k in lookup]

def lossless_pack(images):
 try:
  raw,parts=pack_many_patterns(bytes(4096),32,images,set(range(1,32)),[24]*len(images))
  return raw,parts,'whole_patterns'
 except ValueError as initial:
  components,mapping=shared_components(images)
  try:raw,rr=pack_many_patterns(bytes(4096),32,components,set(range(1,32)),[24]*len(components))
  except ValueError as final:raise ValueError(str(initial)+'; shared-components: '+str(final))from final
  parts=[[r for k in ks for r in rr[k]]for ks in mapping]
  need(all(len(r)<=24 for r in parts),'Shared component parts exceed24')
  return raw,parts,'exact_shared_texel_components'

def packing(arcdata,before,after,probe=False,split_offsets=frozenset()):
 need(sha(arcdata)==ARC_SHA,'Wrong current PL02');need(set(before)==set(after),'Both costume target lists must match')
 selected=set(before);need(not(selected&IDLE),'Accepted idle cannot change');need(selected and selected<=set(range(1,105)),'First pilot scope restricted to main movement refs')
 for n in selected:
  for kind,values in(('before',before),('after',after)):
   v=values[n];need(v.shape==(384,384)and v.dtype==np.uint8 and int(v.max())<16,f'Wrong indexed {kind} target {n}');crop(v)
 arc=Archive(arcdata);g,c=arc.g,arc.c;bank=arc.banks[0];groups={}
 for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 changes={b:{}for b in PARTS};replacements={};counts={};expected={};reports=[];conflicts=[]
 workgroups=[]
 for off,refs in groups.items():
  if off not in split_offsets:workgroups.append((off,refs));continue
  for n in refs:
   if n in selected:workgroups.append((off,[n]))
   else:
    f=bank['frames'][n];replacements[n]=decode_stream(g,off,f['limit'],f['tile_count']*128).data;counts[n]=f['tile_count']
 for off,refs in workgroups:
  if not(selected&set(refs)):continue
  need(not(set(refs)&IDLE),'Shared stream would modify idle')
  targets={};keys=[];planes=[]
  for n in refs:
   for b in PARTS:targets[n,b]=arc.layer(n,b)[0].copy()
   if n in selected:
    need(before[n].shape==after[n].shape==(384,384),'Wrong target dimensions')
    uncovered=(after[n]>0)&(before[n]==0)
    if uncovered.any():conflicts.append({'ref':n,'after_pixels_outside_before':int(uncovered.sum())})
    targets[n,0]=after[n]
    targets[n,5]=np.where(same_rgba(arc,before[n],after[n]),0,before[n]).astype(np.uint8)
    for b in (6,7,8):
     need(not arc.layer(n,b)[0].any(),'Unexpected separate armor component; explicit target required')
     targets[n,b]=np.zeros((384,384),np.uint8)
   for b in PARTS:
    a=crop(targets[n,b])
    for p in range(4):
     v=np.where((a//16==p)&(a>0),a%16,0).astype(np.uint8)
     if v.any():keys.append((n,b,p));planes.append(v)
  # Tile0 is transparent. Edge tile16 is usable only with native x padding;
  # pack_many_patterns shifts its part origin and leaves first column empty.
  # No old-head or old-contour overwrite; exact target rasters are packed.
  try:raw,assigned,method=lossless_pack(planes)
  except ValueError as e:
   if len(refs)>1 and off not in split_offsets:
    return packing(arcdata,before,after,probe,split_offsets|{off})
   raise ValueError(f'Shared refs {refs}: {e}') from e
  rr={(n,b):[]for n in refs for b in PARTS}
  for (n,b,p),parts in zip(keys,assigned):rr[n,b].extend((t,x,y,fl|(p<<2))for t,x,y,fl in parts)
  for n in refs:
   for b in PARTS:
    parts=rr[n,b] or [(0,72,72,0)]
    need(len(parts)<=24,'Native part limit requires investigation')
    need(all(-128<=x-80<=127 and -128<=y-80<=127 for t,x,y,f in parts),'Part origin outside signed range')
    changes[b][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
    expected[n,b]=targets[n,b]
   replacements[n]=raw;counts[n]=32
  atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
  need(not atlas[:,0].any(),'GPU U underflow column nonempty')
  reports.append({'refs':refs,'target_refs':sorted(selected&set(refs)),'packing_method':method,'decoded_bytes':4096,'used_tiles':sorted({t for parts in assigned for t,x,y,fl in parts}),'parts':{str(n):{str(b):len(rr[n,b])or 1 for b in PARTS}for n in refs},'encoded_bytes':len(encode_stream(raw))})
 if conflicts and not probe:raise ValueError('Cannot erase visible after pixels with transparent coat: '+json.dumps(conflicts))
 nc=c;slack={}
 for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
 ng,gr=repack_variable(g,replacements,counts)
 result=replace_entry(replace_entry(arcdata,2,ng),3,nc);out=Archive(result)
 for (n,b),want in expected.items():need(np.array_equal(out.layer(n,b)[0],want),f'Exact target mismatch {n}/{b}')
 rawchecks=0
 for gb,bb in enumerate(arc.banks):
  for f in bb['frames']:
   n=f['index'];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nf=out.banks[gb]['frames'][n];new=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   need(new==(replacements[n]if gb==0 and n in replacements else old),'Unselected decoded stream changed');rawchecks+=1
 partchecks=0
 for b in range(len(bank_offsets(c))):
  for n in range(composition_frame(c,b,0)['bank_frame_count']):
   if b in changes and n in changes[b]:continue
   need(records(c,b,n)==records(nc,b,n),'Unselected part records changed');partchecks+=1
 for e in psx_arc(arcdata):
  t=int(e['type'],16)
  if t not in (2,3):need(entry(arcdata,t)==entry(result,t),'Non graphics entry changed')
 changed_images=0;preserved_images=0
 for n in range(237):
  if n in {105,*range(175,183)}:continue
  for mask in (0,15):
   actual=out.composite(n,mask)[0]
   if n in selected:
    want=arc.rgba(after[n],0)if mask==0 else arc.rgba(before[n],16)
    if not probe:need(actual.tobytes()==want.tobytes(),f'Final display target mismatch {n}/{mask}')
    changed_images+=1
   else:need(actual.tobytes()==arc.composite(n,mask)[0].tobytes(),'Unselected display changed');preserved_images+=1
 need(len(result)==len(arcdata),'ARC size changed')
 return result,{'probe_only':probe,'not_ready_for_game':bool(conflicts)or probe,'conflicts':conflicts,'groups':reports,'parts_slack':slack,'graphics':gr,'decoded_references_checked':rawchecks,'preserved_part_records_checked':partchecks,'selected_display_targets':changed_images,'preserved_display_targets':preserved_images,'old_detail_overwrite':False,'palette_and_all_other_entries_exact':True,'runtime_verified':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path);p.add_argument('--refs',default=','.join(map(str,PILOT)));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();need(out.is_relative_to(H.resolve())and not out.exists(),'Fresh audit output required');need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed')
 data,recs=read_disc(SOURCE,('PL02_U.ARC',));raw=data['PL02_U.ARC'];arc=Archive(raw);refs=list(map(int,a.refs.split(',')))
 before={n:load(a.before/f'{n:03}_indices.png')for n in refs};after={n:load(a.after/f'{n:03}_indices.png')if a.after else arc.layer(n)[0]for n in refs}
 out.mkdir(parents=True)
 try:result,proof=packing(raw,before,after,not bool(a.after))
 except ValueError as e:write(out/'capacity.json',{'passed':False,'reason':str(e),'source_sha256':SOURCE_SHA,'art_not_simplified':True});print(str(e));return
 proof.update({'passed':True,'source_sha256':SOURCE_SHA,'source_arc_sha256':sha(raw),'packed_arc_sha256':sha(result),'before_art_hashes':{str(n):sha((a.before/f'{n:03}_indices.png').read_bytes())for n in refs}})
 if a.after:
  (out/'PL02_U.ARC').write_bytes(result);write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':sha(raw),'after':sha(result)}}})
 else:proof['arc_not_written_reason']='새 after 원화가 없으므로 옛 base와의 alpha 충돌을 숨기지 않고 용량 검사까지만 수행함.'
 write(out/'capacity.json',proof);print(json.dumps({'passed':True,'probe_only':proof['probe_only'],'groups':len(proof['groups']),'conflicts':proof['conflicts'],'parts_slack':proof['parts_slack'],'graphics_slack':proof['graphics']['remaining_slack']}))
if __name__=='__main__':main()
