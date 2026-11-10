"""Separate reader: frozen50 chain + new two-body art + static ownership."""
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
prior_report=D/'final50_readback_audit.json';assert sha(prior_report.read_bytes())=='b305ca775d80b5b55c837a151050e98210ae6bc02a0b11c6f7214ebe5874cd0f';prior=json.loads(prior_report.read_text('utf8'));assert prior['passed']
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256'];baseline=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='3536c3773f3a1a8da48e948b64c556986d2b3a51c7592baf4930b07b837b198d'
P=D/'prepared_burst_pair_final_v1';new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
for r in prior['rows']:assert sha((ROOT/r['path']).read_bytes())==r['sha256']
art=D/'burst_variant185_01';registered=art/'native/b1_185_indices.png';assert sha(registered.read_bytes())=='85871ee3c0804c886b6ea80134e949a97f5bc23edb9dc7c411b8c7246d96ac21';assert sha((art/'generated.png').read_bytes())=='519584a9898e388798652ad5bdf95f205d0720324dfc5dedbdad68a0fa0808f4'
target=np.array(Image.open(registered));assert target.shape==(384,384)and target.dtype==np.uint8 and target.max()<=15
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert c==nc;assert replace_entry(replace_entry(new,2,g),0x10206,t)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
count=collections.Counter();new_refs={(1,184),(1,185)};gpu_count=0
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;assert f['tile_count']==nf['tile_count']<=32;count['raw']+=1
  if key not in new_refs:assert raw==nr;count['other_raw_exact']+=1
  if b==1 and 42<=n<=49:assert raw==nr;count['partial8_raw_parts_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];count['display']+=1
  if key in new_refs:
   assert np.array_equal(z,target);count['new_authored_exact']+=1;assert not np.array_equal(a,z)
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in composition_frame(c,b*5,n)['parts']:
    tile=p['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert np.array_equal(aa[y:y+16,x],zz[y:y+16,x])
    if p['flip_y']and tile//16%16==0:assert np.array_equal(aa[y,x:x+16],zz[y,x:x+16])
    gpu_count+=1
  else:assert np.array_equal(a,z);count['other_display_exact']+=1
assert count=={'raw':444,'other_raw_exact':442,'display':436,'other_display_exact':434,'partial8_raw_parts_exact':8,'new_authored_exact':2}
assert graphics_bank(ng,1)['frames'][184]['offset']==graphics_bank(ng,1)['frames'][185]['offset']
for r in prior['rows']:
 assert np.array_equal(render(new,r['bank'],r['bank']*5,r['ref'])[0],render(old,r['bank'],r['bank']*5,r['ref'])[0])
bt=entry(baseline,0x10206);recipe=json.loads((P/'static_effects.json').read_text('utf8'));assert recipe['source_texture_sha256']==sha(bt)and recipe['parts_sha256']==sha(nc)and recipe['modified_texture_sha256']==sha(nt)
static_count=0;users_baseline=[];users_previous=[]
diffsets=[{(i,s)for i,(a,b)in enumerate(zip(src,nt))for s in(0,4)if(a>>s&15)!=(b>>s&15)}for src in(bt,t)]
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):
  used=set();static_count+=1
  for p in composition_frame(c,b,n)['parts']:
   tile=p['page']*256+p['tile']
   for y in range(16):
    for x in range(16):used.add(((tile//16*16+y)*128+tile%16*8+x//2,(x%2)*4))
  if used&diffsets[0]:users_baseline.append([b,n])
  if used&diffsets[1]:users_previous.append([b,n])
assert users_baseline==[[6,23],[6,24]]==recipe['expected_changed_references'];assert users_previous==[[6,23]]
vanilla_path=ROOT/'MegaMan X4.bin';assert sha(vanilla_path.read_bytes())=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b';vanilla=read_disc(vanilla_path,('PL01_U.ARC',))[0]['PL01_U.ARC'];ot=entry(vanilla,0x10206);zero=np.roll(render(vanilla,1,5,182)[0],-1,axis=0)
hist=json.loads((ROOT/'work/ver_rin_nana/style_revision/v4_special/static_burst/static_effects.json').read_text('utf8'));static_rows=[]
for n,body in[(23,185),(24,182)]:
 cp=composition_frame(nc,6,n);data,size,bb,locs=compose_static(ot,cp);v=np.frombuffer(data,np.uint8).reshape(size[1],size[0]);a=np.frombuffer(compose_static(t,cp)[0],np.uint8).reshape(v.shape);z=np.frombuffer(compose_static(nt,cp)[0],np.uint8).reshape(v.shape)
 freq=collections.Counter(q for qs in locs for q in qs);unique=np.array([len(qs)==1 and freq[qs[0]]==1 for qs in locs]).reshape(v.shape);x0,y0,x1,y1=[160+i for i in bb]
 rm=(zero[y0:y1,x0:x1]>0)&(v>0);rm[:max(0,-17-bb[1])]=False;bg=v.copy()
 for y,x in zip(*np.nonzero(rm)):
  mx=-12-x-2*bb[0]
  if 0<=mx<size[0]and not rm[y,mx]and v[y,mx]:bg[y,x]=v[y,mx]
  else:
   available=[xx for xx in range(size[0])if not rm[y,xx]and v[y,xx]]
   bg[y,x]=0 if not available else 13 if n==24 and any(v[y,xx]==13 for xx in available)else v[y,min(available,key=lambda xx:(abs(xx-x),xx))]
 remap=np.array(hist['frames'][str(n)]['tint_map'],np.uint8);masks=[]
 for blob,actual in[(old,a),(new,z)]:
  model=render(blob,1,5,body)[0][y0:y1,x0:x1];mask=(model>0)&(v>0)&unique;expect=bg.copy();expect[mask]=remap[model[mask]];assert np.array_equal(expect,actual);masks.append(mask)
 assert np.array_equal(a>0,z>0)and np.array_equal(a[~(masks[0]|masks[1])],z[~(masks[0]|masks[1])])
 rr=recipe['frames'][str(n)];png=P/rr['file'];assert sha(png.read_bytes())==rr['sha256']and np.array_equal(np.array(Image.open(png)),z)
 static_rows.append({'ref':n,'body':body,'changed_pixels_from50':int(np.count_nonzero(a!=z)),'before_and_after_reconstruction_exact':True,'entire_alpha_and_outside_body_exact':True})
assert static_rows[0]['changed_pixels_from50']==483 and static_rows[1]['changed_pixels_from50']==0
proposal=json.loads((P/'proposal.json').read_text('utf8'));static_positive=check_static_body(baseline,new,proposal['static_body_patch'])
native_path=D/'rin52_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'candidate_sha256':sha(new),'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':prior['source_bin_sha256'],'prior50_proof':str(prior_report.relative_to(ROOT)),'prior50_proof_sha256':sha(prior_report.read_bytes()),'prior50_art_png_hashes_and_displays_preserved':True,'cumulative_authored_refs':52,'producer_functions_called':False,'incremental_counts':dict(count),'entire_composition_palette_audio_other_entries_exact':True,'tile_counts_and_bank_boundaries_exact':True,'new_gpu_boundary_alpha':0,'new_refs_gpu_parts_checked':gpu_count,'shared184_185_preserved':True,'source_art_sha256':sha((art/'generated.png').read_bytes()),'registered_png_sha256':sha(registered.read_bytes()),'static_rows':static_rows,'static_references_checked':static_count,'static_users_from_baseline':users_baseline,'static_users_from50':users_previous,'common_static_checker':static_positive,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'visual_review':['burst_variant185_01/normal_sequence_comparison.png','prepared_burst_pair_main_v1/normal_readback_00.png','prepared_burst_pair_main_v1/black_readback_00.png','prepared_burst_pair_final_v1/effect_comparison.png'],'limitations':['52참조 누적 작업자료이며 전동작 미술 완료 또는 실제 플레이 통과가 아니다.','부분42..49는 원래 raw/조립을 보존하며 모든 직전 업로드 전이를 실제 게임에서 재현한 것은 아니다.']}
(D/'final52_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'candidate':sha(new),'static':static_rows}))
