"""작은 기본/포스 머리19 최종 ARC 독립 판독. 제작 함수 미호출."""
from pathlib import Path
import collections,hashlib,io,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas
O=Path(__file__).resolve().parent;W=ROOT/'work/sprite_style_unification_20261107';H=W/'shibuki_audit'
P=H/'prepared_vehicle_head_base01';T=H/'vehicle_head_base_targets01'
assert not (O/'report.json').exists()
REFS=set(range(184,204))-{198};PBS=(0,5,6,7,8);RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();tracked={};counts=collections.Counter()
def rel(p):return p.relative_to(ROOT).as_posix()
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):return np.array(Image.open(io.BytesIO(blob(p))))
rawcache={}
def raw(ar,gb,n):
 f=ar.banks[gb]['frames'][n];key=(id(ar),f['offset'],f['tile_count'])
 if key not in rawcache:rawcache[key]=decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
 return rawcache[key]
def cp(ar,pb,n):return composition_frame(ar.c,pb,n)
def parts(ar,pb,n):return cp(ar,pb,n)['parts']
def records(ar,pb,n):return b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in parts(ar,pb,n))
def tile(ar,n,t):
 f=ar.banks[0]['frames'][n];z=np.frombuffer(indexed_atlas(raw(ar,0,n),f['tile_count'])[0],np.uint8).reshape(-1,256)
 return z[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
def compose(ar,ll,mask,arm):
 im=ar.rgba(ll[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(ar.rgba(ll[pb],32 if pb==7 and arm==2 else 16))
 return np.array(im)
oldp=H/'prepared_nova_strike_base01/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=blob(oldp),blob(newp);assert sha(old)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
assert sha(new)=='4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'
a,b=Archive(old),Archive(new)
lock=js(P/'INPUT_LOCK.json');assert tracked[rel(P/'INPUT_LOCK.json')]=='2a205d1ef39c504c07986e272373370dd1eee3a4563e5ff2eb0f09bb871ee5a4'
assert len(lock['files'])==192 and lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)
for p,h in lock['files'].items():assert sha(blob(ROOT/p))==h,p
prepared=js(P/'PREPARED_LOCK.json')
for p,h in prepared['files'].items():assert sha(blob(P/p))==h,p
for p,h in prepared['source_scripts'].items():assert sha(blob(H/p))==h,p
sourcep=W/'nana_audit/shibuki_vehicle_head_base_semantic_read01/report.json'
source=js(sourcep);assert sha(sourcep.read_bytes())=='abc7753ce406a8509cc7a31f44d339125591a07b6127916d8c86e601c0845449'
assert source['passed']and source['source_parent_sha256']==sha(old)
for p,h in source['inputs'].items():assert sha(blob(ROOT/p))==h,p
meta=js(T/'manifest.json');assert sha((T/'manifest.json').read_bytes())==lock['target_manifest_sha256']
assert set(meta['refs'])==REFS and meta['source_geometry_parent_sha256']==sha(old)
for p,h in meta['source_files'].items():assert sha(blob(ROOT/p))==h,p
masters={pb:png(H/f'vehicle_head_base_native02/184_bank{pb}_indices.png')for pb in(0,5)}
targets={};translations=[];origin=a.composite(184,0)[0].getbbox();md={r['ref']:r for r in meta['translations']}
for n in sorted(REFS):
 bb=a.composite(n,0)[0].getbbox();dx,dy=bb[0]-origin[0],bb[1]-origin[1]
 assert [dx,dy]==md[n]['translation_from184'];ll={}
 for pb in PBS:
  z=png(T/f'{n:03}_bank{pb}_indices.png');assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16
  assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)]
  if pb in(0,5):
   expected=np.zeros_like(z);ys,xs=np.nonzero(masters[pb]);expected[ys+dy,xs+dx]=masters[pb][ys,xs];assert np.array_equal(z,expected)
  else:assert not z.any()and np.array_equal(z,a.layer(n,pb)[0])
  ll[pb]=z
 assert (ll[0]>0).sum()==144 and (ll[5]>0).sum()==39 and ll[0][135+dy,156+dx]==7 and ll[5][135+dy,156+dx]==0
 for form,mask in(('base',0),('fourth',15)):
  expected=compose(a,ll,mask,1)
  assert np.array_equal(expected,png(T/f'{form}_{n:03}.png'))
  assert np.array_equal(expected[:,:,3],np.array(a.composite(n,mask)[0])[:,:,3])
 targets[n]=ll;translations.append({'ref':n,'from184':[dx,dy],'bbox_world':[v-160 for v in bb],'opaque':144,'head5':39})
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne]
allowed=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allowed[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allowed)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
co=bank_offsets(a.c);assert co==bank_offsets(b.c)
for pb,st in enumerate(co):
 en=co[pb+1]if pb+1<len(co)else len(a.c)
 if pb not in(0,5):assert a.c[st:en]==b.c[st:en]
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for f,nf in zip(ab['frames'],bb['frames']):
  n=f['index'];assert n==nf['index'];counts['raw']+=1
  if gb==0 and n in REFS:assert nf['tile_count']==4
  else:
   assert raw(a,gb,n)==raw(b,gb,n)and f['tile_count']==nf['tile_count'];counts['non_target_raw']+=1
   excluded=REFS if gb==0 else set()
   og={q['index']for q in ab['frames']if q['offset']==f['offset']}-excluded
   ng={q['index']for q in bb['frames']if q['offset']==nf['offset']}-excluded
   assert og==ng
group={q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][184]['offset']};assert group==REFS
for n in REFS:
 assert raw(b,0,n)==raw(b,0,184)
 assert not tile(b,n,0).any()and not tile(b,n,2).any()
 assert (tile(b,n,1)>0).sum()==144 and (tile(b,n,3)>0).sum()==39
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:z=b.layer(n,pb)[0]
   except(ValueError,IndexError)as e:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as prior:assert(type(e),str(e))==(type(prior),str(prior))
    else:raise AssertionError('new reserved exception')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(z,a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],targets[n][pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers'if n in REFS else'non_target_layers']+=1
users=collections.defaultdict(set);blank=[];spans=[];non_target_relocated=[]
for pb,st in enumerate(co):
 frame_count=cp(a,pb,0)['bank_frame_count'];assert cp(b,pb,0)['bank_frame_count']==frame_count
 for n in range(frame_count):
  ac,bc=cp(a,pb,n),cp(b,pb,n);ap,bp=ac['parts'],bc['parts']
  for p in bp:users[p['record_offset']].add((pb,n))
  if pb in(0,5)and n in REFS:
   dx,dy=md[n]['translation_from184'];assert records(b,pb,n)==struct.pack('<BBbb',0,1 if pb==0 else 3,-10+dx,-37+dy);counts['owner_layers']+=1
  else:
   assert records(a,pb,n)==records(b,pb,n),(pb,n);counts['non_target_compositions']+=1
   if [p['record_offset']for p in ap]!=[p['record_offset']for p in bp]:non_target_relocated.append([pb,n])
  if pb==5 and bp:spans.append({'ref':n,'start':bp[0]['record_offset'],'end':bp[-1]['record_offset']+4,'sequence_sha256':sha(records(b,pb,n))})
  if n in REFS and pb in PBS:
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<4 and p['unknown_flags']==0;tex=tile(b,n,t)
    assert not(t%16==0 and tex[:,0].any())and not(p['flip_y']and t//16==0 and tex[0].any());counts['GPU_parts']+=1
   if pb in(6,7,8):
    assert ac==bc and all(not tile(b,n,p['tile']+p['page']*256).any()for p in bp)
    counts['empty678_offset_exact']+=1;blank.append({'ref':n,'bank':pb,'records':bp})
target_external=[]
for n in sorted(REFS):
 for pb in(0,5):
  for p in parts(b,pb,n):
   ext=[list(v)for v in sorted(users[p['record_offset']])if not(v[0]in(0,5)and v[1]in REFS)]
   if ext:target_external.append({'ref':n,'bank':pb,'record_offset':p['record_offset'],'other_users':ext})
# 접두/접미 저장이 겹치는 실제구간을 읽는다. 의미기록의 내용/순서는 위에서 전수 대조했다.
unique={}
for r in spans:unique.setdefault((r['start'],r['end']),[]).append(r['ref'])
proper_overlaps=[]
for (s1,e1),rr1 in unique.items():
 for (s2,e2),rr2 in unique.items():
  if s1<s2<e1<e2:
   assert(e1-s2)%4==0
   proper_overlaps.append({'left_refs':rr1,'right_refs':rr2,'shared_records':(e1-s2)//4,'byte_range':[s2,e1],'shared_sha256':sha(b.c[s2:e1])})
head_end=co[6];head_used=max(e for s,e in unique);assert head_end-head_used==12
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   im=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(im,compose(a,targets[n],mask,arm))
   assert np.array_equal(im,np.array(b.composite(n,mask&1)[0]));counts['partial_RGBA']+=1
assert raw(a,0,198)==raw(b,0,198)
preserve198=[]
for pb in PBS:
 assert np.array_equal(a.layer(198,pb)[0],b.layer(198,pb)[0])and records(a,pb,198)==records(b,pb,198)
 preserve198.append({'bank':pb,'semantic_record_bytes_exact':True,'records_offsets_exact':parts(a,pb,198)==parts(b,pb,198)})
for mask in range(16):
 for arm in(1,2):assert not np.array(b.composite(198,mask,arm)[0])[:,:,3].any()
nativep=H/'vehicle_head_base_components_native_checks.json';native=js(nativep);nr=native['resources']['PL00_U.ARC']
assert native['passed']and nr['candidate_sha256']==sha(new)and nr['GPU_part_edge_checks']==95
native_refs=[]
for bank in nr['banks']:
 for row in bank['native_decoder_checks']:
  n=row['frame'];assert row['decoded_sha256']==sha(raw(b,bank['bank'],n))and row['bytes']==512 and row['buffer_outside_and_unused_tail_preserved'];native_refs.append(n)
assert set(native_refs)==REFS
js(W/'zero_audit/shibuki_vehicle_head_ownership01/conclusions.json')
post=js(P/'post_lock_evidence.json')
for p,h in post['evidence'].items():assert sha(blob(ROOT/p))==h,p
expected={'raw':508,'non_target_raw':489,'target_layers':95,'non_target_layers':1045,'owner_layers':38,'non_target_compositions':1749,'empty678_offset_exact':57,'GPU_parts':95,'partial_RGBA':608}
assert dict(counts)==expected,counts
sheets=[]
for form,mask in(('base',0),('fourth',15)):
 for page in(0,1):
  sheet=Image.new('RGB',(1100,440),'#e9e6df');dr=ImageDraw.Draw(sheet)
  for i,n in enumerate(sorted(REFS)[page*10:page*10+10]):
   x=i%5*220;y=i//5*220;bb=b.composite(n,mask)[0].getbbox();crop=(bb[0]-3,bb[1]-3,bb[2]+3,bb[3]+3)
   dr.text((x+4,y+4),f'{n} {form}: old / new',fill='black')
   for col,ar in enumerate((a,b)):
    im=ar.composite(n,mask)[0].crop(crop);up=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST)
    sheet.paste(up,(x+col*108+3,y+25),up);sheet.paste(im,(x+col*108+10,y+148),im)
   dr.text((x+4,y+190),str([v-160 for v in bb]),fill='black')
  p=O/f'{form}_{page:02}.png';sheet.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'scale':[1,5]})
for n in(184,196):
 sheet=Image.new('RGB',(600,600),'#253144');dr=ImageDraw.Draw(sheet);bb=b.composite(n,0)[0].getbbox();crop=(bb[0]-3,bb[1]-3,bb[2]+3,bb[3]+3)
 for mask in range(16):
  x=mask%4*150;y=mask//4*150;im=b.composite(n,mask)[0].crop(crop);up=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST)
  sheet.paste(up,(x+15,y+25),up);dr.text((x+4,y+4),f'{n} mask {mask}',fill='white')
 p=O/f'partial_{n}.png';sheet.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'scale':5})
for p in(Path(__file__),ROOT/'scripts/export_x_consistency.py',ROOT/'src/psx_player.py'):blob(p)
for forbidden in('pack_vehicle_head_base','repack_part_records_lossless','native_pose_pack','register_vehicle_head_base','register_vehicle_head_base_semantic','prepare_vehicle_head_base_targets'):assert forbidden not in sys.modules
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'기본/포스 작은머리19 최종ARC 재독출/95층·부분608·공유와비대상 검증. 원화 재양자화는 기존 독립abc7753c를 불변해시로 결속.',
 'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':tracked[rel(P/'INPUT_LOCK.json')],'locked_files':192,'counts':dict(counts),
 'source_reconstruction':{'path':rel(sourcep),'sha256':sha(sourcep.read_bytes()),'source_inputs_unchanged':True,'new_master0_and5_reused':True},
 'translations':translations,'raw_stream':{'refs':sorted(group),'tiles':4,'bytes':512,'sha256':sha(raw(b,0,184)),'blank_tiles':[0,2],'body_tile':1,'head5_tile':3},
 'selected_empty678_offset_proofs':blank,'ref198':{'raw_and_layers_exact':True,'all32_blank':True,'compositions':preserve198},
 'record_storage':{'all_non_target_ordered_4byte_sequences_exact':True,'non_target_relocated_count':len(non_target_relocated),'non_target_relocated_refs':non_target_relocated,'actual_head5_partial_overlaps':proper_overlaps,'head5_tail_slack_bytes':head_end-head_used,'target_records_shared_with_external':target_external},
 'other_entries_palette_sound_exact':True,'bank_boundaries_exact':True,'other_composition_banks_except0and5_entire_bytes_exact':True,'non_target_raw_alias_groups_excluding_targets_exact':True,
 'native_binding':{'path':rel(nativep),'sha256':tracked[rel(nativep)],'candidate_and19_decoded_hashes_match':True,'refs':native_refs,'new_execution':False},
 'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'source_or_resource_modified':False,
 'limits':['현재Shibuki19동형과위치의보존이며원US5/6고유머리복원이아님','95GPU는정적경계검사;원MIPS19는기존실행의후보·decoded해시결속','원화직접재양자화는이전abc7753c 독립기록을재사용하며이번중복실행아님','최종조종석/원표실행/실기미실행']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'report':sha((O/'report.json').read_bytes()),'counts':dict(counts),'head5_overlap_pairs':len(proper_overlaps),'head5_slack':head_end-head_used,'target_external':len(target_external),'ref198':preserve198,'sheets':len(sheets)},ensure_ascii=False))
