"""Independent read-only audit of Rin91; no producer functions imported."""
from pathlib import Path
import sys,json,hashlib,collections,argparse
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from scripts.build_sprite_style_unification import check_static_body
sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--expected-sha256',required=True);args=p.parse_args()
prior_path=D/'final84_readback_audit.json';assert sha(prior_path.read_bytes())=='fe7f02c36255c32e1ba5496fb88c22d2be8ece719be548afc212e1eaa68a0733';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
P=D/'prepared_victory_details_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)==args.expected_sha256
ART=D/'victory_targets_v1';expected={1:'c81e948cf736f3ea3d268f0eb6c3317890987322b06dc896cc112ebac07460cc',2:'475982f79d685df5b5ccf82e242ed3789c34a6440fdc2df6ed3f97a6f4ece2de',3:'9514b6073047669eecd4d88a3319c345c0a8bd52f6872c90106f5fa58355b3d1',4:'c024927198dd2c3a9beb279546ba047a40b528fc66f6d1b84ee1c88dea4ff3ca',6:'4cf50db05c5f763ece0786a8e5be746fed819dd6d97caf6c747bea75461a3e06',7:'0d30e30a0154527ecc0466fe1bb140c29bcd40c5bbb56aabf713f7f45026e5ad',8:'0bc625ab98ee0a1480ee23e82a8893861b448267b426084312b00fd1d5911b18'}
for folder,h in [('victory_detail01','1db69b93d93ee61e121a156557df87a77c0218f5d772d4f320c0b28b86421719'),('victory_detail02','0fc788eb53bc774697af9b5b7167d07457eebce27d01973fb941a5203ec6d956')]:assert sha((D/folder/'generated.png').read_bytes())==h
targets={};rows=[]
for n,h in expected.items():
 path=ART/f'b1_{n:03}_indices.png';assert sha(path.read_bytes())==h;a=np.array(Image.open(path));assert a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15;targets[1,n]=a
 rows.append({'bank':1,'ref':n,'master':n,'path':str(path.relative_to(ROOT)),'sha256':h})
for r in prior['rows']:assert sha((ROOT/r['path']).read_bytes())==r['sha256']
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert t==nt and replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
support={(1,n)for n in(0,5,9)};owned=set(targets)|support;count=collections.Counter();changed_raw=[];changed_parts=[];gpu_count=0
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 if b==0:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert nf['index']==n;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;assert f['tile_count']==nf['tile_count']<=32;count['raw']+=1
  if raw!=nr:changed_raw.append([b,n])
  if key not in owned:assert raw==nr;count['non_owned_raw_exact']+=1
  cp,ncp=composition_frame(c,b*5,n),composition_frame(nc,b*5,n);fields=lambda q:[{k:v for k,v in p.items()if k!='record_offset'}for p in q['parts']]
  if fields(cp)!=fields(ncp):assert key in targets;changed_parts.append([b,n])
  assert len(cp['parts'])==len(ncp['parts'])
  for p,q in zip(cp['parts'],ncp['parts']):
   for k in p:
    if k not in('record_offset','x','y'):assert p[k]==q[k],(b,n,k)
  if b==1 and 42<=n<=49:assert raw==nr and fields(cp)==fields(ncp);count['partial8_raw_parts_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];count['display']+=1
  if key in targets:assert np.array_equal(z,targets[key])and not np.array_equal(a,z);count['new_authored_exact']+=1
  else:assert np.array_equal(a,z);count['other_display_exact']+=1
  if key in support:count['shared_support_display_exact']+=1
  if key in owned:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in ncp['parts']:
    tile=p['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0)),(b,n,tile)
    if p['flip_y']and tile//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0)),(b,n,tile)
    gpu_count+=1
assert count=={'raw':444,'non_owned_raw_exact':434,'display':436,'other_display_exact':429,'partial8_raw_parts_exact':8,'new_authored_exact':7,'shared_support_display_exact':3}
for refs in [(0,1,2),(3,4),(5,6),(7,8,9)]:
 frames=graphics_bank(ng,1)['frames'];assert len({frames[n]['offset']for n in refs})==1
assert c==nc, 'Composition bytes changed'
for phase,radius in [(7,1),(8,2)]:
 for original,data in [(True,old),(False,new)]:
  body=render(data,1,5,3)[0];mask=body>0;derived=np.zeros_like(body)
  for dy in range(-radius,radius+1):
   for dx in range(-radius,radius+1):
    if abs(dx)+abs(dy)<=radius:derived[np.roll(np.roll(mask,dy,0),dx,1)]=11 if phase==7 else 10
  pale=np.array([0,10,10,10,11,11,10,11,11,11,10,10,11,10,11,11],np.uint8);derived[mask]=body[mask]if phase==7 else pale[body[mask]]
  assert np.array_equal(derived,render(data,1,5,phase)[0]),(original,phase)
for r in prior['rows']:assert np.array_equal(render(new,r['bank'],r['bank']*5,r['ref'])[0],render(old,r['bank'],r['bank']*5,r['ref'])[0])
static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static_positive=check_static_body(baseline,new,proposal['static_body_patch'])
native_path=D/'rin91_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior84_proof':str(prior_path.relative_to(ROOT)),'prior84_proof_sha256':sha(prior_path.read_bytes()),'prior84_art_displays_and_source_art_preserved':True,'cumulative_authored_refs':91,'incremental_authored_body_refs':5,'derived_departure_flash_refs':2,'composition_bytes_exact':True,'departure_formula_old_and_new_exact':True,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':changed_raw,'display_changed_refs':[list(k)for k in targets],'changed_compositions':changed_parts,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_and_bank_boundaries_exact':True,'bank0_entire_graphics_exact':True,'new_gpu_boundary_alpha':0,'new_and_support_gpu_parts_checked':gpu_count,'static_references_exact_from84':static_count,'common_static_checker':static_positive,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'targets.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'targets.json').read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review_pending':True,'limitations':['New five victory body poses plus two derived departure flashes; not all-motion or live-game completion.','All original composition bytes, frame order/timing, idle0, refined5 and pure light9..13 remain unchanged.','Partial VRAM42..49 and static23/24 remain unchanged.']}
(D/'final91_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'sha':sha(new),'gpu_parts':gpu_count}))
