"""Independent output reader; no artist/packing functions imported."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_erosion
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
D=Path(__file__).parent/'rin_extension';P=D/'prepared_hurt_lowhp_v1'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas,compose_indices
from scripts.build_sprite_style_unification import check_static_body
sha=lambda b:hashlib.sha256(b).hexdigest()
priorpath=D/'final100_readback_audit.json'
assert sha(priorpath.read_bytes())=='05bd554146e9d7c7f90b6fe0550066f7fc15212a48a194725ee6a8d182a94cea'
prior=json.loads(priorpath.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256']
baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='72d04d36dde42379a144dc4688b09c582e4c0f867bc70d5742c33bb65b75b42a'
new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
ART=D/'hurt_registered_v2';meta=json.loads((ART/'registration.json').read_text('utf8'));masters={}
art_hash={135:'e0f103a55a24bf4d7a6c7f133cba305b34fae8723471d9efb382b1420549323a',139:'2ebe80f7d0451d3d3b12a4d07739481c53dacabf908cf5e070c008e28a5d98e6',149:'d4e216703487a0a2ab9e621a412bd90466301f0439d4475348048a57053207a5',152:'b1f1a363552695a3e660a269dc0fa7ef6faa746eca5c3b8b90913966caab006d'}
provenance=[]
for rec in meta['records']:
 n=rec['ref'];p=ART/f'b0_{n:03}_indices.png';assert sha(p.read_bytes())==art_hash[n]
 rawpath=ROOT/rec['source_native'];assert sha(rawpath.read_bytes())==rec['source_native_sha256']
 assert sha((rawpath.parent.parent/'generated.png').read_bytes())==rec['source_generated_sha256']
 result=np.array(Image.open(rawpath));assert result.dtype==np.uint8 and result.shape==(384,384) and result.max()<=15
 for op in rec['operations']:
  if 'source_iris'in op:
   x,y=op['source_iris'];assert op['source_cyan_votes']>=10 and op['index']==15
   result[y,x]=15
  elif op['name']=='head':
   maskimg=Image.new('1',(384,384));ImageDraw.Draw(maskimg).polygon(op['polygon'],fill=1)
   mask=np.array(maskimg,bool);dx,dy=op['delta'];head=np.roll(np.roll(result,dx,1),dy,0);moved=np.roll(np.roll(mask,dx,1),dy,0)
   result[mask]=0;result[moved]=head[moved]
  elif op['name']=='wholebody':
   dx,dy=op['delta'];result=np.roll(np.roll(result,dx,1),dy,0)
  else:raise AssertionError(op)
 target=np.array(Image.open(p));assert np.array_equal(result,target)
 assert rec['old_pixels_pasted']==0 and np.where(result>0)[0].max()==rec['floor_before']==rec['floor_after']
 masters[n]=result;provenance.append({'ref':n,'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes()),'reconstructed_from_generated_native':True})
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
assert replace_entry(replace_entry(new,2,g),3,c)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(c)==bank_offsets(nc)
def layer(arc,n,start):
 gg,cc=entry(arc,2),entry(arc,3);f=graphics_bank(gg,0)['frames'][n]
 raw=decode_stream(gg,f['offset'],f['limit'],f['tile_count']*128).data
 cp=composition_frame(cc,0,n);cp={**cp,'parts':cp['parts'][start:]}
 px,size,bb,_=compose_indices(raw,f['tile_count'],cp,allowed_cluts={0,2})
 out=np.zeros((384,384),np.uint8);out[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 return out
targets={n:a.copy()for n,a in masters.items()};effect_records=[]
for master,refs in ((135,(136,137)),(139,(140,141))):
 for n in refs:
  effect=layer(old,n,10);assert np.array_equal(layer(new,n,10),effect)
  cp,np_=composition_frame(c,0,n),composition_frame(nc,0,n)
  sem=lambda parts:[{k:v for k,v in x.items()if k!='record_offset'}for x in parts]
  assert sem(cp['parts'][10:])==sem(np_['parts'][10:])
  targets[n]=np.where(effect>0,effect,masters[master]);effect_records.append({'ref':n,'original_pixels_and_geometry_clut_exact':True})
for master,n in ((135,138),(139,142)):
 mask=masters[master]>0
 targets[n]=np.where(binary_dilation(mask,np.ones((3,3),bool)),np.where(mask&(masters[master]!=11),10,11),0).astype(np.uint8)
m=masters[139]>0
cross=np.array([[0,1,0],[1,1,1],[0,1,0]],bool)
targets[143]=np.where(m,np.where(binary_erosion(m,cross),47,37),0).astype(np.uint8)
mapping=np.array([0,7,8,9,8,9,10,9,10,11,11,11,13,14,11,11],np.uint8)
targets[144]=mapping[masters[139]]
near=binary_dilation(m,cross)&~m
far=binary_dilation(m,cross,iterations=2)&~m&~near
targets[145]=np.where(near,37,np.where(far,38,targets[144])).astype(np.uint8)
for master,refs in ((149,(149,150,151)),(152,(152,153,154))):
 for n in refs:
  assert np.array_equal(render(old,0,0,n)[0],render(old,0,0,master)[0]);targets[n]=masters[master]
assert set(targets)==set(range(135,146))|set(range(149,155))
counts=collections.Counter();changed=[];changed_parts=[];gpu=0
for b in (0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 assert len(ob['frames'])==len(nb['frames'])
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for of,nf in zip(ob['frames'],nb['frames']):
  n=of['index'];chosen=b==0 and n in targets
  assert of['tile_count']==nf['tile_count']<=32
  raw=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
  nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
  counts['raw']+=1
  if chosen:changed.append(n)
  else:assert raw==nr;counts['non_target_raw_exact']+=1
  cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
  assert len(cp['parts'])==len(np_['parts'])
  if sem(cp['parts'])!=sem(np_['parts']):assert chosen;changed_parts.append(n)
  for x,y in zip(cp['parts'],np_['parts']):
   for k in x:
    if k not in ('record_offset','tile','x','y'):assert x[k]==y[k]
  if b==1 and 42<=n<=49:assert raw==nr;counts['partial8_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];counts['display']+=1
  if chosen:
   assert np.array_equal(z,targets[n]) and not np.array_equal(z,a);counts['target_display_exact']+=1
   aa=np.frombuffer(indexed_atlas(raw,of['tile_count'])[0],np.uint8).reshape(-1,256)
   zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in np_['parts']:
    t=p['tile'];y,x=t//16*16,t%16*16
    if t%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0))
    if p['flip_y'] and t//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0))
    gpu+=1
  else:assert np.array_equal(z,a);counts['non_target_display_exact']+=1
assert counts=={'raw':444,'display':436,'target_display_exact':17,'non_target_raw_exact':427,'non_target_display_exact':419,'partial8_exact':8}
# Check the entire independent spark/lightning tile sets, not just their flattened display.
effect_tiles=0
for n in (135,139):
 of,nf=graphics_bank(g,0)['frames'][n],graphics_bank(ng,0)['frames'][n]
 ar=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
 br=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
 aa=np.frombuffer(indexed_atlas(ar,of['tile_count'])[0],np.uint8).reshape(-1,256)
 bb=np.frombuffer(indexed_atlas(br,nf['tile_count'])[0],np.uint8).reshape(-1,256)
 for t in range(10,of['tile_count']):
  y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],bb[y:y+16,x:x+16]);effect_tiles+=1
 for alias in ((135,136,137)if n==135 else(139,140,141)):
  assert graphics_bank(ng,0)['frames'][alias]['offset']==nf['offset']
static_count=0
for b in (1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):
  assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in ('palette.bin','effect_23.png','effect_24.png'):assert (P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static=check_static_body(baseline,new,proposal['static_body_patch'])
nativepath=D/'rin117_components_native_checks.json';native=json.loads(nativepath.read_text('utf8'));assert native['passed'] and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'candidate_sha256':sha(new),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior100_proof':str(priorpath.relative_to(ROOT)),'prior100_proof_sha256':sha(priorpath.read_bytes()),'previous100_preserved':True,'cumulative_authored_refs':117,'incremental_four_body_masters':4,'incremental_derived_effect_refs':9,'incremental_lowhp_alias_refs':4,'incremental_counts':dict(counts),'producer_functions_called':False,'source_registration_independently_reconstructed':True,'body_master_provenance':provenance,'effect_original_tile_count':effect_tiles,'effects':effect_records,'body_silhouette_and_ring_independently_recomputed':True,'raw_changed_refs':changed,'changed_compositions':changed_parts,'new_gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'static_references_preserved':404,'common_static_checker':static,'native_proof':str(nativepath.relative_to(ROOT)),'native_proof_sha256':sha(nativepath.read_bytes()),'palette_audio_other_entries_exact':True,'bank1_entire_graphics_exact':True,'part_tile_count_and_bank_bounds_preserved':True,'user_accepted':False,'runtime_verified':False,'root_review_only':True,'limitations':['139의 새 피격 자세가 이전보다 약2px 더 웅크린 형태다. 루트 미술 검토에서 허용 범위로 판단했다.','CLUT2 검정색 표시는 저장 팔레트 미리보기의 제한이며, 실제 게임 전기 색상 검증이 아니다.','8개의 부분VRAM 참조와 기존100은 그대로 보존되었다. 이번 결과는 게임 실기 및 전체 그림체 완료를 의미하지 않는다.']}
(D/'final117_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'sha':sha(new),'gpu_parts':gpu,'effect_tiles':effect_tiles}))
