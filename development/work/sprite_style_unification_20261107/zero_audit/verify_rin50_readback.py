"""Independent cumulative50/native-static audit. No producer functions called."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_static_effect import compose_static
sha=lambda b:hashlib.sha256(b).hexdigest()
source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';assert sha(source.read_bytes())=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
old=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(old)=='e6dbffce1b3f3fa4842c4092c6a4de09109db1bd5569864d4959cb7ec92849e2'
P=D/'prepared_priority_final_v2/PL01_U.ARC';new=P.read_bytes();assert sha(new)=='3536c3773f3a1a8da48e948b64c556986d2b3a51c7592baf4930b07b837b198d'
paths={};manifest_proof=[]
for f in json.loads((D/'run_art_sources_v1.json').read_text('utf8'))['frames']:paths[0,f['ref']]=ROOT/f['path']
for n in(21,27,35,39,40):paths[0,n]=D/f'air_wall_head_candidate_v4/b0_{39 if n==40 else n:03}_indices.png'
for n in(22,23,24,25,26):paths[0,n]=D/f'air_continuation_registered_v2/b0_{22 if n==23 else n:03}_indices.png'
for n,s in{44:44,46:46,47:46,48:46,50:50,51:51,52:51}.items():paths[0,n]=D/f'dash_continuation01/native/b0_{s:03}_indices.png'
for n,s in{28:28,29:29,30:29,31:31,32:31,33:33}.items():paths[0,n]=D/f'air_continuation02/native/b0_{s:03}_indices.png'
assert len(paths)==42
for name in('run_art_sources_v1','air_wall_sources_v3','air_continuation_sources_v1','dash_sources_v1','air_continuation2_sources_v1'):
 p=D/(name+'.json');j=json.loads(p.read_text('utf8'));items=j.get('inputs',[])+j.get('frames',[])+j.get('generated_sources',[])
 for f in items:assert sha((ROOT/f['path']).read_bytes())==f['sha256']
 manifest_proof.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes()),'files':len(items)})
A=D/'detail_priority_singles';j=json.loads((A/'registered_v2/registration.json').read_text('utf8'))
for f in j['frames']:
 assert sha((ROOT/f['source']).read_bytes())==f['source_sha256'];assert sha((ROOT/f['target']).read_bytes())==f['target_sha256'];assert sha((A/f['key']/'inputs.json').read_bytes())==f['input_meta_sha256']
 # v2 only restores cyan cells evidenced in the new image; no old head is pasted.
 raw=np.array(Image.open(A/f['key']/'native'/f"{f['key']}_indices.png"));expect=raw.copy()
 for eye in f['eye_registration']:expect[eye['y'],eye['x']]=eye['after']
 assert np.array_equal(expect,np.array(Image.open(ROOT/f['target'])))
j=json.loads((A/'registered_v3/registration.json').read_text('utf8'))
for f in j['records']:
 before=ROOT/f['parent'];after=ROOT/f['target'];assert sha(before.read_bytes())==f['parent_sha256'];assert sha(after.read_bytes())==f['target_sha256'];a=np.array(Image.open(before));mask=np.zeros_like(a,bool)
 for x0,y0,x1,y1 in f['edit_rects']:mask[y0:y1,x0:x1]=True
 for x0,y0,x1,y1 in f['protected_contact_rects']:mask[y0:y1,x0:x1]=False
 expected=a.copy()
 if f['generated']:
  assert sha((ROOT/f['generated']).read_bytes())==f['generated_sha256'];assert sha((ROOT/f['registered_source']).read_bytes())==f['registered_source_sha256'];repaint=np.array(Image.open(ROOT/f['registered_source']));expected[mask]=repaint[mask]
 assert np.array_equal(expected,np.array(Image.open(after)))
j=json.loads((A/'registered_v4/registration.json').read_text('utf8'));p=A/'registered_v3/b1_005_indices.png';q=A/'registered_v4/b1_005_indices.png';npng=A/'victory_leg_fix02/native/b1_005_indices.png'
assert sha(p.read_bytes())==j['edit_parent_sha256']and sha(q.read_bytes())==j['target_sha256']and sha(npng.read_bytes())==j['native_source_sha256'];assert sha((A/'victory_leg_fix02/generated.png').read_bytes())==j['generated_sha256']
expect=np.array(Image.open(p));a=np.array(Image.open(npng));x0,y0,x1,y1=j['edit_rect'];expect[y0:y1,x0:x1]=a[y0:y1,x0:x1];assert np.array_equal(expect,np.array(Image.open(q)))
for key in('b0_061','b0_174','b1_183'):assert(A/'registered_v4'/f'{key}_indices.png').read_bytes()==(A/'registered_v3'/f'{key}_indices.png').read_bytes()
for b,n,k in[(0,61,'b0_061'),(0,174,'b0_174'),(0,175,'b0_174'),(0,176,'b0_174'),(0,177,'b0_174'),(1,5,'b1_005'),(1,182,'b1_183'),(1,183,'b1_183')]:paths[b,n]=A/'registered_v4'/f'{k}_indices.png'
targets={}
for key,p in paths.items():
 a=np.array(Image.open(p))
 if key in((0,176),(0,177)):
  y,x=np.nonzero(a);z=np.zeros_like(a);z[y,319-x]=a[y,x];a=z
 targets[key]=a
assert len(targets)==50
support={(0,62),(0,63),(0,64),(1,6)};g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert replace_entry(replace_entry(replace_entry(new,2,g),3,c),0x10206,t)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc)
def semantics(c,b,n):return[(p['flags'],p['tile'],p['x'],p['y'])for p in composition_frame(c,b,n)['parts']]
count=collections.Counter();rows=[]
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nraw=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;count['raw']+=1;assert nf['tile_count']<=32
  if key not in targets:assert semantics(c,b*5,n)==semantics(nc,b*5,n);count['non_target_parts_exact']+=1
  if key not in targets and key not in support:assert raw==nraw and f['tile_count']==nf['tile_count'];count['non_target_raw_exact']+=1
  if raw!=nraw:
   count['raw_changed_refs']+=1;aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nraw,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for ppart in composition_frame(nc,b*5,n)['parts']:
    tile=ppart['tile'];y,x=tile//16*16,tile%16*16
    if tile%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]>0))
    if ppart['flip_y']and tile//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]>0))
  if b==1 and 42<=n<=49:assert raw==nraw;count['partial_raw_parts_exact']+=1;continue
  a=render(old,b,b*5,n)[0];z=render(new,b,b*5,n)[0];count['display']+=1;assert np.array_equal(z,targets.get(key,a))
  if key in targets:count['authored_target_exact']+=1;rows.append({'bank':b,'ref':n,'path':str(paths[key].relative_to(ROOT)),'sha256':sha(paths[key].read_bytes()),'mirror':key in((0,176),(0,177)),'changed_pixels':int(np.count_nonzero(a!=z))})
  else:count['non_target_display_exact']+=1
  if key in support:count['shared_support_display_exact']+=1
assert count['raw']==444 and count['display']==436 and count['authored_target_exact']==50 and count['non_target_display_exact']==386 and count['non_target_raw_exact']==390 and count['shared_support_display_exact']==4
for n in(0,1,2,146,147,148):assert np.array_equal(render(old,0,0,n)[0],render(new,0,0,n)[0])
# Static atlas: independent address ownership, unchanged23 and new182 body24.
recipe_path=P.parent/'static_effects.json';recipe=json.loads(recipe_path.read_text('utf8'));assert recipe['parts_sha256']==sha(nc)and recipe['modified_texture_sha256']==sha(nt)and recipe['source_texture_sha256']==sha(t)
modified={(i,s)for i,(a,b)in enumerate(zip(t,nt))for s in(0,4)if(a>>s&15)!=(b>>s&15)};users=[];static_count=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):
  assert semantics(c,b,n)==semantics(nc,b,n);used=set();static_count+=1
  for p in composition_frame(c,b,n)['parts']:
   tile=p['page']*256+p['tile']
   for y in range(16):
    for x in range(16):used.add(((tile//16*16+y)*128+tile%16*8+x//2,(x%2)*4))
  if used&modified:users.append([b,n])
assert users==[[6,24]]==recipe['expected_changed_references']
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
 rr=recipe['frames'][str(n)];png=recipe_path.parent/rr['file'];assert sha(png.read_bytes())==rr['sha256']and np.array_equal(np.array(Image.open(png)),z)
 static_rows.append({'ref':n,'body':body,'changed_pixels':int(np.count_nonzero(a!=z)),'before_and_after_reconstruction_exact':True,'entire_alpha_and_outside_body_exact':True})
assert static_rows[0]['changed_pixels']==0
native_path=D/'rin50_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':sha(source.read_bytes()),'source_arc_sha256':sha(old),'candidate':str(P.relative_to(ROOT)),'candidate_sha256':sha(new),'producer_functions_called':False,'counts':dict(count),'rows':rows,'art_manifests':manifest_proof,'new_four_art_local_edit_provenance_exact':True,'static_rows':static_rows,'static_references_checked':static_count,'changed_static_users':users,'static_recipe_sha256':sha(recipe_path.read_bytes()),'palette_audio_other_entries_exact':True,'idle6_exact':True,'new_gpu_boundary_alpha':0,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'root_review_only':True,'user_accepted':False,'runtime_verified':False,'limitations':['새 사다리 174..177만 이번에 개선했다. 다른 사다리 단계·승리 이웃·낙봉파185/184는 후속 검토 대상이다.','부분42..49 raw/조립을 보존하지만 모든 직전 업로드와 외부 상태를 실제 게임에서 검사하지 않았다.','누적50참조 등록이며 모든 동작의 미술 통일이 끝났다는 뜻이 아니다.'],'visual_review':{'actually_viewed':['prepared_priority_body_v1/normal_readback_00.png','prepared_priority_body_v1/normal_readback_01.png','prepared_priority_body_v1/black_readback_00.png','prepared_priority_body_v1/black_readback_01.png','prepared_priority_victory_v1/normal_readback_00.png','prepared_priority_victory_v1/black_readback_00.png','prepared_priority_final_v2/effect_comparison.png'],'finding':'새 머릿결·소매·앞치마 주름을 확인했다. 국소 체형 보완으로61 허리와183 앞팔,5 지지다리가 두꺼워졌고 머리·손·발 위치는 국소 보완 전 아트를 보존한다. 사다리 좌우와 낙봉파24에서 새 잘림은 보이지 않는다.'}}
(D/'final50_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'static_rows':static_rows,'candidate':sha(new)}))
