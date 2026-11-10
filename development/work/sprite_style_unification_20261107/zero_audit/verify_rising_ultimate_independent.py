"""라이징 Ultimate 출력 자원 독립 감사. 제작·패킹 함수는 호출하지 않는다."""
from pathlib import Path
import sys,json,collections
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D))
import verify_checkpoint20_x_candidates as r
H=r.H;ROOT=r.ROOT;refs=(100,101,102,103,104,231,232);PBS=r.PBS
P=H/'prepared_rising_fire_ultimate01';S=H/'rising_ultimate_shared02';O=D/'rising_independent';O.mkdir(exist_ok=True)
q=r.js(P/'proposal.json');frozen=r.js(P/'INPUT_FROZEN.json')
for name,h in frozen['files'].items():assert r.sha(r.read(P/name))==h
lock=r.check_lock(S);assert r.sha(r.read(S/'LOCK.json'))==q['source_art_manifest_sha256']==frozen['source_lock_sha256']
old=r.read(ROOT/q['sequential_parent']['path']);new=r.read(ROOT/q['files']['PL02_U.ARC']['path'])
assert r.sha(old)==q['sequential_parent']['sha256'];assert r.sha(new)==q['files']['PL02_U.ARC']['after']
a,b=r.Archive(old),r.Archive(new);report=r.js(S/'report.json');lut=np.array(report['palette_mapping'],np.uint8)
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
expectedlut=np.r_[0,1+(((rgb[17:32,None]-rgb[None,1:16])**2).sum(2)).argmin(1)].astype(np.uint8);assert np.array_equal(lut,expectedlut)
targets={};costumes={};source_proof=[]
for n in refs:
 m=231 if n==232 else n;shift=int(n==232);before=r.arr(S/f'before_{m:03}_indices.png');after=r.arr(S/f'after_{m:03}_indices.png')
 if not shift:
  directory=H/f'rising_ultimate_native{1 if n<103 else 2:02}';nb=r.arr(directory/f'ultimate_before_{n:03}_indices.png');na=r.arr(directory/f'ultimate_after_{n:03}_indices.png');mp=S/f'{n:03}_common_mask.png';r.read(mp);mask=np.array(Image.open(mp))>0
  derived=na.copy();derived[mask]=lut[nb][mask];assert np.array_equal(after,derived)
  edge=(derived>0)&(nb==0);bb=nb.copy();bb[edge]=derived[edge];assert np.array_equal(before,bb);assert not np.any((after>0)&(before==0))
  for val in np.unique(derived[edge]):assert np.array_equal(rgb[val],rgb[16+val])
  row=next(x for x in report['rows']if x['ref']==n);assert row['new_after_changed_pixels']==int(np.count_nonzero(derived!=na));assert sorted(row['before_original_native_exact_except_new_after_contour'])==sorted([[int(x)-160,int(y)-160,int(derived[y,x])]for y,x in zip(*np.where(edge))])
  source_proof.append({'ref':n,'shared_source_mask_reconstructed':True,'after_outside_shared_mask_exact':True,'new_source_edge_pixels':int(edge.sum())})
 before=np.roll(before,shift,0);after=np.roll(after,shift,0);same=np.all(r.color(before,a.words,16)==r.color(after,a.words),2)
 targets[n,0]=after;targets[n,5]=np.where(same,0,before).astype(np.uint8)
 for pb in(6,7,8):targets[n,pb]=np.zeros_like(after)
 costumes[n,0]=r.color(after,a.words);costumes[n,15]=r.color(before,a.words,16)
assert len(old)==len(new)and r.replace_entry(r.replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert r.bank_offsets(a.g,allow_aliases=True)==r.bank_offsets(b.g,allow_aliases=True)and r.bank_offsets(a.c)==r.bank_offsets(b.c)
count=collections.Counter();atlases={};reserved=[]
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 for f,g in zip(ab['frames'],bb['frames']):
  aa=r.decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);zz=r.decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128);assert aa.serialize()==a.g[aa.start:aa.end]and zz.serialize()==b.g[zz.start:zz.end];count['raw']+=1
  if gb==0 and f['index']in refs:assert g['tile_count']==32;atlases[f['index']]=np.frombuffer(r.indexed_atlas(zz.data,32)[0],np.uint8).reshape(32,256)
  else:assert aa.data==zz.data and f['tile_count']==g['tile_count'];count['non_target_raw_exact']+=1
sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
for pb in range(len(r.bank_offsets(a.c))):
 assert r.composition_frame(a.c,pb,0)['bank_frame_count']==r.composition_frame(b.c,pb,0)['bank_frame_count']
 for n in range(r.composition_frame(a.c,pb,0)['bank_frame_count']):
  ca,cb=r.composition_frame(a.c,pb,n),r.composition_frame(b.c,pb,n)
  if pb not in(0,5)or n not in refs:assert sem(ca)==sem(cb);count['non_target_composition_records_exact']+=1
  if pb in PBS and n in refs:
   for p in cb['parts']:
    t=p['tile'];assert 0<=t<32;tile=atlases[n][t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    assert t%16!=0 or not tile[:,0].any();assert not p['flip_y']or not tile[0].any();count['gpu_parts']+=1
    if pb in(6,7,8):assert not tile.any();reserved.append({'ref':n,'part_bank':pb,'tile':t})
for n in r.VALID:
 layers={}
 for pb in PBS:
  v=b.layer(n,pb)[0];count['layers']+=1
  if n in refs:assert np.array_equal(v,targets[n,pb]);count['authored_layers_exact']+=1;layers[pb]=v
  else:assert np.array_equal(v,a.layer(n,pb)[0]);count['other_layers_exact']+=1
 if n not in refs:continue
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,r.composite(layers,b.words,mask,arm));count['partial_RGBA']+=1
   if(mask in(0,15)):assert np.array_equal(actual,costumes[n,mask]);count['authored_costume_RGBA']+=1
 for form,mask in(('after',0),('before',15)):
  path=H/'rising_ultimate_pack_probe01'/f'{form}_{n:03}.png';r.read(path);assert np.array_equal(np.array(Image.open(path)),costumes[n,mask]);count['readback_PNG_exact']+=1
assert np.array_equal(atlases[231],atlases[232])
for pb in PBS:assert np.array_equal(b.layer(232,pb)[0],np.roll(b.layer(231,pb)[0],1,0))
assert count['raw']==512 and count['non_target_raw_exact']==505 and count['layers']==1140 and count['authored_layers_exact']==35
for path,h in r.tracked.items():assert r.sha(path.read_bytes())==h
out={'passed':True,'scope':'원화 등록→공통부위 변환→네이티브35층/14표시 독립 읽기 검사. 제작 함수 호출 및 실제게임 실행 없음. 미술은 루트 별도 담당.','candidate_sha256':r.sha(new),'source_sha256':r.sha(old),'counts':dict(count),'source_reconstruction':source_proof,'empty_layers_reserved_tiles':reserved,'derived232':'현재 수용된231의y+1 변환. raw타일 내용동일·압축슬롯별도. 원작 동일포즈 주장 아님','only_graphics_and_composition_changed':True,'fixed_bank_bounds':True,'all_other_entries_palette_audio_static_exact':True,'source_files_unchanged':{r.rel(p):h for p,h in r.tracked.items()},'producer_functions_called':False,'runtime_verified':False,'art_review_performed_here':False}
path=O/'ultimate.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'report_sha256':r.sha(path.read_bytes())}))
