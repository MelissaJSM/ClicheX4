"""새217/220 원화·효과·저장순열을 별도 독립 reader로 재구성한다."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit';sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons,render
P=H/'prepared_nova_strike_base01';T=H/'nova_strike_base_targets01';O=D/'shibuki_nova_strike2_independent02';assert not O.exists()
PBS=(0,5,6,7,8);REFS={217,220};STORAGE={45,46,71,72,73,74};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def equal(v,p):assert np.array_equal(v,png(p)),str(p)
oldp=H/'prepared_nova_base01/PL00_U.ARC';newp=P/'PL00_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5'
assert sha(new)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
pr=js(P/'proposal.json');lk=js(P/'PREPARED_LOCK.json');inputs=js(P/'INPUT_LOCK.json');v=js(P/'verification.json');meta=js(T/'manifest.json')
for p,h in lk['files'].items():assert sha(blob(P/p))==h,p
for p,h in lk['source_scripts'].items():assert sha(blob(H/p))==h,p
assert sha(blob(P/'INPUT_LOCK.json'))==pr['target_lock_sha256']
for p,h in inputs['files'].items():assert sha(blob(R/p))==h,p
assert len(inputs['files'])==122
for p,h in meta['source_files'].items():assert sha(blob(R/p))==h,p
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
def quant(p,size,box,pal):
 blob(p);im=Image.open(p).convert('RGBA');cell=np.array(im.resize(size,Image.Resampling.NEAREST))[box[1]:box[3],box[0]:box[2]]
 q=(1+np.square(cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,pal+1:pal+16]).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
 z=np.zeros((384,384),np.uint8);y0=160-q.shape[0]//2;x0=160-q.shape[1]//2;z[y0:y0+q.shape[0],x0:x0+q.shape[1]]=q
 counts['generated_cells_requantized']+=1;return z
art=H/'nova_strike_base_inputs01/generated.png';reg={}
for i,(form,pal)in enumerate((('base',0),('fourth',16))):
 z=quant(art,(192,128),(i*96,0,(i+1)*96,128),pal);equal(z,H/f'nova_strike_base_native01/{form}_217_indices.png');reg[form]=z
donor=quant(H/'nova_strike_boot_inputs01/generated.png',(128,128),(0,0,128,128),16);equal(donor,H/'nova_strike_boot_native01/fourth_217_indices.png')
Y,X=np.indices((384,384));Y-=160;X-=160;base=reg['base'];fourth=reg['fourth'];boot=(X>=16)&(X<=27)&(Y>=6)&(Y<=14)
shift=np.zeros_like(donor);shift[:,1:]=donor[:,:-1];costume=fourth.copy();costume[boot]=shift[boot];equal(costume,H/'nova_strike_layers_probe01/fourth_boot_composed_indices.png')
hair_polys=[[(-30,-18),(-10,-18),(-9,-9),(-12,-5),(-12,1),(-15,4),(-23,4),(-29,0)],[(-12,-10),(2,-9),(10,-5),(10,0),(5,1),(-2,-3),(-12,-2)],[(8,-1),(18,-1),(21,2),(19,5),(10,4)]]
deco=polygons([[(-16,-14),(-8,-14),(-7,-6),(-10,-3),(-15,-4)]])
hair=polygons(hair_polys)&~deco;hands=polygons([[(-28,3),(-22,3),(-21,8),(-28,8)],[(-6,2),(1,2),(1,7),(-6,7)]])&np.isin(base,[10,12,13]);common=hair|hands
arm=polygons([[(-29,3),(-20,2),(-14,6),(-15,12),(-21,15),(-27,12)]])
lut=1+np.square(rgb[:16,None]-rgb[None,17:32]).sum(2).argmin(1);over=costume.copy();over[common]=0;missing=(base>0)&(over==0)&~common;outline=missing&np.isin(base,[2,15]);over[outline]=lut[base[outline]];pending=missing&~outline;assert not pending.any()
owner=np.full(base.shape,6,np.uint8);owner[(X>=7)&(Y>=6)]=8;owner[hair|deco]=5;owner[arm]=7
ls={0:base.copy(),**{pb:np.where(owner==pb,over,0).astype(np.uint8)for pb in PBS[1:]}}
for name,z in [('boot',boot),('common',common),('head',hair),('hands',hands),('deco',deco),('outline',outline),('unresolved',pending)]:equal(z.astype(np.uint8)*255,H/f'nova_strike_layers_probe01/217_{name}_mask.png')
equal(owner,H/'nova_strike_layers_probe01/217_owner.png')
for pb,z in ls.items():equal(z,H/f'nova_strike_layers_probe01/217_bank{pb}_indices.png')
ring=binary_dilation(base>0)&(base==0);ls[0][ring]=6
origp=H/'chaser_sources01/original_base.ARC';orig=blob(origp);assert sha(orig)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a';us=Archive(orig)
fxmap=np.array([0]+[6 if i==12 else 9 for i in range(1,16)],np.uint8);bg=fxmap[us.layer(220)[0]%16]
equal(bg,T/'220_background_indices.png');equal(ls[0],T/'220_body_with_outline_indices.png')
prefix=b''.join(us.c[p['record_offset']:p['record_offset']+4]for p in parts(us,0,220));assert len(prefix)==96 and prefix==blob(T/'effect220_prefix.bin')
assert [sig(p)for p in parts(b,0,220)[:24]]==[sig(p)for p in parts(us,0,220)]
seed=blob(T/'effect220_seed32.raw');sa=np.frombuffer(indexed_atlas(seed,32)[0],np.uint8).reshape(32,256)
for t in range(18):
 expected=fxmap[tile(us,220,t)];actual=tile(b,220,t);assert np.array_equal(expected,actual);assert np.array_equal(expected,sa[t//16*16:t//16*16+16,t%16*16:t%16*16+16]);counts['original_effect_full256_tiles_exact']+=1
assert np.array_equal(render(b,220,0,parts(b,0,220)[:24]),bg)
assert np.array_equal(render(b,220,0,parts(b,0,220)[24:]),ls[0])
target={}
for n in REFS:
 for pb in PBS:
  z=ls[pb].copy()
  if n==220 and pb==0:z=bg.copy();z[ls[0]>0]=ls[0][ls[0]>0]
  equal(z,T/f'{n:03}_bank{pb}_indices.png');assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)];target[n,pb]=z
for n in(218,219):
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0])and[sig(p)for p in parts(a,pb,n)]==[sig(p)for p in parts(b,pb,n)]
maps={};perms=[]
for g in v['storage_proofs']:
 n=g['refs'][0];mp=[int(g['mapping'][str(i)])for i in range(32)];assert sorted(mp)==list(range(32))
 assert sha(raw(a,0,n))==g['source_raw_sha256']and sha(raw(b,0,n))==g['new_raw_sha256']
 for t in range(32):assert np.array_equal(tile(a,n,t),tile(b,n,mp[t]));counts['storage_full256_tiles_inverse_exact']+=1
 for t in g['fixed_tiles']:assert mp[t]==t
 for k in g['refs']:assert raw(a,0,k)==raw(a,0,n)and raw(b,0,k)==raw(b,0,n);maps[k]=mp
 perms.append({'refs':g['refs'],'mapping':mp,'fixed_tiles':g['fixed_tiles']})
assert set(maps)==STORAGE and len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(x['type'],x['offset'],x['size'])for x in oe]==[(x['type'],x['offset'],x['size'])for x in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
changed=REFS|STORAGE
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
   except(ValueError,IndexError)as e:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as e2:assert(type(e),str(e))==(type(e2),str(e2))
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb);counts['target_layers_exact'if n in REFS else'non_art_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in changed:
   if n in STORAGE:
    assert len(op)==len(bp)
    for p,q in zip(op,bp):assert sig(q)==(p['flags'],maps[n][p['tile']],p['x'],p['y'])
    counts['storage_compositions_inverse_exact']+=1
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and p['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(p['flip_y']and t//16==0 and z[0].any());counts['GPU_target_parts'if n in REFS else'GPU_storage_parts']+=1
  else:assert[sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(changed):
 og=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']];ng=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert og==ng and set(ng)<=changed;groups.append({'ref':n,'owners':ng})
for n in sorted(changed):
 for mask in range(16):
  for arm_type in(1,2):
   if n in REFS:
    exp=color(b,target[n,0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:z=color(b,target[n,pb],32 if pb==7 and arm_type==2 else 16);m=z[:,:,3]>0;exp[m]=z[m]
   else:exp=np.array(a.composite(n,mask,arm_type)[0])
   actual=np.array(b.composite(n,mask,arm_type)[0]);assert np.array_equal(exp,actual);counts['target_partial_RGBA_exact'if n in REFS else'storage_partial_RGBA_exact']+=1
   if n==217:assert label(actual[:,:,3]>0,np.ones((3,3)))[1]==1
nd=js(D/'shibuki_nova_strike2_directory_native01/report.json');assert nd['passed']and nd['candidate_sha256']==sha(new)
for row in nd['references']:assert row['decoded_sha256']==sha(raw(b,row['bank'],row['ref']))
nr=js(D/'shibuki_nova_strike2_renderer_native02/conclusions.json');assert nr['passed']and nr['candidate_sha256']==sha(new)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==500 and counts['target_layers_exact']==10 and counts['non_art_layers_exact']==1130
assert counts['target_partial_RGBA_exact']==64 and counts['storage_partial_RGBA_exact']==192
assert counts['generated_cells_requantized']==3 and counts['original_effect_full256_tiles_exact']==18
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows,box=(104,116,256,208),scale=4):
 w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale;im=Image.new('RGB',((w+8)*len(rows[0]),(h+32)*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(caption,pic)in enumerate(row):
   bb=pic.getbbox();assert bb is None or(box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]),bb
   dr.text((x*(w+8)+3,y*(h+32)+3),caption,fill='white');z=pic.crop(box).resize((w,h),Image.Resampling.NEAREST);im.paste(z,(x*(w+8)+3,y*(h+32)+25),z)
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
for form,m in(('base',0),('fourth',15)):
 sheet(f'{form}_comparison.png',[[(f'{n} old',a.composite(n,m)[0]),(f'{n} new',b.composite(n,m)[0])]for n in(217,220)])
for n in(217,220):sheet(f'partial_{n}.png',[[(f'{n} mask{m}',b.composite(n,m)[0])for m in row]for row in((0,1,2),(4,8,15))])
sheet('effect220.png',[[('original effect recolored',b.rgba(bg)),('new 217 body+outline',b.rgba(ls[0])),('packed220',b.composite(220,0)[0])]],scale=3)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'passed':True,'scope':'시부키 PL00 노바217/220 독립 원화→10층→실제 ARC 및 원효과/저장순열/부분 읽기 검사','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'counts':dict(counts),'source_reconstruction':{'generated_cells':3,'fixed_canvas':[192,128],'boot_donor_fixed_canvas':[128,128],'boot_local_translation':[1,0],'boot_changed_cells':int((costume!=fourth).sum()),'common_head_hands_deco_owner_masks_exact':True,'unresolved_cells':0,'new_outline_Manhattan1_index6_cells':int(ring.sum()),'fourth_source_outline_samples':int(outline.sum())},'effect220':{'original_US_prefix_24_records_exact':True,'original_US_18_full_tiles_recolored_exact':True,'native_color_map':fxmap.tolist(),'background_world_exact':True,'new_body_suffix_7_parts_exact':True,'part_order':'원효과24 파트 뒤 새몸7 파트','base_count':len(parts(b,0,220)),'all_mask15_count':sum(len(parts(b,pb,220))for pb in PBS),'old_body_occlusion_changes_are_new_policy':True},'effects218_219_raw_layers_records_exact':True,'storage_permutations':perms,'stream_groups':groups,'all_entry_bank_boundaries_palette_audio_exact':True,'reserved_layers':reserved,'all217_partial_single_component':True,'native_directory508_hashes_bound':True,'native_renderer136_two_runs_bound':True,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'limits':['원화 고정셀 양자화·부츠 국소등록·부분소유를 직접 재구성했지만 수치 통과가 미술 수용을 대신하지 않음.','producer 재현/거부는 고정 증거를 읽기 결속했으며 독립 재빌드하지 않음.','별도 원 MIPS 실행은 격리 fixture이며 실제 게임/GPU 래스터화/전체장면 실행으로 확대하지 않음.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
