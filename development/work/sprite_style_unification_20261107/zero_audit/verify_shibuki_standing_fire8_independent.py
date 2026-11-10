"""고정 후보 읽기: 새40층/원효과/총열/18참조 전체타일 순열. 제작 함수 미호출."""
from pathlib import Path
import json,hashlib,collections,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,render
P=H/'prepared_standing_fire_base01';T=H/'standing_fire_targets_probe01';O=D/'shibuki_standing_fire8_independent01'
PBS=(0,5,6,7,8);REFS=set(range(85,93));RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
oldp=H/'prepared_standing_special_base01/PL00_U.ARC';newp=P/'PL00_U.ARC';old,new=blob(oldp),blob(newp)
assert sha(old)=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'
assert sha(new)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
a,b=Archive(old),Archive(new);proposal=js(P/'proposal.json');lock=js(P/'PREPARED_LOCK.json');source=js(H/'standing_fire_locked01/LOCK.json');producer=js(P/'verification.json')
for p,h in lock['files'].items():assert sha(blob(P/p))==h,p
for p,h in lock.get('scripts',{}).items():assert sha(blob(H/p))==h,p
assert sha(blob(H/'standing_fire_locked01/LOCK.json'))==proposal['target_lock_sha256']=='ab487baf93cb62a6c73fdf2121452adcbc10dff2e33c55ef00c3e66f60b2f3e5'
for p,h in source['files'].items():assert sha(blob(ROOT/p))==h,p
assert len(source['files'])==442 and source['parent_sha256']==sha(old)and set(source['refs'])==REFS
meta=js(T/'manifest.json');assert meta['parent']['sha256']==sha(old)and set(meta['refs'])==REFS
assert sha(blob(H/'standing_fire_layers_probe02/report.json'))==meta['source_joint_report_sha256']
counts=collections.Counter();target={};storage=set(source['storage_only_refs']);assert len(storage)==18 and not storage&REFS
maps={};permutation=[]
for g in producer['storage_permutation_proofs']:
 mp={int(k):v for k,v in g['mapping'].items()};assert set(mp)==set(mp.values())==set(range(32))
 n=g['refs'][0];assert sha(raw(a,0,n))==g['source_raw_sha256']and sha(raw(b,0,n))==g['permuted_raw_sha256']
 for t in range(32):assert np.array_equal(tile(a,n,t),tile(b,n,mp[t]));counts['whole_256nibble_tiles_inverse_exact']+=1
 for t in g['fixed_tiles']:assert mp[t]==t
 for n in g['refs']:
  assert n in storage and n not in maps;maps[n]=mp
  assert raw(a,0,n)==raw(a,0,g['refs'][0])and raw(b,0,n)==raw(b,0,g['refs'][0])
 permutation.append({'refs':g['refs'],'mapping':mp,'all32_complete_tiles_exact':True,'fixed_tiles':g['fixed_tiles']})
assert set(maps)==storage
for n in REFS:
 for pb in PBS:
  z=png(T/f'{n:03}_bank{pb}_indices.png');assert sha(z.tobytes())==source['targets'][str(n)][str(pb)]==meta['targets'][str(n)][str(pb)]
  if n!=88:assert np.array_equal(z,png(H/f'standing_fire_layers_probe02/{n:03}_bank{pb}_indices.png'))
  target[n,pb]=z
fxparts=[q for q in parts(a,0,88)if q['tile']in(7,8)];assert len(fxparts)==2
fx=render(a,88,0,fxparts);assert np.count_nonzero(fx)==83 and set(np.unique(fx))=={0,6}
assert np.array_equal(fx,png(T/'088_effect_indices.png'))
original=Archive(read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC'])
original_fx=render(original,88,0,[q for q in parts(original,0,88)if q['tile']in(7,8)])
assert np.array_equal(fx>0,original_fx>0)
fxproof=[]
for t in(7,8):
 assert np.array_equal(tile(a,88,t),tile(b,88,t))and sha(tile(a,88,t).tobytes())==meta['effect88']['all_effect_tiles'][str(t)]['all256_nibble_sha256']
 fxproof.append({'tile':t,'whole_tile_parent_candidate_exact':True,'sha256':sha(tile(b,88,t).tobytes())})
for pb in PBS:
 z=np.zeros_like(target[89,pb]);z[:,:-1]=target[89,pb][:,1:]
 z[fx>0]=fx[fx>0]if pb==0 else 0
 assert np.array_equal(z,target[88,pb])
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne]
allow=np.zeros(len(old),bool)
for q in oe:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
changed=REFS|storage
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in changed:assert 0<bf['tile_count']<=32
  else:assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as ex:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
    else:raise AssertionError('New invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'rendered_exact']);continue
  expected=target[n,pb]if n in REFS else a.layer(n,pb)[0]
  assert np.array_equal(b.layer(n,pb)[0],expected),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_art_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in changed:
   if n in storage:
    assert len(op)==len(bp)
    for p,q in zip(op,bp):assert(q['flags'],q['tile'],q['x'],q['y'])==(p['flags'],maps[n][p['tile']],p['x'],p['y'])
    counts['storage_part_sequences_exact_except_tile']+=1
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and q['unknown_flags']==0
    z=tile(b,n,t);assert not(t%16==0 and z[:,0].any())and not(q['flip_y']and t//16==0 and z[0].any());counts['GPU_parts_checked']+=1
  else:assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(changed):
 oldowners=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']]
 newowners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert set(oldowners)<=changed and set(newowners)<=changed
 if n in storage:assert oldowners==newowners
 groups.append({'ref':n,'old_owners':oldowners,'new_owners':newowners,'tiles':b.banks[0]['frames'][n]['tile_count']})
gunproof=[]
for n in(85,86,87,89,90,91,92):
 guard=png(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png')>0;gun=png(H/f'standing_fire_modules_probe02/{n:03}_gun_indices.png');rgba=color(a,gun)
 # Guard includes transparent cells. Its source is the accepted parent base gun,
 # not an inferred rectangle around all dark pixels or old Fourth armor.
 assert np.array_equal(np.array(a.composite(n,0)[0])[guard],rgba[guard])
 gunproof.append({'ref':n,'guard_pixels':int(guard.sum()),'gun_opaque':int((gun>0).sum()),'parent_base_RGBA_exact':True})
for n in sorted(changed):
 for mask in range(16):
  for arm in(1,2):
   if n in REFS:
    expected=color(b,target[n,0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:
      v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   else:expected=np.array(a.composite(n,mask,arm)[0])
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,expected)
   counts['target_partial_RGBA_exact'if n in REFS else'storage_partial_RGBA_exact']+=1
   if n==88:assert np.array_equal(actual[fx>0],color(a,fx)[fx>0]);counts['effect_RGBA_exact']+=1
   elif n in REFS:
    guard=png(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png')>0;gun=png(H/f'standing_fire_modules_probe02/{n:03}_gun_indices.png')
    assert np.array_equal(actual[guard],color(a,gun)[guard]);counts['gun_guard_RGBA_exact']+=1
nativep=D/'shibuki_standing_fire_directory_native01/report.json';native=js(nativep);assert native['passed']and native['candidate_sha256']==sha(new)and native['stats']['references']==508
for q in native['references']:assert q['decoded_sha256']==sha(raw(b,q['bank'],q['ref']))
O.mkdir(exist_ok=False);sheets=[]
box=(122,121,194,188);w,h=72,67
def sheet(name,rows):
 cw,ch=w*4+7,h*4+25;im=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(caption,pic)in enumerate(row):
   bb=pic.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=pic.crop(box).resize((w*4,h*4),Image.Resampling.NEAREST);im.paste(v,(x*cw+3,y*ch+22),v)
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
for i in range(4):
 ns=[85+i*2,86+i*2];rows=[]
 for n in ns:rows.append([(f'{n} old base',a.composite(n,0)[0]),(f'{n} new base',b.composite(n,0)[0]),(f'{n} old fourth',a.composite(n,15)[0]),(f'{n} new fourth',b.composite(n,15)[0])])
 sheet(f'full_{i}.png',rows)
for n in sorted(REFS):sheet(f'partial_{n}.png',[[(f'{n} {name}',b.composite(n,mask)[0])for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body+legs',10))]])
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==482 and counts['whole_256nibble_tiles_inverse_exact']==288 and counts['target_layers_exact']==40 and counts['target_partial_RGBA_exact']==256 and counts['storage_partial_RGBA_exact']==576
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'시부키 기본/포스85..92 40층과 기존18참조 전체32타일 역순열/부분 표시 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha((H/'standing_fire_locked01/LOCK.json').read_bytes()),'locked_inputs':len(source['files']),'counts':dict(counts),'permutation_proofs':permutation,'stream_groups':groups,'gun_guard_proofs':gunproof,'effect83':{'old_full_tiles':fxproof,'original_US_world_alpha_exact':True,'current_index':6,'source89_dx':-1,'new_head_behind_effect_occluded_cells':2},'reserved_layers':reserved,'native_report':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'all508_decoded_hashes_bound':True,'executed_here':False},'other_entries_audio_palette_all_bank_boundaries_exact':True,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['새원화14셀 생성·재양자화/새관절의 원본 의미 재현을 본 reader가 다시 수행한 것은 아니다. 잠금442개와 등록최종35층→88효과파생5층→실제자원을 직접 대조했다.','18저장참조는 원raw 그대로가 아니라 모든256nibble을 보존한32타일 순열이다. 그림·파트 위치/flip·부분표시는exact이며 원시바이트동일과 구분한다.','새8선택사본1..8 동기화는 별도 root 후속이다. 기존18저장대상의 표시일치를 UI실기검증으로 확대하지 않는다.','원MIPS508 검사는 별도보고에 있으며 실제게임/전체GPU렌더/사용자수용은 별도이다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
