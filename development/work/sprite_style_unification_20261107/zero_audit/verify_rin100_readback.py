"""Independent archive+registered-image reader; never imports a producer."""
from pathlib import Path
import sys,json,hashlib,collections,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from scripts.build_sprite_style_unification import check_static_body
sha=lambda b:hashlib.sha256(b).hexdigest();p=argparse.ArgumentParser();p.add_argument('--expected-sha256',required=True);args=p.parse_args()
prior_path=D/'final97_readback_audit.json';assert sha(prior_path.read_bytes())=='ed461f3fe4080ac7ebea89707fd05000d8ffcf717313f37ed12138e33e283291';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
P=D/'prepared_movement_finish_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)==args.expected_sha256
ART=D/'movement_finish_registered_v1';meta=json.loads((ART/'registration.json').read_text('utf8'));assert sha((D/'movement_finish01/generated.png').read_bytes())==meta['source_art_sha256']=='f5567cc3bc73e52cf1de0d66a5f98a9cafbc0e4efcc8d39e2b1bdac7ce2bfc75'
assert sha((D/'movement_finish01/native/registration.json').read_bytes())==meta['generic_registration_sha256']
expected={37:'45199064f330231d73d6b5497828a6456e6b876a94ea0e5cf281a5ef43bf68c1',45:'da21567b5fa6f73663c651976917117d6104f50b828cb426c232f8b4ecac19f4',193:'f7e1b1d3070e3bc3fa786941bf0adedea82312dcf73ccb7f3cc3a0b8b5698915'}
targets={};rows=[]
for r in meta['records']:
 n=int(r['key'][3:]);path=ART/f'b0_{n:03}_indices.png';assert sha(path.read_bytes())==expected[n];z=np.array(Image.open(path));assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15
 sp=ROOT/r['generic_path'];assert sha(sp.read_bytes())==r['generic_sha256'];a=np.array(Image.open(sp));result=a.copy()
 if r['head_polygon']is not None:
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(r['head_polygon'],fill=1);mask=np.array(m,bool);dx,dy=r['head_translation'];moved=np.roll(np.roll(mask,dx,1),dy,0);head=np.roll(np.roll(a,dx,1),dy,0);result[mask]=0;result[moved]=head[moved]
 dx,dy=r['whole_translation'];result=np.roll(np.roll(result,dx,1),dy,0);assert np.array_equal(result,z)
 original=render(old,0,0,n)[0];assert np.where(z>0)[0].max()==np.where(original>0)[0].max()==r['floor_before']==r['floor_after'];assert r['old_body_pixels_pasted']==0
 targets[0,n]=z;rows.append({'bank':0,'ref':n,'path':str(path.relative_to(ROOT)),'sha256':expected[n],'registered_from_new_source_exact':True})
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
assert entry(old,0x10206)==entry(new,0x10206) and replace_entry(replace_entry(new,2,g),3,c)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
count=collections.Counter();raw_changed=[];parts_changed=[];gpu_count=0
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert nf['index']==n;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;assert f['tile_count']==nf['tile_count']<=32;count['raw']+=1
  if raw!=nr:raw_changed.append([b,n])
  if key not in targets:assert raw==nr;count['non_target_raw_exact']+=1
  cp,ncp=composition_frame(c,b*5,n),composition_frame(nc,b*5,n);sem=lambda q:[{k:v for k,v in x.items()if k!='record_offset'}for x in q['parts']]
  if sem(cp)!=sem(ncp):assert key in targets;parts_changed.append([b,n])
  assert len(cp['parts'])==len(ncp['parts'])
  for op,np_ in zip(cp['parts'],ncp['parts']):
   for k in op:
    if k not in('record_offset','x','y','tile'):assert op[k]==np_[k]
  if b==1 and 42<=n<=49:assert raw==nr and sem(cp)==sem(ncp);count['partial8_raw_parts_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];count['display']+=1
  if key in targets:
   assert np.array_equal(z,targets[key])and not np.array_equal(a,z);count['new_authored_exact']+=1
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for q in ncp['parts']:
    tile=q['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0))
    if q['flip_y']and tile//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0))
    gpu_count+=1
  else:assert np.array_equal(a,z);count['other_display_exact']+=1
assert count=={'raw':444,'non_target_raw_exact':441,'display':436,'other_display_exact':433,'partial8_raw_parts_exact':8,'new_authored_exact':3}
static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static=check_static_body(baseline,new,proposal['static_body_patch'])
native_path=D/'rin100_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior97_proof':str(prior_path.relative_to(ROOT)),'prior97_proof_sha256':sha(prior_path.read_bytes()),'prior97_art_displays_preserved':True,'cumulative_authored_refs':100,'incremental_authored_body_keys':3,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':raw_changed,'display_changed_refs':[list(k)for k in targets],'changed_compositions':parts_changed,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_part_counts_and_bank_boundaries_exact':True,'bank1_entire_graphics_exact':True,'new_gpu_boundary_alpha':0,'new_gpu_parts_checked':gpu_count,'static_references_exact_from97':static_count,'common_static_checker':static,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'registration.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'registration.json').read_bytes()),'source_registration_independently_reconstructed':True,'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review_pending':True,'limitations':['새3자세 작업 ARC의 정적검사이며 실제 게임이나 전체 미술 완료가 아니다.','45 새 부츠의 마지막 행 중심이 원래보다1.5px 오른쪽이다. 발바닥y와 머리 눈y는 원래 기준을 유지한다.','부분 VRAM8·정적404·이전97은 보존한다.']}
(D/'final100_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'sha':sha(new),'gpu_parts':gpu_count}))
