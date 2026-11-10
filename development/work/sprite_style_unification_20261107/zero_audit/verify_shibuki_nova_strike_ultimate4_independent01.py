"""Ultimate 217..220: 제작 함수 없이 원화/역사효과/실제 ARC를 읽는다."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_fill_holes,label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit';sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
P=H/'prepared_nova_strike_ultimate01';T=H/'nova_strike_ultimate_targets01';E=H/'nova_strike_ultimate_effects02'
O=D/'shibuki_nova_strike_ultimate4_independent01';assert not O.exists()
PBS=(0,5,6,7,8);REFS={217,218,219,220};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def equal(z,p):assert np.array_equal(z,png(p)),str(p)
oldp=H/'prepared_nova_ultimate01/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f'
assert sha(new)=='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7'
pr=js(P/'proposal.json');lk=js(P/'PREPARED_LOCK.json');inp=js(P/'INPUT_LOCK.json');meta=js(T/'manifest.json');em=js(E/'manifest.json');ver=js(P/'verification.json')
for p,h in lk['files'].items():assert sha(blob(P/p))==h,p
for p,h in lk['source_scripts'].items():assert sha(blob(H/p))==h,p
assert sha(blob(P/'INPUT_LOCK.json'))==pr['target_lock_sha256'] and len(inp['files'])==83
for source in(inp['files'],meta['source_files'],em['source_files']):
 for p,h in source.items():assert sha(blob(R/p))==h,p
art=H/'nova_strike_ultimate_inputs01/generated_v1.png';blob(art);im=Image.open(art).convert('RGBA');assert im.width==im.height
cell=np.array(im.resize((128,128),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.int32)
q=(1+np.square(cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:]).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
body=np.zeros((384,384),np.uint8);body[96:224,96:224]=q;assert int((body>0).sum())==776 and label(body>0,np.ones((3,3)))[1]==1
equal(body,H/'nova_strike_ultimate_native01/217_indices.png');equal(body,E/'body_217_indices.png')
hp=js(R/'work/ultimate_costume_swap_20261105/core/prepared_special_v1/ver_buki_riko/proposal.json');binp=R/hp['baseline'];assert sha(blob(binp))==hp['baseline_sha256']
histdata=read_disc(binp,('PL02_U.ARC',))[0]['PL02_U.ARC'];assert sha(histdata)==hp['source_arc_sha256'] and histdata==blob(E/'historical_PL02.ARC');hist=Archive(histdata)
oldbody=hist.layer(217,5)[0];currentbody=a.layer(217,0)[0];assert int((currentbody>0).sum())==840
remove=binary_dilation(oldbody>0);effects={217:np.zeros_like(body)};effectproof=[]
for n,fill in((218,None),(220,7)):
 source=hist.layer(n,5)[0];envelope=binary_fill_holes(source>0)
 def derive(silhouette):
  z=source.copy();z[remove]=0;holes=np.zeros_like(remove)
  if fill is not None:holes=remove&envelope&(z==0)&(silhouette==0);z[holes]=fill
  z[silhouette>0]=0;return z,holes
 previous,oldholes=derive(currentbody);assert np.array_equal(previous,a.layer(n,5)[0])
 regenerated,holes=derive(body);z=previous.copy() if n==218 else regenerated
 protected=(~remove)&(body==0)
 if n==218:protected&=currentbody==0
 assert np.array_equal(z[protected],source[protected]) and not((z>0)&(body>0)).any()
 if n==218:
  yy,xx=np.nonzero(z);assert sorted(zip((xx-160).tolist(),(yy-160).tolist(),z[yy,xx].tolist()))==[(7,-28,1),(7,27,1),(12,-14,1)]
  yy,xx=np.nonzero(regenerated!=z);assert list(zip((xx-160).tolist(),(yy-160).tolist()))==[(12,13)]
  assert regenerated[173,172]==1 and currentbody[173,172]==2
 else:assert int((z!=previous).sum())==93
 for name,value in(('source_effect',source),('old_body_dilation',remove*255),('old_effect_envelope',envelope*255),('new_fill_mask',holes*255),('protected_mask',protected*255),('effect',z)):
  equal(value,E/f'{name}_{n}_indices.png' if name in('source_effect','effect') else E/f'{name}_{n}.png')
 effects[n]=z;effectproof.append({'ref':n,'historical_current_reproduced':True,'changed_cells':int((z!=previous).sum()),'effect_pixels':int((z>0).sum()),'new_body_covered_cells':0,'source_outside_old_dilation_and_new_body_exact':True,'new_holes':int(holes.sum()),'whole_effect_unchanged':bool(np.array_equal(z,previous))})
oldflash=np.zeros_like(body);oldflash[binary_dilation(currentbody>0,iterations=2)]=7;oldflash[currentbody>0]=6;assert np.array_equal(oldflash,a.layer(219,5)[0])
flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6;effects[219]=flash;equal(flash,E/'effect_219_indices.png')
target={}
for n in REFS:
 for pb in PBS:
  z=(body if n!=219 else np.zeros_like(body)) if pb==0 else effects[n] if pb==5 else np.zeros_like(body)
  target[n,pb]=z;equal(z,T/f'{n:03}_bank{pb}_indices.png');assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)]
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(x['type'],x['offset'],x['size'])for x in oe]==[(x['type'],x['offset'],x['size'])for x in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert 0<bf['tile_count']<=32
  else:assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as e:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as e2:assert(type(e),str(e))==(type(e2),str(e2))
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb);counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in REFS:
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and p['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(p['flip_y']and t//16==0 and z[0].any());counts['GPU_parts']+=1
  else:assert[sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(REFS):
 og=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']];ng=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert og==ng==[n];groups.append({'ref':n,'owners':ng,'tiles':b.banks[0]['frames'][n]['tile_count']})
 for mask in range(16):
  for arm in(1,2):
   exp=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:z=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=z[:,:,3]>0;exp[m]=z[m]
   assert np.array_equal(exp,np.array(b.composite(n,mask,arm)[0]));counts['target_partial_RGBA_exact']+=1
post=js(P/'post_lock_evidence.json')
for p,h in post['evidence'].items():assert sha(blob(R/p))==h,p
native=js(H/'nova_strike_ultimate_components_native_checks.json');assert native['passed']
nr=native['resources']['PL02_U.ARC'];assert nr['candidate_sha256']==sha(new)and nr['GPU_part_edge_checks']==counts['GPU_parts']
for row in nr['banks'][0]['native_decoder_checks']:assert row['decoded_sha256']==sha(raw(b,0,row['frame']))
assert dict(counts)=={'raw_checked':512,'non_target_raw_exact':508,'non_target_layers_exact':1120,'target_layers_exact':20,'non_target_compositions_exact':1771,'GPU_parts':66,'target_partial_RGBA_exact':128},dict(counts)
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows,box=(104,120,256,200),scale=4):
 w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale;im=Image.new('RGB',((w+8)*len(rows[0]),(h+32)*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(caption,pic)in enumerate(row):
   bb=pic.getbbox();assert bb is None or(box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]),bb
   dr.text((x*(w+8)+3,y*(h+32)+3),caption,fill='white');z=pic.crop(box).resize((w,h),Image.Resampling.NEAREST);im.paste(z,(x*(w+8)+3,y*(h+32)+25),z)
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
sheet('actual_217_218.png',[[(f'{n} parent15',a.composite(n,15)[0]),(f'{n} packed15',b.composite(n,15)[0])]for n in(217,218)])
sheet('actual_219_220.png',[[(f'{n} parent15',a.composite(n,15)[0]),(f'{n} packed15',b.composite(n,15)[0])]for n in(219,220)])
for n in(218,220):sheet(f'ownership_{n}.png',[[('new body0',b.rgba(target[n,0])),('effect5',b.rgba(target[n,5],16)),('actual mask15',b.composite(n,15)[0])]],scale=3)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'passed':True,'scope':'시부키 Ultimate217..220 새1몸체/파생효과20층 독립 읽기 검사','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'counts':dict(counts),'generated_cells_direct_requantized':1,'new_body_pixels':776,'whole_canvas_native':[128,128],'historical_BIN_direct_extraction_exact':True,'effects':effectproof,'effect218_current3_world_exact':True,'effect218_hidden_old_foot_pixel_not_reintroduced':[12,13,1],'effect219_rule':'Manhattan2 ring7/body6','effect219_new_pixels':int((flash>0).sum()),'staging220_world_translation':[0,0],'all_entry_bank_boundaries_palette_audio_exact':True,'stream_groups':groups,'reserved_layers':reserved,'native_producer_4_raw_hashes_bound':True,'native_new_execution_by_this_reader':False,'diagnostic128_partial_not_actual128_states':True,'actual_engine_mask':15,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'limits':['고정128셀 원화1개를 직접 양자화했으며 새로운 몸/실루엣 정책과 역사효과 재현을 구분한다.','220은 새몸 가림93셀 변경이며 전체효과 raw 보존이 아니다.218 현재3점은 전체 그대로다.','제작자 MIPS/재현/거부/원순서 증거는 해시 결속하며 독립 재실행이나 실제 게임 검증으로 부르지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
