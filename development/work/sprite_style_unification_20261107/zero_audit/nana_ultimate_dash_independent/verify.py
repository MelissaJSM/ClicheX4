"""Read-only source-to-native audit; no Nana producer modules are imported."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas
O=Path(__file__).parent;D=O.parent.parent/'nana_audit/ultimate_dash_repaint';P=D/'packed_dash_candidate_v1';T=D/'joint_native_targets_v1';N=D/'nova_head_registered_v1'
sha=lambda x:hashlib.sha256(x).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
oldpath=D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';newpath=P/'PL02_U.ARC';old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'and sha(new)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
a,b=Archive(old),Archive(new);dash=set(range(67,85))|{93,94};nova={217,218,220};selected=dash|nova;PBS=(0,5,6,7,8);count=collections.Counter();targets={};sources=[]
meta=read(T/'manifest.json');assert meta['source_arc_sha256']==sha(old);rows={q['ref']:q for q in meta['frames']};assert set(rows)==dash
for n,q in rows.items():
 if n in(73,74):continue
 bp,ap=ROOT/q['before_source'],ROOT/q['after_source'];assert sha(bp.read_bytes())==q['before_source_sha256']and sha(ap.read_bytes())==q['after_source_sha256'];sources.extend([bp,ap])
 before,after=np.array(Image.open(bp)),np.array(Image.open(ap));assert before.shape==after.shape==(384,384)and before.dtype==after.dtype==np.uint8 and max(before.max(),after.max())<16
 outside=(after>0)&(before==0);changes=[{'world':[int(x-160),int(y-160)],'after_index':int(after[y,x])}for y,x in np.argwhere(outside)];assert changes==q['source_boundary_corrections'];count['new_source_boundary_cells_removed']+=len(changes)
 after=after.copy();after[outside]=0
 targets[n,0]=after;targets[n,5]=np.where((before!=after)|(before==15),before,0).astype(np.uint8)
 for pb in(6,7,8):targets[n,pb]=np.zeros_like(after)
 count['source_pose_pairs_reconstructed']+=1
def raw(ar,n,gb=0):
 f=ar.banks[gb]['frames'][n];v=decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128);assert v.serialize()==ar.g[v.start:v.end];return v.data
def atlas(ar,n):
 f=ar.banks[0]['frames'][n];return np.frombuffer(indexed_atlas(raw(ar,n),f['tile_count'])[0],np.uint8).reshape(-1,256)
def tile(at,t):return at[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
# Read original effect tile and original nine placement records, including hidden pixels.
effect_source=read(D/'structure_v3/manifest.json');assert effect_source['parent_sha256']==sha(old)
for n,body in((73,71),(74,72)):
 q=next(q for q in effect_source['effects']if q['ref']==n);fx=np.zeros((384,384),np.uint8);at=atlas(a,n);assert len(q['effect_parts'])==9
 for p in q['effect_parts']:
  assert p['flags']&0x3f==0;z=tile(at,p['tile'])
  if p['flags']&64:z=np.fliplr(z)
  if p['flags']&128:z=np.flipud(z)
  y,x=p['y']+160,p['x']+160;region=fx[y:y+16,x:x+16];region[z>0]=z[z>0]
 assert np.count_nonzero(fx)==54 and sha(fx.tobytes())==q['effect_sha256'];assert np.array_equal(fx,np.array(Image.open(D/f'structure_v3/effect_{n:03}.png')))
 for pb in PBS:targets[n,pb]=targets[body,pb].copy()
 if n==74:
  assert targets[n,0][164,125]==0 and targets[n,5][164,125]==1;targets[n,0][164,125]=1
 targets[n,0][fx>0]=fx[fx>0];count['original_dash_effect_texels_exact']+=54
for n in sorted(dash):
 for pb in PBS:
  want=np.array(Image.open(T/f'layer{pb}_{n:03}.png'));assert sha(want.tobytes())==rows[n]['layers'][str(pb)]and np.array_equal(want,targets[n,pb]);count['source_registered_layers_reconstructed']+=1
 before=np.where(targets[n,5],targets[n,5],targets[n,0]).astype(np.uint8)
 assert np.array_equal(before,np.array(Image.open(T/f'before_{n:03}.png')))
 assert np.array_equal(targets[n,0],np.array(Image.open(T/f'after_{n:03}.png')))
# Derive old Nova body independently from largest old dash73 connected component.
ar=a.layer(73)[0];labs,_=label(ar>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;oldbody=np.where(labs==sizes.argmax(),ar,0).astype(np.uint8);newbody=targets[71,0];Y,X=np.indices(oldbody.shape);Y-=160;X-=160
om=(Y<=9)|((Y==10)&(X<=10))|((Y==11)&(X==6))
nm=(Y<=8)|((Y==9)&((X<=-9)|(X>=-3)))|((Y==10)&((X<=-16)|(X>=-2)|((X<=-10)&np.isin(newbody,(1,2)))))|((Y==11)&((X<=-20)|(X>=4)))|((Y==12)&(X>=10))
protect=(X>=0)&(Y>=8)&np.isin(oldbody,(10,11,12));om&=~protect;nm&=~protect;headbody=oldbody.copy();headbody[om]=0;headbody[nm]=newbody[nm]
assert np.array_equal(headbody[~(om|nm)],oldbody[~(om|nm)])and np.array_equal(headbody[protect],oldbody[protect])
for name,z in [('old_head_mask',om),('new_head_mask',nm),('protected_hand',protect)]:assert np.array_equal(np.array(Image.open(N/(name+'.png')))>0,z)
assert np.array_equal(np.array(Image.open(N/'target_source_coords.png')),headbody)
for n in nova:
 assert np.array_equal(np.roll(oldbody,(-6,3),(0,1)),a.layer(n,0)[0]);target=np.roll(headbody,(-6,3),(0,1));assert np.array_equal(target,np.array(Image.open(N/f'target_{n:03}.png')));targets[n,0]=target;count['nova_semantic_head_targets_reconstructed']+=1
assert len(targets)==103
assert len(old)==len(new)and replace_entry(replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
 assert len(ob['frames'])==len(nb['frames'])
 for f,g in zip(ob['frames'],nb['frames']):
  n=f['index'];assert n==g['index'];u,v=raw(a,n,gb),raw(b,n,gb);count['raw_checked']+=1
  if gb!=0 or n not in selected:assert u==v and f['tile_count']==g['tile_count'];count['non_target_raw_exact']+=1
  else:assert g['tile_count']==32
sem=lambda c:[(p['flags'],p['tile'],p['x'],p['y'])for p in c['parts']]
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  if(n,pb)not in targets:assert sem(composition_frame(a.c,pb,n))==sem(composition_frame(b.c,pb,n));count['non_target_composition_exact']+=1
for n in selected:
 at=atlas(b,n)
 for pb in PBS:
  for p in composition_frame(b.c,pb,n)['parts']:
   z=tile(at,p['tile']);assert z.shape==(16,16)
   if p['tile']%16==0:assert not z[:,0].any()
   if p['flip_y']and p['tile']//16==0:assert not z[0].any()
   count['GPU_parts_checked']+=1
 if n in nova:
  oldat=atlas(a,n);used={p['tile']for pb in PBS[1:]for p in composition_frame(a.c,pb,n)['parts']}
  if n==220:assert len(used)==25
  for t in used:assert np.array_equal(tile(at,t),tile(oldat,t));count['original_nova_effect_full_tiles_exact']+=1
for n in list(range(67,85,2))+[93]:assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][n+1]['offset'];count['shared_pairs_exact']+=1
fire=read(D/'fire_constraints_v2/manifest.json');assert fire['parent_arc_sha256']==sha(old);windows={q['ref']:q['window_world']for q in fire['frames']}
def composite(layers,mask,arm):
 z=np.array(a.rgba(layers[0],0))
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   layer=np.array(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16));k=layer[:,:,3]>0;z[k]=layer[k]
 return z
for n in range(237):
 if n in{105,*range(175,183)}:continue
 expected={pb:targets.get((n,pb),a.layer(n,pb)[0])for pb in PBS}
 for pb in PBS:
  assert np.array_equal(expected[pb],b.layer(n,pb)[0]);count['layers_checked']+=1;count['non_target_layers_exact']+=int((n,pb)not in targets)
 for mask in range(16):
  for arm in(1,2):
   want=composite(expected,mask,arm);actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,want);count['RGBA_combinations_checked']+=1;count['selected_RGBA_exact'if n in selected else'non_target_RGBA_exact']+=1
   if n in windows:
    x0,y0,x1,y1=windows[n];assert x1-x0==8;sl=np.s_[y0+160:y1+160,x0+160:x1+160];assert np.array_equal(actual[sl],np.array(a.composite(n,mask,arm)[0])[sl]);count['original_muzzle_RGBA_exact']+=1
assert count['raw_checked']==512 and count['non_target_raw_exact']==489 and count['non_target_layers_exact']==1037 and count['non_target_composition_exact']==1688
assert count['RGBA_combinations_checked']==7296 and count['original_muzzle_RGBA_exact']==288 and count['original_nova_effect_full_tiles_exact']==41
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
native=D/'native_components_native_checks.json';nat=read(native);assert nat['passed']and nat['resources']['PL02_U.ARC']['candidate_sha256']==sha(new)
result={'passed':True,'scope':'나나 대시20+노바 머리3. 제작 모듈을 호출하지 않고 출처PNG/경계36셀/원효과를 재구성해 실제 ARC와 대조했다. 노바는 동일머리 의미영역만(+3,-6) 이동하며 원손·하체·효과는 보존한다.','parent':str(oldpath.relative_to(ROOT)),'parent_sha256':sha(old),'candidate':str(newpath.relative_to(ROOT)),'candidate_sha256':sha(new),'source_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(count),'other_entries_including_palette_audio_static_exact':True,'fixed_bank_boundaries_exact':True,'source_preserved':True,'producer_functions_called':False,'native_MIPS_performed_here':False,'producer_native_evidence':{'path':str(native.relative_to(ROOT)),'sha256':sha(native.read_bytes()),'passed':True},'runtime_verified':False,'visual_review_pending':True}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count)}))
