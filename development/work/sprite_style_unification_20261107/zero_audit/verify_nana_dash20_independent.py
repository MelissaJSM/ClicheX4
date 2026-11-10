"""Independent native-output readback; production and registration code not imported."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas,compose_indices
D=Path(__file__).parent;N=D.parent/'nana_audit';A=N/'dash_repaint';P=A/'packed_dash_candidate_v1';T=A/'joint_layers_candidate_v1'
sha=lambda v:hashlib.sha256(v).hexdigest()
oldpath=N/'air_repaint/packed_air_candidate_v1/PL00_U.ARC';newpath=P/'PL00_U.ARC'
old=oldpath.read_bytes();new=newpath.read_bytes()
assert sha(old)=='721457a50ea48e76c1ac592eec21db274b43c5863cc5b3df310ac981d5890dca'
assert sha(new)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa'
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs=set(range(67,85))|{93,94};reserved={105,*range(175,183)}
manifest=json.loads((T/'manifest.json').read_text('utf8'));proof=json.loads((P/'verification.json').read_text('utf8'))
assert sha((T/'manifest.json').read_bytes())==proof['targets_manifest_sha256']=='7faf6f72361ee46289f414ecb3ae8fb040072068019a1f882d59fc2029e20bf8'
assert manifest['source_arc_sha256']==sha(old)
assert replace_entry(replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
count=collections.Counter();target={};rows={q['ref']:q for q in manifest['frames']};assert set(rows)==refs
assert all(not q['unresolved_folded_leg']for q in rows.values())
for gb,(oldbank,newbank)in enumerate(zip(a.banks,b.banks)):
 assert len(oldbank['frames'])==len(newbank['frames'])
 for f,q in zip(oldbank['frames'],newbank['frames']):
  n=f['index'];assert n==q['index'];x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);y=decode_stream(b.g,q['offset'],q['limit'],q['tile_count']*128)
  assert x.serialize()==a.g[x.start:x.end]and y.serialize()==b.g[y.start:y.end];count['raw_checked']+=1
  if gb==0 and n in refs:
   assert q['tile_count']==32
   atlas=np.frombuffer(indexed_atlas(y.data,32)[0],np.uint8).reshape(-1,256)
   assert not np.any(atlas[0:16,0:16])and not np.any(atlas[16:32,0:16])
  else:assert x.data==y.data and f['tile_count']==q['tile_count'];count['non_target_raw_exact']+=1
for n in range(67,85,2):assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][n+1]['offset'];count['exact_paired_streams']+=1
#93/94 retain their two original directory groups despite equal decoded data.
f93,f94=[b.banks[0]['frames'][n]for n in(93,94)]
assert decode_stream(b.g,f93['offset'],f93['limit'],4096).data==decode_stream(b.g,f94['offset'],f94['limit'],4096).data
count['separate93_94_identical_raw']=1
assert b.banks[0]['frames'][71]['offset']!=b.banks[0]['frames'][73]['offset']
for n in range(237):
 if n in reserved:continue
 for pb in PBS:
  layer=b.layer(n,pb)[0];count['layers_checked']+=1
  if n in refs:
   path=T/f'layer{pb}_{n:03}.png';want=np.array(Image.open(path));assert want.shape==(384,384)and want.dtype==np.uint8 and want.max()<16
   assert sha(want.tobytes())==(rows[n]['base_sha256']if pb==0 else rows[n]['layers'][str(pb)])
   assert np.array_equal(layer,want);target[n,pb]=want;count['authored_layer_exact']+=1
  else:assert np.array_equal(layer,a.layer(n,pb)[0]);count['non_target_layer_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  cp,ncp=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
  sem=lambda c:[(p['flags'],p['tile'],p['x'],p['y'])for p in c['parts']]
  if pb in PBS and n in refs:
   for p in ncp['parts']:assert p['tile']not in(0,16)and not p['flip_y'];count['safe_target_parts']+=1
  else:assert sem(cp)==sem(ncp);count['non_target_composition_exact']+=1
def color(arr,words):
 table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(words)],np.uint8)
 return table[arr]
def combine(layers,mask,arm):
 z=color(layers[0],b.words)
 for bit,pb in[(8,8),(1,5),(4,7),(2,6)]:
  if mask&bit:
   q=color(layers[pb],b.words[(32 if pb==7 and arm==2 else 16):]);k=q[:,:,3]>0;z[k]=q[k]
 return z
fire=json.loads((A/'fire_constraints/manifest.json').read_text('utf8'));guns={q['ref']:q for q in fire['frames']};assert set(guns)==set(range(68,85,2))and fire['source_arc_sha256']==sha(old)
for n in sorted(refs):
 layers={pb:target[n,pb]for pb in PBS}
 full=layers[0].copy()
 for pb in(8,5,7,6):full=np.where(layers[pb]>0,layers[pb],full)
 assert sha(full.tobytes())==rows[n]['full_sha256']
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);expected=combine(layers,mask,arm);assert np.array_equal(actual,expected);count['authored_partial_RGBA_combinations']+=1
   if n in guns:
    x0,y0,x1,y1=[160+v for v in guns[n]['gun_window']];assert x1-x0==8
    original=np.array(a.composite(n,mask,arm)[0]);assert np.array_equal(actual[y0:y1,x0:x1],original[y0:y1,x0:x1]);count['original_gun_RGBA_combinations']+=1
   if mask==15:
    assert np.array_equal(expected,color(full,b.words[16:]));count['full_costume_registered_RGBA_exact']+=1
# Reconstruct the original54-pixel dust/light effects from the parent's part list.
effects=json.loads((A/'effects/manifest.json').read_text('utf8'));assert effects['source_arc_sha256']==sha(old)
for row in effects['frames']:
 n=row['ref'];body=row['body_ref'];assert(n,body)in((73,71),(74,72))
 cp=composition_frame(a.c,0,n);parts=[]
 for p in row['parts']:
  actual=cp['parts'][p['index']];assert actual==p;parts.append(actual)
 f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
 pix,size,bounds,_=compose_indices(raw,f['tile_count'],{**cp,'parts':parts})
 fx=np.zeros((384,384),np.uint8);fx[160+bounds[1]:160+bounds[3],160+bounds[0]:160+bounds[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
 assert np.count_nonzero(fx)==54 and np.array_equal(fx,np.array(Image.open(A/'effects'/f'effect_{n:03}.png')))
 assert np.array_equal(target[n,0],np.where(fx>0,fx,target[body,0]))
 for pb in(5,6,7,8):assert np.array_equal(target[n,pb],target[body,pb])
 count['original_effect_pixels_exact']+=54
assert count['raw_checked']==508 and count['non_target_raw_exact']==488 and count['layers_checked']==1140 and count['non_target_layer_exact']==1040 and count['authored_layer_exact']==100
assert count['authored_partial_RGBA_combinations']==640 and count['original_gun_RGBA_combinations']==288 and count['original_effect_pixels_exact']==108
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
result={'passed':True,'scope':'나나 기본·포스 새 대시20참조 네이티브 등록의 독립 읽기 검사. 제작·정합·패킹 함수를 호출하지 않았다.','source_arc':str(oldpath.relative_to(ROOT)),'source_sha256':sha(old),'candidate':str(newpath.relative_to(ROOT)),'candidate_sha256':sha(new),'targets_manifest':str((T/'manifest.json').relative_to(ROOT)),'targets_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(count),'nonselected_6656_RGBA_combinations_implied_by1040_exact_layers_and_palettes':True,'all_audio_static_images_palette_other_entries_exact':True,'bank_boundaries_exact':True,'original_partial_reserved_data_exact':True,'actual_MIPS_test_performed_here':False,'gameplay_runtime_verified':False,'source_files_unchanged':True,'producer_functions_called':False,'visual_review_pending':False,'actually_viewed_readback_sheets':[{'path':str((P/f'readback_{i}.png').relative_to(ROOT)),'sha256':sha((P/f'readback_{i}.png').read_bytes())}for i in range(1,5)],'visual_observations':['최종 패킹 재추출4장 전체를 실제 열람했다. 머릿결·소매·옷 주름과 포스 베일 내부 명암이 대기와 이어지며 총구와 손목·어깨가 연결된다.','71/75 접힌 하체는 뒤 종아리와 구두가 분리되어 읽힌다. 기본 부츠가 가려지는 자세이며 원래 대시의 접힌 다리를 억지로 벌리지는 않았다.','83 기본 부츠는 다른 자세보다 좁지만 종아리·발의 면이 남는다.93 무릎의 회색 가로 절단처럼 보이던 경계는 피부 굴곡과 연결되며94 뒤로 뻗은 팔도 몸과 이어진다.','93/94는 사격 짝이 아니라 공중 대시 전환이다. 공통 readback 제목의 새 사격 문구는 해당 열에 적용되지 않는다. 실제 게임 연속 움직임과 모든 부분파츠 육안 검증은 별도다.']}
out=D/'nana_dash20_independent.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'out':str(out)}))
