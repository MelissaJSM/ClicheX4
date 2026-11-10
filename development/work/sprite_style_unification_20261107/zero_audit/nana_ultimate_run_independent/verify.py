"""제작 함수를 호출하지 않는 나나 Ultimate 이동32 source-to-native 읽기 검사."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas
O=Path(__file__).parent;D=O.parent.parent/'nana_audit/ultimate_run_repaint';P=D/'packed_run_candidate_v1';T=D/'joint_native_targets_v1'
sha=lambda x:hashlib.sha256(x).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rel=lambda p:p.relative_to(ROOT).as_posix()
oldpath=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC';newpath=P/'PL02_U.ARC';old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
assert sha(new)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
a,b=Archive(old),Archive(new);selected=set(range(1,33));PBS=(0,5,6,7,8);count=collections.Counter();targets={}
meta=read(T/'manifest.json');assert meta['source_arc_sha256']==sha(old);rows={q['ref']:q for q in meta['frames']};assert set(rows)==selected
for n,q in rows.items():
 bp,ap=ROOT/q['before_source'],ROOT/q['after_source'];assert sha(bp.read_bytes())==q['before_source_sha256'] and sha(ap.read_bytes())==q['after_source_sha256']
 prov=q['source_provenance'];assert sha((ROOT/prov['registration']).read_bytes())==prov['registration_sha256']
 before,after=np.array(Image.open(bp)),np.array(Image.open(ap));assert before.shape==after.shape==(384,384) and before.dtype==after.dtype==np.uint8 and max(before.max(),after.max())<16
 assert not ((after>0)&(before==0)).any();assert label(before>0,np.ones((3,3)))[1]==label(after>0,np.ones((3,3)))[1]==1
 targets[n,0]=after;targets[n,5]=np.where((before!=after)|(before==15),before,0).astype(np.uint8)
 for pb in (6,7,8):targets[n,pb]=np.zeros_like(after);assert not a.layer(n,pb)[0].any()
 for pb in PBS:
  want=np.array(Image.open(T/f'layer{pb}_{n:03}.png'));assert sha(want.tobytes())==q['layers'][str(pb)] and np.array_equal(want,targets[n,pb]);count['source_layers_reconstructed']+=1
 assert np.array_equal(np.where(targets[n,5],targets[n,5],targets[n,0]),before)
 assert np.array_equal(before,np.array(Image.open(T/f'before_{n:03}.png'))) and np.array_equal(after,np.array(Image.open(T/f'after_{n:03}.png')))
 count['registered_form_sources_checked']+=2
freeze=read(P/'INPUT_FROZEN.json');assert freeze['candidate_sha256']==sha(new)
for q in freeze['files']:
 assert sha((ROOT/q['path']).read_bytes())==q['sha256'],q['path'];count['frozen_file_hashes_checked']+=1
def raw(ar,n,gb=0):
 f=ar.banks[gb]['frames'][n];v=decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128);assert v.serialize()==ar.g[v.start:v.end];return v.data
def atlas(ar,n):
 f=ar.banks[0]['frames'][n];return np.frombuffer(indexed_atlas(raw(ar,n),f['tile_count'])[0],np.uint8).reshape(-1,256)
def tile(at,t):return at[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
assert len(old)==len(new) and replace_entry(replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True) and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ob,nb) in enumerate(zip(a.banks,b.banks)):
 assert len(ob['frames'])==len(nb['frames'])
 for f,g in zip(ob['frames'],nb['frames']):
  n=f['index'];assert n==g['index'];u,v=raw(a,n,gb),raw(b,n,gb);count['raw_checked']+=1
  if gb!=0 or n not in selected:assert u==v and f['tile_count']==g['tile_count'];count['non_target_raw_exact']+=1
  else:assert g['tile_count']==32
sem=lambda c:[(p['flags'],p['tile'],p['x'],p['y']) for p in c['parts']]
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  if (n,pb) not in targets:assert sem(composition_frame(a.c,pb,n))==sem(composition_frame(b.c,pb,n));count['non_target_composition_exact']+=1
for n in selected:
 at=atlas(b,n)
 for pb in PBS:
  for p in composition_frame(b.c,pb,n)['parts']:
   z=tile(at,p['tile']);assert z.shape==(16,16)
   if p['tile']%16==0:assert not z[:,0].any()
   if p['flip_y'] and p['tile']//16==0:assert not z[0].any()
   count['GPU_parts_checked']+=1
for n in range(1,33,2):assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][n+1]['offset'];count['shared_pairs_checked']+=1
fire=read(D/'firing_inputs_v1/manifest.json');assert fire['parent_arc_sha256']==sha(old);windows={q['ref']:q['window_world'] for q in fire['frames']};assert set(windows)==set(range(2,33,2))
def composite(layers,mask,arm):
 z=np.array(a.rgba(layers[0],0))
 for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   layer=np.array(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16));k=layer[:,:,3]>0;z[k]=layer[k]
 return z
for n in range(237):
 if n in {105,*range(175,183)}:continue
 expected={pb:targets.get((n,pb),a.layer(n,pb)[0]) for pb in PBS}
 for pb in PBS:
  assert np.array_equal(expected[pb],b.layer(n,pb)[0]);count['layers_checked']+=1;count['non_target_layers_exact']+=int((n,pb)not in targets)
 for mask in range(16):
  for arm in (1,2):
   want=composite(expected,mask,arm);actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,want);count['RGBA_combinations_checked']+=1;count['selected_RGBA_exact' if n in selected else 'non_target_RGBA_exact']+=1
   if n in windows:
    x0,y0,x1,y1=windows[n];assert x1-x0==8;sl=np.s_[y0+160:y1+160,x0+160:x1+160];assert np.array_equal(actual[sl],np.array(a.composite(n,mask,arm)[0])[sl]);count['original_muzzle_RGBA_exact']+=1
assert count['raw_checked']==512 and count['non_target_raw_exact']==480 and count['non_target_layers_exact']==980 and count['non_target_composition_exact']==1631
assert count['RGBA_combinations_checked']==7296 and count['original_muzzle_RGBA_exact']==512 and count['shared_pairs_checked']==16
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
result={'passed':True,'scope':'나나 Ultimate 이동32. 제작 모듈 미호출. 등록된 전후 원화64장을 직접 읽어 160층을 재구성하고 실제 ARC의 모든 표시/부분아머와 비교했다. 원화 생성 및 RGB57셀·재킷48셀 의미영역 편집의 재구성은 이 검사의 범위가 아니다.','parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),'source_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(count),'other_entries_including_palette_audio_static_exact':True,'fixed_bank_boundaries_exact':True,'source_preserved':True,'producer_functions_called':False,'native_MIPS_performed_here':False,'runtime_verified':False,'visual_review_pending':True}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count)}))
