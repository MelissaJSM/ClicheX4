"""Separate full ARC reader for Rin75. No producer/registration functions called."""
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
prior_path=D/'final62_readback_audit.json';assert sha(prior_path.read_bytes())=='77e85c9d125d0e3c9c8a228d3a672aed072b3b42928a202a089fc1ead2454b7d';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='11d4c88a17983dd3e106d13af3938075803186c59045b0b372b0f813b3aa09ae'
P=D/'prepared_rear_continuation_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)==args.expected_sha256
ART=D/'rear_registered_grips_v1';expected={178:'82d103d469676b701c187b7f1bc68a2180918f76bb9e7a75af720b028ef277ff',182:'cd76069916e1cb1fc6e8673d3fcc9a34ffc4b8e6b49405178f32cf3f1273fa70',186:'5c2df1fc2324e36abd8cddac48ea6bee43f7ddcfdb06105095441e021c7e9b88',190:'d18ec0f788307bb1898bad6d974551cf0f007a17a1d3e7145a4a77f799392a9a'}
groups={178:{178:False,179:False,180:True,181:True},182:{182:False,183:False,184:True,185:True},186:{186:False,188:False,187:True,189:True},190:{190:False}}
def mirror(a):
 r=np.zeros_like(a);y,x=np.nonzero(a);r[y,319-x]=a[y,x];return r
targets={};rows=[]
for master,refs in groups.items():
 path=ART/f'b0_{master:03}_indices.png';assert sha(path.read_bytes())==expected[master];a=np.array(Image.open(path));assert a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15
 for n,flipped in refs.items():
  original=render(old,0,0,master)[0];assert np.array_equal(render(old,0,0,n)[0],mirror(original)if flipped else original)
  targets[0,n]=mirror(a)if flipped else a;rows.append({'bank':0,'ref':n,'master':master,'mirror_x_319_minus_x':flipped,'path':str(path.relative_to(ROOT)),'sha256':expected[master]})
for folder,h in[('rear_continuation01','67f1a95bd572aaef9f0417828e77bb0e916c5ab44cdbd6e9891c8554d1b141dd'),('rear_leg_fix_186','b079b9f7220371ef15d0bc6c3473396df73f3d710fc1d8cd8b81a5a581a13089'),('rear_leg_fix_190','e83cd48ddd3facb5a6aa931225724954dabc4c311bcc1763b16c5562107bb195')]:assert sha((D/folder/'generated.png').read_bytes())==h
for row in prior['rows']:assert sha((ROOT/row['path']).read_bytes())==row['sha256']
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert t==nt and replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
support={(0,191)};owned=set(targets)|support;count=collections.Counter();changed_raw=[];changed_parts=[];gpu_count=0
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
  master=next((m for m,refs in groups.items() if n in refs),None)if b==0 else None
  if master is not None and master!=n:
   canonical=composition_frame(nc,0,master)
   assert len(canonical['parts'])==len(ncp['parts'])
   flipped=groups[master][n]
   for p,q in zip(canonical['parts'],ncp['parts']):
    want=dict(p);want.pop('record_offset');want['x']=-p['x']-16 if flipped else p['x']
    if flipped:want.update(flags=p['flags']^0x40,flip_x=not p['flip_x'])
    assert want=={k:v for k,v in q.items()if k!='record_offset'},(n,'canonical reflection')
  else:
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
assert count=={'raw':444,'non_owned_raw_exact':430,'display':436,'other_display_exact':423,'partial8_raw_parts_exact':8,'new_authored_exact':13,'shared_support_display_exact':1}
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
native_path=D/'rin75_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior62_proof':str(prior_path.relative_to(ROOT)),'prior62_proof_sha256':sha(prior_path.read_bytes()),'prior62_art_displays_and_source_art_preserved':True,'cumulative_authored_refs':75,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':changed_raw,'display_changed_refs':[list(k)for k in targets],'changed_compositions':changed_parts,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_and_bank_boundaries_exact':True,'bank1_entire_graphics_exact':True,'new_gpu_boundary_alpha':0,'new_and_support_gpu_parts_checked':gpu_count,'static_references_exact_from62':static_count,'common_static_checker':static_positive,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'registration.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'registration.json').read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review_pending':True,'limitations':['後면13참조와 이전62참조의 누적작업이며 모든동작의미술통일이나실기완료가 아니다.','190은 전체y-1등록을 취소하고 새부츠만 y-1로정합했다.178/182/186의새장갑과손목만원접점으로국소이동했다.','부분VRAM42..49의원래bank1raw·조립·전체은행은보존했다. 모든실제전이경로를게임에서검사한것은아니다.']}
(D/'final75_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'sha':sha(new),'gpu_parts':gpu_count,'parts_changed':changed_parts}))
