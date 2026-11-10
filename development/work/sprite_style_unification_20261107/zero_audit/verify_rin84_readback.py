"""Independent read-only audit of Rin84; no producer functions imported."""
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
prior_path=D/'final80_readback_audit.json';assert sha(prior_path.read_bytes())=='8c7507073c99f0f06b82d60727a0f626c98312391235f248f65297e5aa690b52';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='a565e55fb422764432b03fe60d53430fcd5ede2aa95829a655a9c22bcc902c4d'
P=D/'prepared_rising_rear_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)==args.expected_sha256
ART=D/'rising_registered_contacts_v1';expected={148:'eb978411934bd1510b5604c66e1ee8dfc9a853a17649230c0259941b6ae85daf',150:'ee57b33108c7704309b4b3fdeb71faeafe4a05beabec56bdf0eb5b9c614d4c46',152:'90ff8e0d563ade7b5c188f6caf9da17c0e88bd269c8bd0da07700dec48505bfc',154:'182433f88a6937522d6d0cf6d3f3dbfc74f0a84303e061ca574da8f8d89b0a26'}
assert sha((D/'rising_rear01/generated.png').read_bytes())=='541661aaad1cae0cb822480e40614a2a6128f6969c482e03b0340f117fcebeb4'
targets={};rows=[]
for n,h in expected.items():
 path=ART/f'b1_{n:03}_indices.png';assert sha(path.read_bytes())==h;a=np.array(Image.open(path));assert a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15;targets[1,n]=a
 rows.append({'bank':1,'ref':n,'master':n,'path':str(path.relative_to(ROOT)),'sha256':h})
for r in prior['rows']:assert sha((ROOT/r['path']).read_bytes())==r['sha256']
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert t==nt and replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
support={(1,n)for n in(149,151,153,155)};owned=set(targets)|support;count=collections.Counter();changed_raw=[];changed_parts=[];gpu_count=0
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
  if key in support:count['shared_flame_display_exact']+=1
  if key in owned:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in ncp['parts']:
    tile=p['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0)),(b,n,tile)
    if p['flip_y']and tile//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0)),(b,n,tile)
    gpu_count+=1
assert count=={'raw':444,'non_owned_raw_exact':436,'display':436,'other_display_exact':432,'partial8_raw_parts_exact':8,'new_authored_exact':4,'shared_flame_display_exact':4}
for n in expected:
 frames=graphics_bank(ng,1)['frames'];assert frames[n]['offset']==frames[n+1]['offset']
for r in prior['rows']:assert np.array_equal(render(new,r['bank'],r['bank']*5,r['ref'])[0],render(old,r['bank'],r['bank']*5,r['ref'])[0])
static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static_positive=check_static_body(baseline,new,proposal['static_body_patch'])
native_path=D/'rin84_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior80_proof':str(prior_path.relative_to(ROOT)),'prior80_proof_sha256':sha(prior_path.read_bytes()),'prior80_art_displays_and_source_art_preserved':True,'cumulative_authored_refs':84,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':changed_raw,'display_changed_refs':[list(k)for k in targets],'changed_compositions':changed_parts,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_and_bank_boundaries_exact':True,'bank0_entire_graphics_exact':True,'new_gpu_boundary_alpha':0,'new_and_support_gpu_parts_checked':gpu_count,'static_references_exact_from80':static_count,'common_static_checker':static_positive,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'registration.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'registration.json').read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review_pending':True,'limitations':['용염인 새4몸체와 이전80 보존 검사이며 전동작 미술 통일·실기 완료가 아니다.','152/154 전신 y이동을 취소하고 새원화 부츠만 국소정합했다.','부분VRAM42..49·공유불꽃4·정적23/24의 표시 및 원래 시간표는 보존했다. 실제 모든 전이 실기는 아직이다.']}
(D/'final84_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'sha':sha(new),'gpu_parts':gpu_count}))
