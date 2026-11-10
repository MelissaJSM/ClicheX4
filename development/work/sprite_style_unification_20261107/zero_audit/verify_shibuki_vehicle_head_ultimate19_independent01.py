"""작은 차량머리19의 고정목표→실제 ARC와 공유·빈층을 독립으로 읽는다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit'
P=H/'prepared_vehicle_head_ultimate01';T=H/'vehicle_head_ultimate_targets01';O=D/'shibuki_vehicle_head_ultimate19_independent01'
assert not O.exists()
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
REFS=set(range(184,204))-{198};PBS=(0,5,6,7,8);RESERVED={105,*range(175,183)}
hb=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=hb(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def compose(ls,mask,arm=1):
 out=color(a,ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   v=color(a,ls[pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;out[m]=v[m]
 return out
oldp=H/'prepared_hover_ultimate01/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert hb(old)=='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
assert hb(new)=='a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024'
lock=js(P/'INPUT_LOCK.json');assert len(lock['files'])==188 and hb(blob(P/'INPUT_LOCK.json'))=='9af12e9e1af6150475331e930ef7d5c3aec2dc2d36876558dd710788a8418a8f'
assert lock['candidate_sha256']==hb(new) and lock['parent_sha256']==hb(old)
for p,h in lock['files'].items():assert hb(blob(R/p))==h,p
prep=js(P/'PREPARED_LOCK.json')
for p,h in prep['files'].items():assert hb(blob(P/p))==h,p
for p,h in prep['source_scripts'].items():assert hb(blob(H/p))==h,p
meta=js(T/'manifest.json');assert hb(blob(T/'manifest.json'))==lock['target_manifest_sha256']
assert set(meta['refs'])==REFS and meta['parent_sha256']==hb(old)
for p,h in meta['source_files'].items():assert hb(blob(R/p))==h,p
targets={};translations=[];nb={pb:png(H/f'vehicle_head_ultimate_native02/184_bank{pb}_indices.png')for pb in(0,5)}
bb=a.composite(184,0)[0].getbbox();delta_rows={q['ref']:q for q in meta['translations']}
for n in sorted(REFS):
 box=a.composite(n,0)[0].getbbox();dx,dy=box[0]-bb[0],box[1]-bb[1];assert [dx,dy]==delta_rows[n]['translation_from184']
 ll={}
 for pb in PBS:
  z=png(T/f'{n:03}_bank{pb}_indices.png');assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16
  assert hb(z.tobytes())==meta['targets'][str(n)][str(pb)]
  if pb in(0,5):
   expected=np.zeros_like(z);ys,xs=np.nonzero(nb[pb]);expected[ys+dy,xs+dx]=nb[pb][ys,xs];assert np.array_equal(z,expected)
  else:assert not z.any()and np.array_equal(z,a.layer(n,pb)[0])
  ll[pb]=z
 assert int((ll[0]>0).sum())==144 and int((ll[5]>0).sum())==8 and ll[0][135+dy,156+dx]==7
 oa=np.array(a.composite(n,0)[0])[:,:,3]>0;na=ll[0]>0
 assert int((na&~oa).sum())==int((oa&~na).sum())==1
 assert Image.fromarray(compose(ll,0)).getbbox()==box
 for form,mask in(('before',15),('after',0)):
  assert np.array_equal(compose(ll,mask),png(T/f'{form}_{n:03}.png'))
 targets[n]=ll;translations.append({'ref':n,'world_translation_from184':[dx,dy],'bbox':[v-160 for v in box],'opaque':144,'side_overlay':8,'alpha_added':1,'alpha_removed':1})
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
abanks,bbanks=bank_offsets(a.c),bank_offsets(b.c)
for pb,start in enumerate(abanks):
 if pb not in(0,5):
  end=abanks[pb+1]if pb+1<len(abanks)else len(a.c);assert a.c[start:end]==b.c[start:end]
for gb,(aa,ba)in enumerate(zip(a.banks,b.banks)):
 assert (aa['base'],aa['end'],len(aa['frames']))==(ba['base'],ba['end'],len(ba['frames']))
 if gb:assert a.g[aa['base']:aa['end']]==b.g[ba['base']:ba['end']]
 for af,bf in zip(aa['frames'],ba['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert bf['tile_count']==5
  else:
   assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
   og={q['index']for q in aa['frames']if q['offset']==af['offset']};ng={q['index']for q in ba['frames']if q['offset']==bf['offset']}
   excluded=REFS if gb==0 else set();assert og-excluded==ng-excluded
newgroup={q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][184]['offset']};assert newgroup==REFS
for n in REFS:
 assert raw(b,0,n)==raw(b,0,184)
 for t in(0,2,3):assert not tile(b,n,t).any()
 assert tile(b,n,1).shape==(16,16) and int((tile(b,n,1)>0).sum())==144 and int((tile(b,n,4)>0).sum())==8
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:z=b.layer(n,pb)[0]
   except(ValueError,IndexError)as e:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as e2:assert(type(e),str(e))==(type(e2),str(e2))
    else:raise AssertionError('new invalid reserved')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(z,a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],targets[n][pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
composition_users=collections.defaultdict(set);blank_proofs=[]
for pb in range(len(abanks)):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  ap,bp=parts(a,pb,n),parts(b,pb,n)
  for p in bp:composition_users[p['record_offset']].add((pb,n))
  if pb in(0,5)and n in REFS:assert len(bp)==1;counts['new_owner_layers']+=1
  else:
   assert [sig(q)for q in ap]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
  if n in REFS and pb in PBS:
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<5 and p['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(p['flip_y']and t//16==0 and z[0].any());counts['GPU_parts']+=1
   if pb in(6,7,8):
    assert ap==bp and all(not tile(b,n,p['tile']+p['page']*256).any()for p in bp)
    counts['selected_blank_records_exact']+=1;blank_proofs.append({'ref':n,'bank':pb,'records':bp})
outside=[]
for n in sorted(REFS):
 for pb in(0,5):
  for p in parts(b,pb,n):
   users=composition_users[p['record_offset']];external=[list(v)for v in sorted(users)if not(v[0]in(0,5)and v[1]in REFS)]
   if external:outside.append({'ref':n,'bank':pb,'external':external})
assert not outside
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,compose(targets[n],mask,arm))
   assert np.array_equal(actual,np.array(b.composite(n,mask&1)[0]));counts['partial_RGBA_exact']+=1
assert raw(a,0,198)==raw(b,0,198)
for pb in PBS:assert np.array_equal(a.layer(198,pb)[0],b.layer(198,pb)[0])and[sig(p)for p in parts(a,pb,198)]==[sig(p)for p in parts(b,pb,198)]
for mask in range(16):
 for arm in(1,2):assert not np.array(b.composite(198,mask,arm)[0])[:,:,3].any()
native=js(H/'vehicle_head_ultimate_components_native_checks.json');nr=native['resources']['PL02_U.ARC'];assert native['passed']and nr['candidate_sha256']==hb(new)and nr['GPU_part_edge_checks']==95
native_refs=[]
for bank in nr['banks']:
 for row in bank['native_decoder_checks']:
  n=row['frame'];assert row['decoded_sha256']==hb(raw(b,bank['bank'],n))and row['bytes']==640 and row['buffer_outside_and_unused_tail_preserved'];native_refs.append(n)
assert set(native_refs)==REFS
ver=js(P/'verification.json');assert ver['candidate_sha256']==hb(new)
post=js(P/'post_lock_evidence.json')
for p,h in post['evidence'].items():assert hb(blob(R/p))==h,p
assert[counts[k]for k in('raw_checked','non_target_raw_exact','target_layers_exact','non_target_layers_exact','new_owner_layers','non_target_compositions_exact','selected_blank_records_exact','GPU_parts','partial_RGBA_exact')]==[512,493,95,1045,38,1753,57,95,608],counts
O.mkdir(exist_ok=False);sheets=[]
for form,mask in(('before',15),('after',0)):
 for page in(0,1):
  refs=sorted(REFS)[page*10:page*10+10];out=Image.new('RGB',(5*220,2*224),'#e6e3db');dr=ImageDraw.Draw(out)
  for i,n in enumerate(refs):
   x=i%5*220;y=i//5*224;bb=b.composite(n,mask)[0].getbbox();crop=(bb[0]-3,bb[1]-3,bb[2]+3,bb[3]+3)
   dr.text((x+4,y+4),f'{n} {form}: parent / new',fill='black')
   for col,ar in enumerate((a,b)):
    im=ar.composite(n,mask)[0].crop(crop);up=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST);out.paste(up,(x+col*108+3,y+25),up);out.paste(im,(x+col*108+10,y+148),im)
   dr.text((x+4,y+190),str([v-160 for v in bb]),fill='black')
  p=O/f'{form}_{page:02}.png';out.save(p);sheets.append({'path':rel(p),'sha256':hb(p.read_bytes()),'scale':[1,5],'normalized_display':'原world原点は行のbboxで保持。比較表示は各ref親子共通crop。'})
for n in(184,196):
 out=Image.new('RGB',(4*150,4*150),'#263345');dr=ImageDraw.Draw(out);bb=b.composite(n,0)[0].getbbox();crop=(bb[0]-3,bb[1]-3,bb[2]+3,bb[3]+3)
 for mask in range(16):
  x=mask%4*150;y=mask//4*150;im=b.composite(n,mask)[0].crop(crop);up=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST);out.paste(up,(x+15,y+25),up);dr.text((x+5,y+4),f'{n} mask {mask:02}',fill='white')
 p=O/f'partial_{n}.png';out.save(p);sheets.append({'path':rel(p),'sha256':hb(p.read_bytes()),'scale':5,'diagnostic_masks':list(range(16))})
for p in(Path(__file__),R/'scripts/export_x_consistency.py',R/'src/psx_player.py',D/'verify_shibuki_ultimate_hurt13_independent.py'):blob(p)
for p,h in tracked.items():assert hb((R/p).read_bytes())==h,p
report={'passed':True,'scope':'Shibuki Ultimate 작은차량머리19 고정등록→95목표층·ARC·비대상·빈프레임·공유·부분GPU 독립 읽기','candidate':rel(newp),'candidate_sha256':hb(new),'parent_sha256':hb(old),'counts':dict(counts),'translations':translations,'source_reconstruction':'동료 별도 직접 재양자화 결과를 최종 결속. 여기서는 native02 등록2층→19평행이동38층 및 빈57층을 독립 재계산했다.','new_shared_raw':{'refs':sorted(newgroup),'tiles':5,'sha256':hb(raw(b,0,184)),'whole_blank_tiles':[0,2,3],'base_tile':1,'overlay_tile':4},'ref198_raw_layers_compositions_all32blank_preserved':True,'selected_empty678_proofs':blank_proofs,'new_records_external_owners':outside,'non_target_raw_aliases_without_selected_preserved':True,'other_composition_banks_entire_bytes_exact':True,'target_part_policy':'부모의 중복5층 기록은 한 새정확기록으로 대체. 타깃38층만 레코드 변경 허용하며 선택빈57층은 offset을 포함한 records exact.','partial_dependence':'608조합은 head bit1만 영향을 주며 arm variant1/2는 동일. 실제Ultimate 전후 마스크는 별도 caller 보고에 결속.','native_author_report_bound':{'path':rel(H/'vehicle_head_ultimate_components_native_checks.json'),'sha256':hb((H/'vehicle_head_ultimate_components_native_checks.json').read_bytes()),'native_refs':native_refs,'raw_hashes_match':True},'new_MIPS_execution':False,'reserved_layers':reserved,'entry_boundaries_palette_audio_other_entries_exact':True,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'source_or_resource_modified':False,'runtime_verified':False,'limits':['현재19동형은 수용된Shibuki 정책이다. 원US의5/6개RGBA크롭을 복원했다고 주장하지 않는다.','새머리의13×15/144px·원점·홍채는 부모와 같지만 귀사이 외곽1추가1제거가 있어 alpha exact가 아니다.','원화 직접 재양자화는 별도 독립 결과로 구분한다.','95GPU는 읽기 경계검사이고 기존 원MIPS19는 제작자실행 해시결속이다. 이번 새MIPS/게임실기/실제조종석 접점 실행은 없다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'report_sha256':hb((O/'report.json').read_bytes()),'counts':dict(counts),'sheets':len(sheets)}))
