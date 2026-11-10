"""라이징 Ultimate 출력 자원 독립 감사. 제작·패킹 함수는 호출하지 않는다."""
from pathlib import Path
import sys,json,collections
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;sys.path.insert(0,str(D))
import verify_checkpoint20_x_candidates as r
H=r.H;ROOT=r.ROOT;refs=(100,101,102,103,104,231,232);PBS=r.PBS
P=H/'prepared_rising_fire_base02';S=H/'rising_common_layers02';O=D/'rising_independent';O.mkdir(exist_ok=True)
q=r.js(P/'proposal.json');frozen=r.js(P/'INPUT_FROZEN.json')
for name,h in frozen['files'].items():assert r.sha(r.read(P/name))==h
lock=r.check_lock(S);assert r.sha(r.read(S/'LOCK.json'))==q['source_art_manifest_sha256']==frozen['source_lock_sha256']
old=r.read(ROOT/q['sequential_parent']['path']);new=r.read(ROOT/q['files']['PL00_U.ARC']['path'])
assert r.sha(old)==q['sequential_parent']['sha256'];assert r.sha(new)==q['files']['PL00_U.ARC']['after']
a,b=r.Archive(old),r.Archive(new);report=r.js(S/'report.json')
targets={};costumes={};source_proof=[]
for n in refs:
 m=231 if n==232 else n;shift=int(n==232)
 for pb in PBS:targets[n,pb]=np.roll(r.arr(S/f'{m:03}_bank{pb}_indices.png'),shift,0)
 if shift:continue
 row=next(v for v in report['rows']if v['ref']==n)
 directory=H/('rising104_arm_native02'if n==104 else f'rising_fire_native{1 if n<103 else 2:02}')
 base=r.arr(directory/f'base_{n:03}_indices.png');full=r.arr(directory/f'fourth_{n:03}_indices.png');original=full.copy()
 mm=Image.new('1',(384,384));ImageDraw.Draw(mm).polygon([(x+160,y+160)for x,y in row['common_head_polygon']],fill=1);mask=np.array(mm,bool)
 yy,xx=np.indices(base.shape);x=xx-160;y=yy-160;x0,y0,x1,y1=row['face_rect'];face=(x>=x0)&(x<x1)&(y>=y0)&(y<y1)
 mask &=np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13]))
 x0,y0,x1,y1=row['decoration_rect'];deco=(x>=x0)&(x<x1)&(y>=y0)&(y<y1);mask|=deco
 mp=S/f'{n:03}_common_mask.png';r.read(mp);assert np.array_equal(mask,np.array(Image.open(mp))>0)
 full[mask]=0;full[deco]=original[deco];missing=(base>0)&(full==0)&~(mask&~deco)
 marks=row['contour_material_registration'];assert set(map(tuple,np.argwhere(missing)))=={(my+160,mx+160)for mx,my,src,dst in marks}
 for mx,my,src,dst in marks:assert base[my+160,mx+160]==src;full[my+160,mx+160]=dst
 owner=np.full(base.shape,6,np.uint8);owner[y>={100:16,101:12,102:12,103:11,104:12,231:12}[n]]=8
 if n in(101,102):owner[(x<=-6)&(y>=7)&(y<=17)]=8
 owner[(x<=-10)&(y<8)]=7
 if n==100:owner[(x<=-10)&(y>=2)&(y<17)]=7
 owner[(x>=7)&(y>={100:8,101:0,102:2,103:2,104:1,231:1}[n])&(y<14)]=7;owner[deco]=5
 assert np.array_equal(owner,r.arr(S/f'{n:03}_owner.png'));assert np.array_equal(base,targets[n,0])
 for pb in(5,6,7,8):
  derived=np.where(owner==pb,full,0).astype(np.uint8)
  if(n,pb)==(103,7):
   sd=H/'rising103_sleeve_native03';ed=H/'rising103_sleeve_edit01';path=ed/'generated.png';raw=r.read(path);im=Image.open(path).convert('RGBA');assert im.size==(1254,1254)
   small=np.array(im.resize((64,64),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[17:32]],np.int32)
   qi=(1+((small[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None])**2).sum(3).argmin(2)).astype(np.uint8);qi[small[:,:,3]<128]=0
   sampled=np.zeros(base.shape,np.uint8);sampled[124:188,128:192]=qi;assert np.array_equal(sampled,r.arr(sd/'sampled_source_indices.png'))
   gp=ed/'sleeve_region.png';r.read(gp);guide=np.array(Image.open(gp))>0;local=guide&~mask&(derived>0);missing_local=local&(sampled==0)
   edge=[[int(px)-160,int(py)-160,int(derived[py,px])]for py,px in zip(*np.where(missing_local))]
   assert edge==[[-12,-13,4],[-16,-2,1],[-16,-1,1],[-16,0,1],[-15,1,1],[-14,2,1]]
   local&=~missing_local;assert local.sum()==70;previous=derived.copy();derived[local]=sampled[local];assert np.count_nonzero(derived!=previous)==58
  assert np.array_equal(derived,targets[n,pb]),(n,pb)
 source_proof.append({'ref':n,'source_and_common_head_ownership_reconstructed':True,'registered_contour_pixels':len(marks),'new_local_sleeve103':n==103})
for n in refs:
 layers={pb:targets[n,pb]for pb in PBS}
 for mask in(0,15):costumes[n,mask]=r.composite(layers,a.words,mask,1)
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
  if pb not in PBS or n not in refs:assert sem(ca)==sem(cb);count['non_target_composition_records_exact']+=1
  if pb in PBS and n in refs:
   for p in cb['parts']:
    t=p['tile'];assert 0<=t<32;tile=atlases[n][t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    assert t%16!=0 or not tile[:,0].any();assert not p['flip_y']or not tile[0].any();count['gpu_parts']+=1
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
 for form,mask in(('base',0),('fourth',15)):
  path=H/'rising_base_pack_probe02'/f'{form}_{n:03}.png';r.read(path);assert np.array_equal(np.array(Image.open(path)),costumes[n,mask]);count['readback_PNG_exact']+=1
assert np.array_equal(atlases[231],atlases[232])
for pb in PBS:assert np.array_equal(b.layer(232,pb)[0],np.roll(b.layer(231,pb)[0],1,0))
assert count['raw']==508 and count['non_target_raw_exact']==501 and count['layers']==1140 and count['authored_layers_exact']==35
for path,h in r.tracked.items():assert r.sha(path.read_bytes())==h
out={'passed':True,'scope':'원화 등록→공통부위 변환→네이티브35층/14표시 독립 읽기 검사. 제작 함수 호출 및 실제게임 실행 없음. 미술은 루트 별도 담당.','candidate_sha256':r.sha(new),'source_sha256':r.sha(old),'counts':dict(count),'source_reconstruction':source_proof,'derived232':'현재 수용된231의y+1 변환. raw타일 내용동일·압축슬롯별도. 원작 동일포즈 주장 아님','only_graphics_and_composition_changed':True,'fixed_bank_bounds':True,'all_other_entries_palette_audio_static_exact':True,'source_files_unchanged':{r.rel(p):h for p,h in r.tracked.items()},'producer_functions_called':False,'runtime_verified':False,'art_review_performed_here':False}
path=O/'base_v2.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'report_sha256':r.sha(path.read_bytes())}))
