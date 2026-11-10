"""Independent decoder/readback; deliberately imports no art producer or packer."""
from pathlib import Path
import sys,json,hashlib,collections,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_static_effect import compose_static
from scripts.build_sprite_style_unification import check_static_body
sha=lambda b:hashlib.sha256(b).hexdigest()
prior_path=D/'final52_readback_audit.json';assert sha(prior_path.read_bytes())=='b9e5197587079b51ca3d85a3a71934c6940e5e922eaa39e4f878f03ae7f02049';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
prior50_path=ROOT/prior['prior50_proof'];assert sha(prior50_path.read_bytes())==prior['prior50_proof_sha256'];prior50=json.loads(prior50_path.read_text('utf8'));assert prior50['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior50['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
P=D/'prepared_third_saber_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='11d4c88a17983dd3e106d13af3938075803186c59045b0b372b0f813b3aa09ae'
ART=D/'third_saber_registered_v2'
expected={109:'bec5ba4131dc13d96bb66854f71a6af915558bf28b77b545126392cd81779b0e',111:'da5a10d2cb51f3553a842160c5f62f378fc7c885a67a6dfdb16ac898c9e62e35',113:'d19469a045f71fe1490077fb9549262a2843ddbfcc0c9d5f8a31a0328111de58',115:'b7d06ea7594704adcf816b0e49df34f5e0cb56554ccee2277715163f74cb6a43',121:'3391032a953156736b5481eb010f92d532911561ee2e401a8ec0d58b496a3f0d'}
groups={109:[109],111:[111],113:[113],115:[115,117,119],121:[121,123,125,127]}
targets={};rows=[]
for master,refs in groups.items():
 path=ART/f'b0_{master:03}_indices.png';assert sha(path.read_bytes())==expected[master];im=Image.open(path);a=np.array(im);assert im.mode in('L','P')and a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15
 for n in refs:targets[0,n]=a;assert np.array_equal(render(old,0,0,n)[0],render(old,0,0,master)[0]);rows.append({'bank':0,'ref':n,'master':master,'path':str(path.relative_to(ROOT)),'sha256':expected[master]})
for name,h in [('third_saber01','5254b64368f1b6f7aae3fb7569180d805c72dd58520d0e4ef86052a559e2ca66'),('third_saber121_01','6995d888a9e666e1dea2536932a0a29b8ae10db2b9858bdb662b283ec3ff4081')]:assert sha((D/name/'generated.png').read_bytes())==h
registration=json.loads((ART/'registration.json').read_text('utf8'))
for r in registration['records']:assert sha((ROOT/r['generated']).read_bytes())==r['generated_sha256']and r['after_sha256']==expected[int(r['key'][3:])]
for r in prior50['rows']:assert sha((ROOT/r['path']).read_bytes())==r['sha256']
assert sha((D/'burst_variant185_01/native/b1_185_indices.png').read_bytes())==prior['registered_png_sha256']
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert t==nt and replace_entry(replace_entry(new,2,g),3,c)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
support={(0,n)for n in [110,112,114,116,118,120,122,124,126,128,129]};owned=set(targets)|support
count=collections.Counter();changed_raw=[];changed_parts=[];gpu_count=0
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert nf['index']==n;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;assert f['tile_count']==nf['tile_count']<=32;count['raw']+=1
  if raw!=nr:changed_raw.append([b,n])
  if key not in owned:assert raw==nr;count['non_owned_raw_exact']+=1
  cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
  fields=lambda q:[{k:v for k,v in p.items()if k!='record_offset'}for p in q['parts']]
  if fields(cp)!=fields(np_):changed_parts.append([b,n]);assert key in targets and n in(109,115,117,119)
  assert len(cp['parts'])==len(np_['parts'])
  for p,q in zip(cp['parts'],np_['parts']):
   for k in p:
    if k not in('record_offset','x','y'):assert p[k]==q[k],(b,n,k)
  if b==1 and 42<=n<=49:assert raw==nr and fields(cp)==fields(np_);count['partial8_raw_parts_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];count['display']+=1
  if key in targets:
   assert np.array_equal(z,targets[key])and not np.array_equal(a,z);count['new_authored_exact']+=1
  else:assert np.array_equal(a,z);count['other_display_exact']+=1
  if key in support:count['shared_effects_exact']+=1
  if key in owned:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in np_['parts']:
    tile=p['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0)),(b,n,tile)
    if p['flip_y']and tile//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0)),(b,n,tile)
    gpu_count+=1
assert count=={'raw':444,'non_owned_raw_exact':423,'display':436,'other_display_exact':426,'partial8_raw_parts_exact':8,'new_authored_exact':10,'shared_effects_exact':11}
assert changed_parts==[[0,n]for n in(109,115,117,119)]
for r in prior50['rows']:assert np.array_equal(render(new,r['bank'],r['bank']*5,r['ref'])[0],render(old,r['bank'],r['bank']*5,r['ref'])[0])
for n in(184,185):assert np.array_equal(render(new,1,5,n)[0],render(old,1,5,n)[0])
static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):
  cp,np_=composition_frame(c,b,n),composition_frame(nc,b,n);assert cp['parts']==np_['parts'];static_count+=1
recipe=json.loads((P/'static_effects.json').read_text('utf8'));assert recipe['source_texture_sha256']==sha(entry(baseline,0x10206))and recipe['parts_sha256']==sha(nc)and recipe['modified_texture_sha256']==sha(nt)
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
binding={'recipe':str((P/'static_effects.json').relative_to(ROOT)),'sha256':sha((P/'static_effects.json').read_bytes())};static_positive=check_static_body(baseline,new,binding)
native_path=D/'rin62_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior52_proof':str(prior_path.relative_to(ROOT)),'prior52_proof_sha256':sha(prior_path.read_bytes()),'prior52_art_displays_and_source_art_preserved':True,'cumulative_authored_refs':62,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':changed_raw,'display_changed_refs':[list(k)for k in targets],'changed_compositions':changed_parts,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_and_bank_boundaries_exact':True,'new_gpu_boundary_alpha':0,'new_and_support_gpu_parts_checked':gpu_count,'static_references_exact_from52':static_count,'common_static_checker':static_positive,'static_binding':binding,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'registration.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'registration.json').read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review':[str((P/f'{form}_readback_{n:02}.png').relative_to(ROOT))for form in('normal','black')for n in range(3)],'limitations':['새 3타 몸체 10참조와 기존 52참조의 누적 작업이다. 전 동작 미술 통일 완료나 실제 플레이 검증을 뜻하지 않는다.','게임 원점·타이밍·검기 그림은 유지되지만 새 원화의 손·발 윤곽이 원래 모든 픽셀과 같지는 않다. 실제 동작과 검기 접점은 실기 확인이 남는다.','부분 VRAM 42..49는 원래 raw/조립을 보존했다. 모든 직전 업로드 이력을 게임에서 재현한 검사는 아니다.']}
(D/'final62_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'candidate':sha(new),'static_count':static_count,'parts_changed':changed_parts,'gpu_parts':gpu_count}))
