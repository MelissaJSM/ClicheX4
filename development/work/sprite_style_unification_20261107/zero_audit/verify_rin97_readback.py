"""Independent low-level reader for Rin97: no producer/packer imported."""
from pathlib import Path
import sys,json,hashlib,collections,argparse,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from scripts.build_sprite_style_unification import check_static_body
sha=lambda b:hashlib.sha256(b).hexdigest();p=argparse.ArgumentParser();p.add_argument('--expected-sha256',required=True);args=p.parse_args()
prior_path=D/'final91_readback_audit.json';assert sha(prior_path.read_bytes())=='5baad4e637050faa9ed41dabf46d0932d2350eee08fe8501d8ee2f5d58b96e84';prior=json.loads(prior_path.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e'
P=D/'prepared_wall_followup_v2';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)==args.expected_sha256
ART=D/'wall_followup_registered_v2';meta=json.loads((ART/'registration.json').read_text('utf8'));assert sha((D/'wall_followup01/generated.png').read_bytes())==meta['source_generated_sha256']=='bf9d790730fe4b6041a18f8b17e3d4afdd80f635c437a3ffc8bc7745806e8e3f'
expected={34:'5f057fb3bce32cb93edcd69c073b3e845498b4d739a4978a8b23aa65a73dc2be',36:'17be78053f6c40a74fd6630a2390d0eb7bc22fa77dbb76f80f3d23f825da3e67',38:'5a40cc92b8c9bcc92c4af99052f6900f96bdbd3296dc7df1929cecd4f9de94ce',41:'bb98a83158a70e0b5121a1145af19ba32ced3014b8f6e8c0d76158547a3fdb6a'}
targets={};rows=[]
def polygon(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon(points,fill=1);return np.array(im,bool)
for r in meta['records']:
 n=r['ref'];path=ART/f'b0_{n:03}_indices.png';assert sha(path.read_bytes())==expected[n];z=np.array(Image.open(path));assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15
 sp=ROOT/r['source_native'];assert sha(sp.read_bytes())==r['source_native_sha256'];a=np.array(Image.open(sp));ix,iy=r['source_iris'];a[iy,ix]=15;hm=polygon(r['source_head_polygon']);dx,dy=r['source_head_delta'];ht=np.roll(np.roll(np.where(hm,a,0),dx,1),dy,0);moved=np.roll(np.roll(hm,dx,1),dy,0);result=a.copy();result[hm]=0;layers=[]
 for poly,delta in r['new_glove_translations']:
  gm=polygon(poly);gx,gy=delta;gt=np.roll(np.roll(np.where(gm,a,0),gx,1),gy,0);result[gm]=0;layers.append(gt)
 result[moved]=ht[moved]
 for gt in layers:result[gt>0]=gt[gt>0]
 if n==38:result[143:159,140:146]=a[143:159,140:146]
 assert np.array_equal(result,z);assert np.array_equal(z[166:],a[166:])
 for ref in([41,42,43]if n==41 else[n]):
  assert np.array_equal(render(old,0,0,ref)[0],render(old,0,0,n)[0]);targets[0,ref]=z;rows.append({'bank':0,'ref':ref,'master':n,'path':str(path.relative_to(ROOT)),'sha256':expected[n]})
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert t==nt and replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
count=collections.Counter();changed_raw=[];changed_parts=[];gpu_count=0
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert nf['index']==n;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;assert f['tile_count']==nf['tile_count']<=32;count['raw']+=1
  if raw!=nr:changed_raw.append([b,n])
  if key not in targets:assert raw==nr;count['non_target_raw_exact']+=1
  cp,ncp=composition_frame(c,b*5,n),composition_frame(nc,b*5,n);fields=lambda q:[{k:v for k,v in x.items()if k!='record_offset'}for x in q['parts']]
  if fields(cp)!=fields(ncp):assert key in targets;changed_parts.append([b,n])
  assert len(cp['parts'])==len(ncp['parts'])
  for op,np_ in zip(cp['parts'],ncp['parts']):
   for k in op:
    if k not in('record_offset','x','y','tile'):assert op[k]==np_[k],(b,n,k)
  if b==1 and 42<=n<=49:assert raw==nr and fields(cp)==fields(ncp);count['partial8_raw_parts_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];count['display']+=1
  if key in targets:assert np.array_equal(z,targets[key])and not np.array_equal(a,z);count['new_authored_exact']+=1
  else:assert np.array_equal(a,z);count['other_display_exact']+=1
  if key in targets:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for q in ncp['parts']:
    tile=q['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0)),(b,n,tile)
    if q['flip_y']and tile//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0)),(b,n,tile)
    gpu_count+=1
   if n==36:
    used={q['tile']for q in ncp['parts']};assert 0 not in used
    for tile in set(range(f['tile_count']))-used:
     y,x=tile//16*16,tile%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16])
assert count=={'raw':444,'non_target_raw_exact':438,'display':436,'other_display_exact':430,'partial8_raw_parts_exact':8,'new_authored_exact':6}
frames=graphics_bank(ng,0)['frames'];assert len({frames[n]['offset']for n in(41,42,43)})==1
cp42=composition_frame(nc,0,42)['parts'];assert {k:v for k,v in cp42[-1].items()if k not in('record_offset','index')}=={k:v for k,v in cp42[-2].items()if k not in('record_offset','index')}
static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static_positive=check_static_body(baseline,new,proposal['static_body_patch'])
native_path=D/'rin97_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior91_proof':str(prior_path.relative_to(ROOT)),'prior91_proof_sha256':sha(prior_path.read_bytes()),'prior91_art_displays_preserved':True,'cumulative_authored_refs':97,'incremental_authored_body_keys':4,'exact_alias_expansion_refs':2,'producer_functions_called':False,'incremental_counts':dict(count),'raw_changed_refs':changed_raw,'display_changed_refs':[list(k)for k in targets],'changed_compositions':changed_parts,'palette_audio_static_texture_other_entries_exact':True,'tile_counts_part_counts_and_bank_boundaries_exact':True,'bank1_entire_graphics_exact':True,'new_gpu_boundary_alpha':0,'new_gpu_parts_checked':gpu_count,'static_references_exact_from91':static_count,'common_static_checker':static_positive,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'native_cumulative_GPU_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rows':rows,'registered_art_metadata':str((ART/'registration.json').relative_to(ROOT)),'registered_art_metadata_sha256':sha((ART/'registration.json').read_bytes()),'new_head_and_glove_source_registration_independently_reconstructed':True,'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review_pending':True,'limitations':['새4키와 실제 표시가 같은2참조의 작업ARC 검사이다. 전체 미술 통일 또는 실기완료가 아니다.','눈·손과 바닥 정합은 별도 미술검토 대상이며 기존 타이밍·판정은 변경하지 않았다.','부분VRAM8과 모든 보조효과는 이전91을 보존한다.']}
(D/'final97_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'sha':sha(new),'gpu_parts':gpu_count}))
