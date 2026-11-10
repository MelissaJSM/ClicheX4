"""Separate full ARC reader for Rin80. No producer/registration functions called."""
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
prior_path=D/'final75_readback_audit.json';assert sha(prior_path.read_bytes())=='5431f08087a023cb47978393bf073eefb857e27c047492379324d653cb31697a';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='806b3871055233a5c37c1c2c17685e02aadd07d647be62ea69bf696787f3fbe4'
P=D/'prepared_rear_continuation2_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)==args.expected_sha256
ART=D/'rear_continuation02/native';expected={191:'b49739d80948e2f026f1cb35d3f8cc51f1eab8e05147d86554b169de55fe1e0c',192:'14592ed62637b063f68918d4d1522c341ffead3b2847005dce6062ca0756ba35',194:'58fd05d51a46692c31451a4dfe3e5d442d621405d0be8be5f5d0e21ff7c97378',195:'b0469849ce9192ce6105e9e1bfeb2d75287d0277157eca79377154324d5ff106'}
groups={191:{191:False},192:{192:False},194:{194:False},195:{195:False,196:False}}

def mirror(a):
 r=np.zeros_like(a);y,x=np.nonzero(a);r[y,319-x]=a[y,x];return r
targets={};rows=[]
for master,refs in groups.items():
 path=ART/f'b0_{master:03}_indices.png';assert sha(path.read_bytes())==expected[master];a=np.array(Image.open(path));assert a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15
 for n,flipped in refs.items():
  original=render(old,0,0,master)[0];assert np.array_equal(render(old,0,0,n)[0],mirror(original)if flipped else original)
  targets[0,n]=mirror(a)if flipped else a;rows.append({'bank':0,'ref':n,'master':master,'mirror_x_319_minus_x':flipped,'path':str(path.relative_to(ROOT)),'sha256':expected[master]})
assert sha((D/'rear_continuation02/generated.png').read_bytes())=='cd305386dd977a435b0c6acb4a1e27ec4223ebf0a42523f5d704fd6d039eee0c'
for row in prior['rows']:assert sha((ROOT/row['path']).read_bytes())==row['sha256']
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert t==nt and replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
support={(0,190)};owned=set(targets)|support;count=collections.Counter();changed_raw=[];changed_parts=[];gpu_count=0
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
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
assert count=={'raw':444,'non_owned_raw_exact':438,'display':436,'other_display_exact':431,'partial8_raw_parts_exact':8,'new_authored_exact':5,'shared_support_display_exact':1}
for master,refs in groups.items():
 offsets={graphics_bank(ng,0)['frames'][n]['offset']for n in refs};assert len(offsets)==1
assert graphics_bank(ng,0)['frames'][190]['offset']==graphics_bank(ng,0)['frames'][191]['offset']
for r in prior['rows']:assert np.array_equal(render(new,r['bank'],r['bank']*5,r['ref'])[0],render(old,r['bank'],r['bank']*5,r['ref'])[0])
static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static_positive=check_static_body(baseline,new,proposal['static_body_patch'])
native_path=D/'rin80_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior75_proof':str(prior_path.relative_to(ROOT)),'prior75_proof_sha256':sha(prior_path.read_bytes()),'prior75_art_displays_and_source_art_preserved':True,'cumulative_authored_refs':80,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':changed_raw,'display_changed_refs':[list(k)for k in targets],'changed_compositions':changed_parts,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_and_bank_boundaries_exact':True,'bank1_entire_graphics_exact':True,'new_gpu_boundary_alpha':0,'new_and_support_gpu_parts_checked':gpu_count,'static_references_exact_from75':static_count,'common_static_checker':static_positive,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'registration.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'registration.json').read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review_pending':True,'limitations':['New rear five references and prior75, not full art-unification completion or live gameplay verification.','No whole-body translation, old-head overlay, or generated-pose warping. Native glove-center differences are below0.6px; boot baseline preserved.','Partial VRAM42..49 raw/parts and entire bank1 preserved.']}
(D/'final80_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'sha':sha(new),'gpu_parts':gpu_count,'parts_changed':changed_parts}))
