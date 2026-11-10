"""Read the frozen 24-pose Ultimate wall proposal without importing its producer."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
D=Path(__file__).parent;H=D.parent/'shibuki_audit';P=H/'prepared_ultimate_wall01'
sha=lambda x:hashlib.sha256(x).hexdigest()
oldpath=H/'prepared_ultimate_lowhp01/PL02_U.ARC';newpath=P/'PL02_U.ARC'
old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b'
assert sha(new)=='c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf'
a,b=Archive(old),Archive(new);targets=set(range(55,67));PBS=(0,5,6,7,8);count=collections.Counter()
lockpath=H/'ultimate_wall_target_lock01.json';lock=json.loads(lockpath.read_text('utf8'))['targets'];assert set(lock)=={f'{form}/{n}'for form in('before','after')for n in targets}
assert len(old)==len(new)and replace_entry(replace_entry(new,2,a.g),3,a.c)==old
assert a.p==b.p and bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
art={}
for key,r in lock.items():
 p=ROOT/r['path'];assert sha(p.read_bytes())==r['sha256'];arr=np.array(Image.open(p));assert arr.shape==(384,384)and arr.dtype==np.uint8 and int(arr.max())<16
 f,n=key.split('/');art[f,int(n)]=arr
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
 assert len(ob['frames'])==len(nb['frames'])
 for o,n in zip(ob['frames'],nb['frames']):
  assert o['index']==n['index'];ref=o['index'];x=decode_stream(a.g,o['offset'],o['limit'],o['tile_count']*128);y=decode_stream(b.g,n['offset'],n['limit'],n['tile_count']*128)
  assert x.serialize()==a.g[x.start:x.end]and y.serialize()==b.g[y.start:y.end];count['raw_checked']+=1
  if gb!=0 or ref not in targets:assert x.data==y.data and o['tile_count']==n['tile_count'];count['non_target_raw_exact']+=1
  else:
   assert n['tile_count']==32;atlas=np.frombuffer(indexed_atlas(y.data,32)[0],np.uint8).reshape(32,256);assert not np.any(atlas[:,0]);count['selected_stream_gpu_u_boundary_exact_transparent']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  x,y=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n);sem=lambda q:[(p['flags'],p['tile'],p['x'],p['y'])for p in q['parts']]
  if pb in PBS and n in targets:
   f=b.banks[0]['frames'][n];raw=decode_stream(b.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
   for p in y['parts']:
    assert 0<=p['tile']<32
    if p['flip_y']and p['tile']//16==0:assert not np.any(atlas[0,p['tile']%16*16:p['tile']%16*16+16])
    count['selected_gpu_parts']+=1
  else:assert sem(x)==sem(y);count['non_target_part_records_exact']+=1
for n in range(237):
 if n in {105,*range(175,183)}:continue
 for pb in PBS:
  x,y=a.layer(n,pb)[0],b.layer(n,pb)[0];count['layers_read']+=1
  if n not in targets:assert np.array_equal(x,y);count['non_target_layers_exact']+=1
  elif pb==0:assert np.array_equal(y,art['after',n]);count['authored_base_layers_exact']+=1
  elif pb in(6,7,8):assert not np.any(y);count['intentionally_empty_armor_layers_exact']+=1
 for form,mask,start in [('before',15,16),('after',0,0)]:
  actual=b.composite(n,mask)[0]
  if n in targets:assert actual.tobytes()==b.rgba(art[form,n],start).tobytes();count['authored_full_composites_exact']+=1
  else:assert actual.tobytes()==a.composite(n,mask)[0].tobytes();count['non_target_composites_exact']+=1
barrels=json.loads((H/'ultimate_wall_inputs01/manifest.json').read_text('utf8'))['refs']
for n in range(56,67,2):
 row=next(q for q in barrels if q['body_ref']==n-1);box=tuple(160+x for x in row['barrel_rect_world'])
 for mask in(0,15):
  assert a.composite(n,mask)[0].crop(box).tobytes()==b.composite(n,mask)[0].crop(box).tobytes();count['original_barrel_RGBA_exact']+=1
assert count['raw_checked']==512 and count['non_target_raw_exact']==500 and count['authored_full_composites_exact']==24 and count['non_target_composites_exact']==432
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
report={'passed':True,'scope':'시부키 얼티밋 벽55..66의 캡슐 전/후24표시 독립 읽기 검증.제작/등록/패킹 함수는 호출하지 않았다.원화 미술·실기는 별도다.','source':str(oldpath.relative_to(ROOT)),'source_sha256':sha(old),'candidate':str(newpath.relative_to(ROOT)),'candidate_sha256':sha(new),'target_lock_sha256':sha(lockpath.read_bytes()),'counts':dict(count),'all_other_entries_including_audio_static_palette_exact':True,'fixed_bank_offsets_exact':True,'source_files_preserved':True,'producer_function_called':False,'native_MIPS_performed_here':False,'runtime_verified':False,'visual_review_pending':False}
report['actually_viewed_readbacks']=[{'path':str((P/f/f'actual_{i:02}.png').relative_to(ROOT)),'sha256':sha((P/f/f'actual_{i:02}.png').read_bytes())}for f in('before','after')for i in range(2)]
report['visual_observations']=['양 의상4시트24표시를 실제 열람했다.귀·머릿결·옷의 명암이 대기와 이어지고 사격팔과 몸통의 큰 분리, 손 위로 튀어나온 옛 소매 흔적은 보이지 않는다.','수영복59..66의 위로 뻗은 팔은 원래 벽 접점을 유지한 자세로 읽힌다.정지 시트 판정이며 실시간 벽타기 연결/전수 부분파츠 미술 수용을 뜻하지 않는다.']
out=D/'shibuki_ultimate_wall_independent.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'out':str(out)}))
