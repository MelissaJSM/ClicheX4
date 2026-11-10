"""고정 PL00 호버10의50층과 저장전용16참조를 제작모듈 없이 검증한다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';H=W/'shibuki_audit';P=S/'packed_hover_candidate03';O=D/'shibuki_base_hover10_independent01';assert not O.exists();sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,composition_frame
from src.psx_ui_atlas import local_composition,tile_pixels
from src.psx_static_effect import compose_static
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
sha=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};C=collections.Counter();PBS=(0,5,6,7,8);REFS=set(range(221,231));STORAGE={39,40,41,42,43,44,49,50,59,60,61,62,65,66,79,80};CHANGED=REFS|STORAGE
def blob(p):v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def comp(ls,mask,arm=1):
 z=color(a,ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:q=color(a,ls[pb],32 if pb==7 and arm==2 else 16);m=q[:,:,3]>0;z[m]=q[m]
 return z
parent=H/'prepared_vehicle_head_base01/PL00_U.ARC';old,new=blob(parent),blob(P/'PL00_U.ARC');a,b=Archive(old),Archive(new)
assert sha(old)=='4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'and sha(new)=='8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397'
ver=js(P/'verification.json');assert ver['parent_sha256']==sha(old)and ver['after']==sha(new)and set(ver['storage_only_refs'])==STORAGE
lock=js(S/'packed_hover_shared_optimized02/input_lock.json');targets={}
source_evidence={}
for name,expect in(('shibuki_base_hover_layers03_read01','c7881481e4201f94195a88c0d0c3a27ad8d9d366e4bf961c56c77204aa1ac3db'),('shibuki_base_hover_shots01','e2f40514987e3ff724c08edf2f5d709ca2daff227b9b5e31ff7c4a12059da5d9'),('shibuki_base_hover_shots02_delta01','6fad6d57a6c120655a91d08473d4ec6550078c70a8e9912694430c63229be6d2')):
 p=D/name/'READER_LOCK.json';m=js(p);assert sha(blob(p))==expect
 for q,h in m['files'].items():assert sha((R/q).read_bytes())==h,q
 source_evidence[name]={'lock_path':rel(p),'lock_sha256':expect,'report':js(D/name/'report.json')['scope']}
 for filename in('report.json','visual_review.json','conclusions.json'):blob(D/name/filename)
geom=Archive(blob(H/'prepared_nova_strike_base01/PL00_U.ARC'));assert sha(geom.data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'and geom.p==a.p
for n in sorted(REFS):
 ls={}
 for pb in PBS:
  q=lock['sources'][str(n)][str(pb)];p=R/q['path'];assert sha(blob(p))==q['sha256'];z=png(p)
  expected=S/(f'body_layers_probe04/layer{pb}_{n}.png'if n%2 else f'shot_composed02/layer{pb}_{n}.png');assert p.resolve()==expected.resolve()
  assert sha(z.tobytes())==lock['targets'][str(n)][str(pb)]and z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16
  assert np.array_equal(a.layer(n,pb)[0],geom.layer(n,pb)[0]);ls[pb]=z;C['parent_rebase_layers_exact']+=1
 targets[n]=ls
 if n%2==0:assert np.array_equal(ls[8],targets[n-1][8])
oe,ne=psx_arc(old),psx_arc(new);assert len(old)==len(new)and[(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
groups=[]
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];C['raw_checked']+=1
  if gb==0 and n in CHANGED:assert bf['tile_count']==32
  else:assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];C['nonselected_raw_exact']+=1
  og={f['index']for f in ab['frames']if f['offset']==af['offset']};ng={f['index']for f in bb['frames']if f['offset']==bf['offset']}
  assert og==ng,(gb,n,og,ng)
  if gb==0 and n in CHANGED:assert og<=CHANGED
for n in range(221,231,2):
 owners=[f['index']for f in b.banks[0]['frames']if f['offset']==b.banks[0]['frames'][n]['offset']];assert owners==[n,n+1]
 g=next(x for x in ver['target_groups']if x['refs']==[n,n+1]);recipe=js(R/g['recipe']);rawpath=(R/g['recipe']).with_suffix('.raw');assert sha(blob(rawpath))==g['raw_sha256']and sha(raw(b,0,n))==g['raw_sha256']
 assert sha(blob(R/g['recipe']))==g['recipe_sha256'];assert raw(b,0,n)==raw(b,0,n+1)
 for j,ref in enumerate((n,n+1)):
  for pb,rr in zip(PBS,recipe['assignments'][j*5:j*5+5]):assert[sig(p)for p in parts(b,pb,ref)]==[(fl,t,x-80,y-80)for t,x,y,fl in rr]
 groups.append({'refs':owners,'tile_count':32,'raw_sha256':g['raw_sha256'],'recipe':g['recipe']})
mapping={};storage_rows=[]
for q in ver['storage_proofs']:
 ns=q['refs'];assert set(ns)<=STORAGE;mp={int(k):int(v)for k,v in q['mapping'].items()};assert set(mp)==set(range(32))and set(mp.values())==set(range(32));assert mp[0]==0 and mp[16]==16
 for fixed in q['optimization']['fixed_tiles']:assert mp[fixed]==fixed
 for n in ns:
  assert sha(raw(a,0,n))==q['source_raw_sha256']and sha(raw(b,0,n))==q['optimized_raw_sha256']
  for t in range(32):assert np.array_equal(tile(a,n,t),tile(b,n,mp[t])),(n,t);C['whole_tile_inverse_exact']+=1
  mapping[n]=mp
 storage_rows.append({'refs':ns,'mapping':mp,'all32_full_tiles_exact':True,'fixed_tiles':q['optimization']['fixed_tiles'],'source_raw_sha256':q['source_raw_sha256'],'new_raw_sha256':q['optimized_raw_sha256']})
assert set(mapping)==STORAGE
reserved=[]
for n in range(237):
 for pb in PBS:
  try:z=a.layer(n,pb)[0]
  except(ValueError,IndexError)as e:
   assert n not in CHANGED
   try:b.layer(n,pb)
   except(ValueError,IndexError)as e2:assert(type(e),str(e))==(type(e2),str(e2))
   else:raise AssertionError('reserved validity changed')
   reserved.append([n,pb,str(e)]);continue
  assert np.array_equal(b.layer(n,pb)[0],targets[n][pb]if n in REFS else z),(n,pb);C['target_layers_exact'if n in REFS else'nonart_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  oldparts,newparts=parts(a,pb,n),parts(b,pb,n);C['composition_refs_checked']+=1
  if n in STORAGE and pb in PBS:
   assert[sig(p)for p in newparts]==[(p['flags'],mapping[n][p['tile']],p['x'],p['y'])for p in oldparts];C['storage_composition_refs_mapped']+=1
  elif not(n in REFS and pb in PBS):assert[sig(p)for p in oldparts]==[sig(p)for p in newparts];C['other_composition_refs_exact']+=1
  if n in CHANGED and pb in PBS:
   for p in newparts:
    t=p['tile']+p['page']*256;assert t<32 and p['unknown_flags']==0;z=tile(b,n,t);assert not(t%16==0 and z[:,0].any())and not(p['flip_y']and t//16==0 and z[0].any());C['GPU_parts']+=1
guard_checks=[]
for n in sorted(CHANGED):
 if n in REFS and n%2==0:
  guard=png(S/f'shot_inputs01/{n}_gun_guard.png')>0;gun=png(S/f'shot_inputs01/{n}_gun_indices.png');assert int(guard.sum())==71 and int((gun>0).sum())==60
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);expected=comp(targets[n],mask,arm)if n in REFS else np.array(a.composite(n,mask,arm)[0]);assert np.array_equal(actual,expected);C['partial_RGBA_exact']+=1
   if n in REFS and mask>=8:assert int(label(actual[:,:,3]>0,np.ones((3,3)))[1])==1;C['actual_leg_masks_single_component']+=1
   if n in REFS and n%2==0:assert np.array_equal(actual[guard],color(a,gun)[guard]);C['canonical_guard_RGBA_exact']+=1
# 작은머리19와원표에포함된빈198을별도로증명한다.다른레코드와저장offset은리패킹으로달라도의미값은보존한다.
head_rows=[]
for n in range(184,204):
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0])and[sig(p)for p in parts(a,pb,n)]==[sig(p)for p in parts(b,pb,n)]
 offsets_changed=sum([p['record_offset']for p in parts(a,pb,n)]!=[p['record_offset']for p in parts(b,pb,n)]for pb in PBS)
 for mask in range(16):
  for arm in(1,2):
   x,y=a.composite(n,mask,arm)[0],b.composite(n,mask,arm)[0];assert x.tobytes()==y.tobytes()
   if n==198:assert y.getbbox()is None
 head_rows.append({'ref':n,'raw_5layers_semantic_records_all32RGBA_exact':True,'composition_pointer_offsets_changed_layers':offsets_changed})
proof=js(D/'shibuki_base_hover_ownership01/report.json');assert sha(blob(D/'shibuki_base_hover_ownership01/report.json'))=='4a09339f0f6e270c89d75963c9676b38fdc896abe51abd4ecb8bb302fe5191af'
def static(ar,pb,n):
 c=composition_frame(ar.c,pb,n);px,size,bb,_=compose_static(entry(ar.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8)
 if len(px):z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 return z,c
for q in proof['jets']['frames']:
 n=q['frame'];z,c=static(b,12,n);oldz,oldc=static(a,12,n);p=D/f'shibuki_base_hover_ownership01/jet_{n:02}.npy';blob(p);assert np.array_equal(z,np.load(p))and np.array_equal(z,oldz)and[sig(x)for x in c['parts']]==[sig(x)for x in oldc['parts']]
 for t in q['tiles']:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(b.data,0x10206),t)
 C['original_jets_exact']+=1
for q in proof['lemon7']:
 n=q['step'][3];z,c=static(b,1,n);oz,oc=static(a,1,n);assert np.array_equal(z,oz)and[sig(p)for p in c['parts']]==[sig(p)for p in oc['parts']]
 for t in q['tiles']:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(b.data,0x10206),t)
 C['original_bullet_steps_exact']+=1
assert[C[k]for k in('raw_checked','nonselected_raw_exact','whole_tile_inverse_exact','target_layers_exact','nonart_layers_exact','composition_refs_checked','storage_composition_refs_mapped','other_composition_refs_exact','GPU_parts','partial_RGBA_exact','actual_leg_masks_single_component','canonical_guard_RGBA_exact')]==[508,482,512,50,1090,1787,80,1657,411,832,160,160],C
O.mkdir(exist_ok=False);sheets=[]
for n in range(221,231,2):
 crop=(124,126,185,192);out=Image.new('RGB',(4*310,4*355),'#c5cfd5');dr=ImageDraw.Draw(out)
 for row,(ref,mask,arm)in enumerate(((n,8,1),(n,15,1),(n+1,8,1),(n+1,15,1))):
  for col,(caption,im)in enumerate((('parent',a.composite(ref,mask,arm)[0]),('source50',Image.fromarray(comp(targets[ref],mask,arm))),('packed',b.composite(ref,mask,arm)[0]),('mask11 arm2',b.composite(ref,11,2)[0]))):
   dr.text((col*310+3,row*355+3),f'{ref} m{mask} {caption}',fill='black');pic=im.crop(crop).resize((305,330),Image.Resampling.NEAREST);out.paste(pic,(col*310+2,row*355+22),pic)
 p=O/f'readback_pair_{n}.png';out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'scale':5,'crop_world':[v-160 for v in crop]})
for p in(Path(__file__),R/'scripts/export_x_consistency.py',R/'src/psx_player.py',D/'verify_shibuki_ultimate_hurt13_independent.py',S/'pack_hover03.py'):blob(p)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'passed':True,'scope':'Shibuki PL00 기본/포스호버10 최종50층·저장전용16참조·부모작은머리보존 독립읽기','candidate':rel(P/'PL00_U.ARC'),'candidate_sha256':sha(new),'parent_sha256':sha(old),'source_geometry_parent_sha256':sha(geom.data),'counts':dict(C),'source_evidence_reused':source_evidence,'source50_and_palette_parent_rebase_exact':True,'target_stream_groups':groups,'storage_permutations':storage_rows,'small_heads_and_blank198':head_rows,'entry_bank_boundaries_palette_sound_other_entries_exact':True,'reserved_unreconstructed_layers_exact':reserved,'readback_sheets':sheets,'inputs':tracked,'actually_viewed':False,'producer_functions_imported_or_called':False,'source_or_resource_modified':False,'new_MIPS_execution':False,'runtime_verified':False,'limits':['변경raw26은새호버10과저장순열16으로구분한다.16은미술변경이아니다.','모든32전체타일의512배열역순열을대조했다.순열후소비레코드의tile번호외flags/x/y/순서는동일이다.','본문50층과320부분은독립수용source와일치,별도저장16의512부분은부모와일치하여합832이다.','작은머리19및198의raw/층/의미기록/640부분은부모4cea와같다.물리record_offset까지모두같다고주장하지않는다.','비사격source10과사격source10의기존독립범위를재사용하며새원화작업·재생성은없다.','원MIPS/재현거부는Root준비중이므로최종결속전별도로확인한다.이번은새MIPS/실기검증이아니다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(C)}))
