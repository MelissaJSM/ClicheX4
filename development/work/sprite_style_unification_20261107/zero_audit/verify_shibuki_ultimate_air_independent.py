"""Independent readback of Ultimate air22; no producer/registration imports."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
D=Path(__file__).parent;H=D.parent/'shibuki_audit';P=H/'prepared_ultimate_air01';T=H/'ultimate_air_targets02'
sha=lambda v:hashlib.sha256(v).hexdigest()
oldpath=H/'prepared_rising_right_ultimate01/PL02_U.ARC';newpath=P/'PL02_U.ARC'
old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='d636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d'
assert sha(new)=='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7'
a,b=Archive(old),Archive(new);refs=set(range(33,55));PBS=(0,5,6,7,8);count=collections.Counter()
lp=T/'LOCK.json';assert sha(lp.read_bytes())=='bd7ca64adbf3dd1c65964d74984a47f905ff0776b8fcdcb6871d87fcea0b6ef4'
lock=json.loads(lp.read_text('utf8'));art={}
for name,h in lock['files'].items():
 p=T/name;assert sha(p.read_bytes())==h;f,n=name.split('_')[:2];z=np.array(Image.open(p));assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16;art[f,int(n)]=z
assert set(art)=={(f,n)for f in('before','after')for n in refs}
for name,h in lock['source_files'].items():assert sha((H/name).read_bytes())==h;count['provenance_files_hash_checked']+=1
assert len(old)==len(new)and replace_entry(replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
 assert len(ob['frames'])==len(nb['frames'])
 for o,n in zip(ob['frames'],nb['frames']):
  ref=o['index'];assert ref==n['index'];x=decode_stream(a.g,o['offset'],o['limit'],o['tile_count']*128);y=decode_stream(b.g,n['offset'],n['limit'],n['tile_count']*128)
  assert x.serialize()==a.g[x.start:x.end]and y.serialize()==b.g[y.start:y.end];count['raw_checked']+=1
  if gb!=0 or ref not in refs:assert x.data==y.data and o['tile_count']==n['tile_count'];count['non_target_raw_exact']+=1
  else:assert n['tile_count']==32
for n in range(33,55,2):assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][n+1]['offset'];count['shared_body_shot_pairs']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  x,y=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n);sem=lambda q:[(p['flags'],p['tile'],p['x'],p['y'])for p in q['parts']]
  if pb in PBS and n in refs:
   f=b.banks[0]['frames'][n];raw=decode_stream(b.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
   for p in y['parts']:
    t=p['tile'];assert 0<=t<32;tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    if t%16==0:assert not tile[:,0].any()
    if p['flip_y']:assert not tile[0].any()
    count['GPU_parts_checked']+=1
  else:assert sem(x)==sem(y);count['non_target_part_records_exact']+=1
for n in range(237):
 if n in {105,*range(175,183)}:continue
 if n in refs:
  ar,br=art['after',n],art['before',n];same=np.all(np.array(a.rgba(ar,0))==np.array(a.rgba(br,16)),axis=2)
  layers={0:ar,5:np.where(same,0,br).astype(np.uint8),**{q:np.zeros_like(ar)for q in(6,7,8)}}
 for pb in PBS:
  count['layers_checked']+=1
  if n in refs:assert np.array_equal(b.layer(n,pb)[0],layers[pb]);count['registered_layers_exact']+=1
  else:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0]);count['non_target_layers_exact']+=1
 if n in refs:
  for mask in range(16):
   for arm in(1,2):
    want=a.rgba(br,16)if mask&1 else a.rgba(ar,0)
    assert b.composite(n,mask,arm)[0].tobytes()==want.tobytes();count['registered_RGBA_combinations_exact']+=1
 else:
  for mask in(0,15):assert a.composite(n,mask)[0].tobytes()==b.composite(n,mask)[0].tobytes();count['non_target_full_display_exact']+=1
# Independently derive the 60-pixel module from parent after34 and translate it.
mi=H/'ultimate_air_shot_inputs01/manifest.json';m=json.loads(mi.read_text('utf8'));master=m['master_barrel'];mp=ROOT/master['master_mask_source'];assert sha(mp.read_bytes())==master['master_mask_source_sha256']
guard=np.array(Image.open(mp))>0;assert guard.sum()==71
old34=a.layer(34,0)[0];source=np.where(guard,old34,0).astype(np.uint8);assert np.count_nonzero(source)==60 and sha(source.tobytes())==master['native_indices_sha256']
ys,xs=np.where(guard)
for row in m['barrels']:
 n=row['shot_ref'];f=row['form'];dx,dy=row['module_translation'];xx,yy=xs+dx,ys+dy
 expected=np.array(a.rgba(source,0))[ys,xs];actual=np.array(b.composite(n,15 if f=='before'else 0)[0])[yy,xx]
 assert np.array_equal(actual,expected);assert [-24+dx,-10+dy]==row['muzzle_world'];count['original34_module_translated_RGBA_exact']+=1
assert count['raw_checked']==512 and count['non_target_raw_exact']==490
assert count['registered_layers_exact']==110 and count['non_target_layers_exact']==1030
assert count['registered_RGBA_combinations_exact']==704 and count['original34_module_translated_RGBA_exact']==22
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
out=D/'shibuki_ultimate_air_independent.json'
report={'passed':True,'scope':'시부키 얼티밋 공중33~54 전후44표시를 제작 함수 없이 독립 읽기 검사했다. 총열은 각 옛 모양 보존이 아니라 부모 after34의60픽셀 모듈을 원총구로 평행이동한 것이 정확하다.','source_arc':str(oldpath.relative_to(ROOT)),'source_sha256':sha(old),'candidate':str(newpath.relative_to(ROOT)),'candidate_sha256':sha(new),'target_lock_sha256':sha(lp.read_bytes()),'counts':dict(count),'all_other_entries_audio_palette_static_exact':True,'bank_boundaries_exact':True,'source_files_preserved':True,'producer_functions_called':False,'native_MIPS_performed_here':False,'runtime_verified':False,'visual_review_pending':True}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'out':str(out)}))
