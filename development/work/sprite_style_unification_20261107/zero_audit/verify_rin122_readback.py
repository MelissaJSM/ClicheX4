"""Read the packed output independently; do not call the production packer."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ground_first_v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
priorpath=D/'final117_readback_audit.json';prior=json.loads(priorpath.read_text('utf8'))
assert prior['passed'] and prior['cumulative_authored_refs']==117
old=(ROOT/prior['candidate']).read_bytes();assert sha(old)==prior['candidate_sha256']=='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1'
source=ROOT/prior['source_bin'];assert sha(source.read_bytes())==prior['source_bin_sha256']
assets=read_disc(source,('PL01_U.ARC','SLUS_005.61'))[0];baseline=assets['PL01_U.ARC'];assert sha(baseline)==prior['source_arc_sha256']
ART=D/'ground_registered_v1';meta=json.loads((ART/'registration.json').read_text('utf8'))
assert meta['source_arc_sha256']==sha(old)
assert sha((D/'ground_first01/generated.png').read_bytes())==meta['generated_sha256']=='ac417d1d1295943ad845f4b53f5719fca0a0096cb0cfba53afeb1bf376e2af10'
hashes={62:'153ca50a1a464059b0eff9acfacd07542d98b41f35e438b197e215101dcb7104',63:'3ccfa2608c8d906a5d783d944946f3cebfca021e98f2fe62b8f30a8ac1596996',65:'fd0d84c9a33696849d837e9d30464c3b5f036dbea68ac2906a2446b06f1f1725',67:'a423a72784dc2e2a3ca85237129be55124ecc1214367ce49a61e0f744fbc7bec'}
def polygon(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon(points,fill=1);return np.array(im,bool)
targets={};provenance=[]
for r in meta['records']:
 n=int(r['key'][3:]);p=ART/f'b0_{n:03}_indices.png';assert sha(p.read_bytes())==hashes[n]==r['output_sha256']
 s=ROOT/r['native_source'];assert sha(s.read_bytes())==r['native_source_sha256']
 a=np.array(Image.open(s));assert a.shape==(384,384) and a.dtype==np.uint8 and a.max()<16
 for op in r['operations']:
  if 'whole_art_translation' in op:
   dx,dy=op['whole_art_translation'];a=np.roll(a,(dy,dx),(0,1))
  else:
   protect=polygon(op['protected_polygon']) if op['protected_polygon'] else np.zeros_like(a,bool)
   mask=polygon(op['polygon'])&~protect;dx,dy=op['translate'];out=a.copy();out[mask]=0
   moved=np.roll(mask,(dy,dx),(0,1))&~protect;pixels=np.roll(a,(dy,dx),(0,1));out[moved]=pixels[moved];out[protect]=a[protect];a=out
 target=np.array(Image.open(p));assert np.array_equal(a,target)
 assert not r['old_body_or_head_override'] and not r['new_color_drawn']
 targets[n]=target;provenance.append({'ref':n,'path':rel(p),'sha256':sha(p.read_bytes()),'source_art_registration_reconstructed':True})
assert np.array_equal(render(old,0,0,67)[0],render(old,0,0,69)[0]);targets[69]=targets[67]
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
assert replace_entry(replace_entry(new,2,g),3,c)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(c)==bank_offsets(nc)
support={61,64,66,68,70};counts=collections.Counter();changed_raw=[];changed_parts=[];gpu=0
sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y']) for p in cp['parts']]
raw_cache={}
for b in (0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 assert len(ob['frames'])==len(nb['frames'])
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for of,nf in zip(ob['frames'],nb['frames']):
  n=of['index'];selected=b==0 and n in targets;shared=b==0 and n in support
  assert of['tile_count']==nf['tile_count']<=32
  raw=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
  nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  if raw!=nr:assert selected or shared;changed_raw.append([b,n])
  else:counts['raw_exact']+=1
  cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
  assert len(cp['parts'])==len(np_['parts'])
  if sem(cp)!=sem(np_):assert b==0 and n in (62,63,69);changed_parts.append(n)
  for p,q in zip(cp['parts'],np_['parts']):assert p['flags']==q['flags']
  if b==1 and 42<=n<=49:assert raw==nr and sem(cp)==sem(np_);counts['partial8_exact']+=1;continue
  a,z=render(old,b,b*5,n)[0],render(new,b,b*5,n)[0];counts['display']+=1
  if selected:assert np.array_equal(z,targets[n]) and not np.array_equal(a,z);counts['target_display_exact']+=1
  else:assert np.array_equal(a,z);counts['non_target_display_exact']+=1
  if selected or shared:
   aa=np.frombuffer(indexed_atlas(raw,of['tile_count'])[0],np.uint8).reshape(-1,256)
   zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256);raw_cache[n]=(aa,zz)
   for p in np_['parts']:
    t=p['tile'];y,x=t//16*16,t%16*16
    if t%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0))
    if p['flip_y'] and t//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0))
    gpu+=1
assert counts=={'raw':444,'raw_exact':434,'display':436,'target_display_exact':5,'non_target_display_exact':431,'partial8_exact':8},counts
assert changed_parts==[62,63,69]
# Both refined body61 and the original saber64 own unchanged tiles outside9..27.
aa,zz=raw_cache[61];kept=[]
for t in list(range(9))+list(range(28,32)):
 y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]);kept.append(t)
assert not np.any(zz[16:32,0])
assert len({graphics_bank(ng,0)['frames'][n]['offset'] for n in(61,62,63,64)})==1
effect_tiles=[]
for n in (64,66,68,70):
 aa,zz=raw_cache[n]
 for t in sorted({p['tile'] for p in composition_frame(c,0,n)['parts']}):
  y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]);effect_tiles.append([n,t])
static_count=0
for b in (1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):
  assert composition_frame(c,b,n)['parts']==composition_frame(nc,b,n)['parts'];static_count+=1
assert static_count==404
for name in('palette.bin','effect_23.png','effect_24.png'):assert(P/name).read_bytes()==(ROOT/prior['candidate']).parent.joinpath(name).read_bytes()
proposal=json.loads((P/'proposal.json').read_text('utf8'));static=check_static_body(baseline,new,proposal['static_body_patch'])
nativepath=D/'rin122_components_native_checks.json';native=json.loads(nativepath.read_text('utf8'));assert native['passed'] and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
timeline=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json').read_text('utf8'))
seq={a['id']:a for a in timeline['animations'] if a['id']in(88,112)}
for anim in seq.values():
 for s in anim['steps']:
  offset=int(s['address'],16)-0x80010000+0x800;assert assets['SLUS_005.61'][offset:offset+4]==bytes.fromhex(s['bytes'])
report={'passed':True,'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':sha(new),'source_bin':rel(source),'source_bin_sha256':prior['source_bin_sha256'],'source_arc_sha256':sha(baseline),'prior117_proof':rel(priorpath),'prior117_proof_sha256':sha(priorpath.read_bytes()),'previous117_preserved':True,'cumulative_authored_refs':122,'incremental_body_masters':4,'incremental_exact_aliases':1,'incremental_counts':dict(counts),'producer_functions_called':False,'body_master_provenance':provenance,'raw_changed_refs':changed_raw,'changed_compositions':changed_parts,'joint62_63_original_pool':list(range(9,28)),'joint61_64_entire_tiles_exact':kept,'original_saber_entire_tiles_exact':effect_tiles,'new_gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'static_references_preserved':404,'common_static_checker':static,'native_proof':rel(nativepath),'native_proof_sha256':sha(nativepath.read_bytes()),'palette_audio_other_entries_exact':True,'bank1_entire_graphics_exact':True,'part_tile_count_and_bank_bounds_preserved':True,'timelines':seq,'timeline_actual_EXE_bytes_checked':True,'user_accepted':False,'runtime_verified':False,'root_review_only':True,'limitations':['실제 게임 검증이 아니다. 첫타 후반71..82 등은 다음 미술 수정 대상이다.','8개 부분VRAM 참조는 원자료 전체를 보존했고 독립 완성 그림으로 복원했다고 주장하지 않는다.','검기는 원래 조립·타일·팔레트 그대로다. 동일 원점 합성은 접점 검토용이며 외부 무기 객체의 런타임 이동/가림까지 재현하지 않는다.']}
dump(D/'final122_readback_audit.json',report)
print(json.dumps({'passed':True,'sha':sha(new),'counts':dict(counts),'gpu_parts':gpu,'effect_tiles':len(effect_tiles)}))
