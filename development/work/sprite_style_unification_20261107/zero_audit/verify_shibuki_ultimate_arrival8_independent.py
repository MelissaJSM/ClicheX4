"""등장8 읽기 독립검사. 제작 모듈과 게임 실행을 호출하지 않는다."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,render,color,polygons
H=D.parent/'shibuki_audit';P=H/'prepared_ultimate_arrival_partial01'
C=H/'ultimate_arrival_common_probe03';T=H/'ultimate_arrival_targets01'
O=D/'shibuki_ultimate_arrival8_independent01'
PBS=(0,5,6,7,8);REFS={130,131,133,134,136,137,138,139};BODIES=(133,136,137,138,139)
RESERVED={105,*range(175,183)}
sha=lambda x:hashlib.sha256(x).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def readj(p):return json.loads(readb(p))
def png(p):readb(p);return np.asarray(Image.open(p))
def npy(p):readb(p);return np.load(p)
def over(bg,fg):return np.where(fg>0,fg,bg).astype(np.uint8)
def shift(v,dx=0,dy=0):
 z=np.zeros_like(v);y,x=np.nonzero(v);z[y+dy,x+dx]=v[y,x];return z
def blank():return np.zeros((384,384),np.uint8)

oldp=H/'prepared_ultimate_hurt02/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=readb(oldp),readb(newp)
assert sha(old)=='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94'
assert sha(new)=='3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138'
a,b=Archive(old),Archive(new)
proposal=readj(P/'proposal.json');lock=readj(P/'SOURCE_LOCK.json')
assert sha(readb(P/'SOURCE_LOCK.json'))==proposal['target_lock']['sha256']
assert lock['parent_sha256']==sha(old) and lock['candidate_sha256']==sha(new)
for name,h in lock['files'].items():assert sha(readb(ROOT/name))==h,name
meta=readj(T/'manifest.json');cm=readj(C/'report.json')
assert sha(readb(T/'manifest.json'))==proposal['targets']['sha256']
assert sha(readb(C/'report.json'))==meta['body_report_sha256']
assert set(meta['refs'])==REFS and cm['refs_excluded']==[135]
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8)
assert lut.tolist()==cm['palette_map']

# 원화 등록 뒤의 발/팔 정합과 공통 부위만 별도로 재구성한다.
feet=H/'ultimate_arrival136_foot_contacts01';fm=readj(feet/'report.json')
yy,xx=np.indices((384,384));xx-=160;yy-=160
for q in fm['rows']:
 f=q['form'];srcp=H/f'ultimate_arrival_separate_native01/{f}_136_indices.png';src=png(srcp)
 assert sha(readb(srcp))==q['source_sha256'];v=src.copy()
 for x0,x1 in((-18,-7),(0,12)):
  m=(xx>=x0)&(xx<=x1)&(yy>=15)&(yy<=24);module=np.where(m,src,0).astype(np.uint8)
  v[m&(yy>15)]=0;z=shift(module,dy=1);v[z>0]=z[z>0]
 assert np.array_equal(v,png(feet/f'{f}_136_indices.png')) and np.array_equal(v[yy<=15],src[yy<=15])
armdir=H/'ultimate_arrival_overhead_arm_composed02';am=readj(armdir/'report.json')
for q in am['rows']:
 n=q['ref'];s=H/q['source_folder'];bef=png(s/f'before_{n:03}_indices.png');aft=png(s/f'after_{n:03}_indices.png').copy()
 for f in('before','after'):assert sha(readb(s/f'{f}_{n:03}_indices.png'))==q['source_hashes'][f]
 donor=png(H/f'ultimate_arrival_overhead_arm_inspection01/after_{n:03}_donor_indices.png')
 assert sha(donor.tobytes())==q['donor_array_sha256'];m=polygons(q['polygons']);aft[m]=donor[m]
 apex=q['new_clasp_apex_y'];hand=np.zeros_like(m);hand[160+apex-1:160+apex+4,156:164]=True
 low=np.zeros_like(m);low[160+apex+4:160+apex+7,156:165]=True;hand|=low&np.isin(bef,(10,11,12,13))
 aft[hand]=lut[bef][hand]
 assert np.array_equal(m,png(armdir/f'{n:03}_arm_mask.png')>0)
 assert np.array_equal(hand,png(armdir/f'{n:03}_new_clasp_mask.png')>0)
 assert np.array_equal(aft,png(armdir/f'after_{n:03}_indices.png'))
 assert np.array_equal(bef,png(armdir/f'before_{n:03}_indices.png'))
body={};source_rows=[]
for q in cm['rows']:
 n=q['ref'];s=H/q['source_folder'];bef=png(s/f'before_{n:03}_indices.png');aft=png(s/f'after_{n:03}_indices.png').copy()
 for f in('before','after'):assert sha(readb(s/f'{f}_{n:03}_indices.png'))==q['source_hashes'][f]
 head=polygons(q['head_polygons']);legs=polygons(q['leg_polygons']);hands=np.zeros_like(head)
 for x0,y0,x1,y1 in q['hand_rectangles']:hands[y0+160:y1+160,x0+160:x1+160]=True
 hands&=np.isin(bef,(10,11,12,13))
 if n==133:hands[179:184,150:159]=True
 if n==136:legs[169,157]=True
 if n==137:head[144:157,143:150]=False;head[146:159,164:171]=False
 if n in(138,139):
  head&=~(png(s/f'{n:03}_arm_mask.png')>0);hands=png(s/f'{n:03}_new_clasp_mask.png')>0
  if n==138:hands[135,158]=True
 common=head|legs|hands;aft[common]=lut[bef][common]
 for k,m in(('head',head),('legs',legs),('hands',hands),('common',common)):assert np.array_equal(m,png(C/f'{n:03}_{k}_mask.png')>0)
 assert not np.any((aft>0)&(bef==0))
 assert np.array_equal(bef,png(C/f'before_{n:03}_indices.png')) and np.array_equal(aft,png(C/f'after_{n:03}_indices.png'))
 body['before',n],body['after',n]=bef,aft
 source_rows.append({'ref':n,'registered_source':q['source_folder'],'common_masks_reconstructed':True,'old_body_copied':False})

# 기존 조사 보고에만 의존하지 않고 실제 역사 ARC의 효과를 다시 독출한다.
R=D/'shibuki_ultimate_arrival_relations01';relations=readj(R/'report.json')
assert sha(readb(R/'report.json'))==meta['source_report_sha256']
hist=Archive(readb(ROOT/meta['historical_source']))
assert sha(hist.data)==relations['historical_baseline_sha256']
target={};backgrounds={};effect_proof=[]
for n in BODIES:
 bef,aft=body['before',n],body['after',n]
 same=np.all(color(a,bef,16)==color(a,aft),axis=2)
 target[n,0]=aft.copy();target[n,5]=np.where(same,0,bef).astype(np.uint8)
 for pb in(6,7,8):assert not a.layer(n,pb)[0].any();target[n,pb]=blank()
oldmeta=readj(ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14/art.json')
original=Archive(readb(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc'))
bg=original.layer(130)[0].copy();bg[np.isin(bg,(5,8))]=14;bg=np.array(oldmeta['effect_index_mapping'],np.uint8)[bg]
assert np.array_equal(bg,npy(R/'effect_130_historical_background.npy'))
oldbody=blank();oldbody[80:240,80:240]=png(ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14/frame_133.png')
assert np.array_equal(oldbody,npy(R/'effect_130_historical_body.npy'))
pred=np.where(oldbody>0,9,bg).astype(np.uint8);pred[183,159:162]=9;assert np.array_equal(pred,a.layer(130)[0])
bg[183,159:162]=9;backgrounds[130]=bg
fx131=render(hist,131,0,parts(hist,0,131)[:16]);assert np.array_equal(fx131,npy(R/'effect_131.npy'))
assert np.array_equal(fx131,a.layer(132)[0]) and np.array_equal(np.where(a.layer(133)[0]>0,9,fx131),a.layer(131)[0]);backgrounds[131]=fx131
orb=hist.layer(129)[0];assert np.array_equal(orb,npy(R/'effect_134_orb.npy'))
assert np.array_equal(over(orb,a.layer(133)[0]),a.layer(134)[0]);backgrounds[134]=orb
for n in(130,131):
 target[n,0]=np.where(body['after',133]>0,9,backgrounds[n]).astype(np.uint8)
 for pb in PBS[1:]:target[n,pb]=blank()
for pb in PBS:target[134,pb]=target[133,pb].copy()
target[134,0]=over(orb,target[134,0])
for n in(136,137):
 ps=[q for q in parts(hist,0,n)if q['tile']==7];fx=render(hist,n,0,ps)
 assert np.count_nonzero(fx)==46 and np.array_equal(fx,npy(R/f'effect_{n}.npy'))
 assert [sig(q)for q in ps]==[sig(q)for q in meta['protected_effect_records'][str(n)]]
 assert np.array_equal(tile(hist,n,7),tile(b,n,7))
 for pb in(0,5):
  target[n,pb]=over(target[n,pb],fx)
  actual=parts(b,pb,n)
  assert [sig(q)for q in actual[-len(ps):]]==[sig(q)for q in ps]
  assert np.array_equal(render(b,n,pb,actual[-len(ps):]),fx)
 effect_proof.append({'ref':n,'historical_tile7_whole256_texels_exact':True,'records_appended_after_body_in_base_and_overlay':True,'visible_effect_pixels':46})
for n in REFS:
 for pb in PBS:
  z=target[n,pb];assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)]
  assert np.array_equal(z,png(T/f'{n:03}_bank{pb}_indices.png'))
for n,bg in backgrounds.items():
 assert np.array_equal(bg,png(T/f'{n:03}_background_indices.png'))
 ps=parts(b,0,n);prefix=next((i for i in range(1,len(ps)+1)if np.array_equal(render(b,n,0,ps[:i]),bg)),None)
 assert prefix is not None,n
 effect_proof.append({'ref':n,'entire_background_including_body_occluded_pixels_exact':True,'background_prefix_records':prefix,'background_before_body':True})

counts=collections.Counter();assert len(old)==len(new) and a.p==b.p
ae,be=psx_arc(old),psx_arc(new)
assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for q in ae:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True) and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert (ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']];counts['other_graphics_banks_byte_exact']+=1
 for f,g in zip(ab['frames'],bb['frames']):
  n=f['index'];assert n==g['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert g['tile_count']==32
  else:assert raw(a,gb,n)==raw(b,gb,n) and f['tile_count']==g['tile_count'];counts['non_target_raw_exact']+=1
for n in range(237):
 if n in RESERVED:continue
 for pb in PBS:
  want=target[n,pb]if n in REFS else a.layer(n,pb)[0]
  assert np.array_equal(b.layer(n,pb)[0],want),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 original_parts={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
 addr={q['record_offset']for n in REFS if n in original_parts and pb in PBS for q in original_parts[n]}
 for n,op in original_parts.items():
  bp=parts(b,pb,n)
  if pb in PBS and n in REFS:
   assert 0<len(bp)<=256
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0
    v=tile(b,n,t);assert not(t%16==0 and v[:,0].any());assert not(q['flip_y']and t//16==0 and v[0].any());counts['GPU_parts_checked']+=1
  else:
   assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
   overlaps=sorted(addr&{q['record_offset']for q in op})
   if overlaps:shared.append({'bank':pb,'ref':n,'old_shared_record_offsets':overlaps,'entire_semantics_exact':True})
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   assert np.array_equal(expected,np.asarray(b.composite(n,mask,arm)[0]));counts['partial_RGBA_exact']+=1
assert raw(a,0,135)==raw(b,0,135) and raw(a,0,132)==raw(b,0,132)
assert a.banks[0]['frames'][131]['offset']==a.banks[0]['frames'][132]['offset']
assert b.banks[0]['frames'][131]['offset']!=b.banks[0]['frames'][132]['offset']
nativep=H/'ultimate_arrival_partial_components_native_checks.json';native=readj(nativep);assert native['passed']
nr=native['resources']['PL02_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n)) and q['buffer_outside_and_unused_tail_preserved']

O.mkdir(exist_ok=True);sheets=[]
def board(items,name,cols,scale):
 pics=[im for _,im in items];boxes=[im.getbbox()for im in pics if im.getbbox()]
 x0=min(p[0]for p in boxes)-4;y0=min(p[1]for p in boxes)-4;x1=max(p[2]for p in boxes)+4;y1=max(p[3]for p in boxes)+4
 cw=(x1-x0)*scale+12;ch=(y1-y0)*scale+26;im=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  cx=(i%cols)*cw;cy=(i//cols)*ch;v=pic.crop((x0,y0,x1,y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST)
  im.paste(v,(cx+6,cy+22),v);dr.text((cx+6,cy+4),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':[x0,y0,x1,y1],'no_opaque_pixels_clipped':True})
for i,ns in enumerate(((130,131),(133,134),(136,137),(138,139))):
 items=[]
 for n in ns:
  for ar,mask,label in((a,15,'old before'),(b,15,'new before'),(a,0,'old after'),(b,0,'new after')):items.append((f'{n} {label}',ar.composite(n,mask)[0]))
 board(items,f'readback_{i:02}.png',4,4)
for n in(133,136,138,139):board([(f'{n} mask {m}',b.composite(n,m)[0])for m in(0,1,2,4,8,15)],f'partial_{n}.png',3,4)
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==504 and counts['target_layers_exact']==40 and counts['non_target_layers_exact']==1100 and counts['partial_RGBA_exact']==256
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'등록5자세·발/팔 공통정합→역사효과별도독출→등장8 실제40층 및비대상 독립검사',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'source_lock_sha256':sha((P/'SOURCE_LOCK.json').read_bytes()),'locked_inputs':len(lock['files']),
 'counts':dict(counts),'common_body_sources':source_rows,'effect_preservation':effect_proof,'protected_ref135_exact':True,'shared132_all_raw_layers_parts_exact':True,
 'old_shared_non_target_compositions':shared,'part_counts':{str(n):{str(pb):len(parts(b,pb,n))for pb in PBS}for n in sorted(REFS)},
 'other_entries_palette_audio_and_bank_boundaries_exact':True,'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'new8_decoded_hashes_exact':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limitations':['원화 생성 또는 최초 고정셀 재양자화는 재실행하지 않았다. 등록 파일 출처잠금·공통 부위와 국소 발/팔 합성부터 독립 재구성했다.',
 '대상256RGBA·1100비대상층/팔레트 보존이며 제작자7296 전조합 반복은 아니다. 새MIPS/게임실기/원순서 브라우저 실행은 별도다.',
 '135는 도구 거부된 편집을 우회하지 않고 부모 그대로 보존했다. 등장 전체완료나 사용자 수용을 뜻하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))
