"""노바 준비4의 원화·의상·공통층 및 고정은행을 독립 읽기로 재구성한다."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
MODE=sys.argv[1];assert MODE in('base','ultimate');U=MODE=='ultimate'
P=H/f'prepared_nova_{MODE}01';T=H/f'nova_{MODE}_targets01';O=D/f'shibuki_nova_{MODE}4_independent01'
assert not O.exists(),'기존 감사 보존: 새 폴더 필요'
PBS=(0,5,6,7,8);KEYS=(213,215);REFS={213,214,215,216};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def equal(z,p):assert np.array_equal(z,png(p)),str(p)
oldp=H/f'prepared_chaser_{MODE}01'/('PL02_U.ARC'if U else'PL00_U.ARC');newp=P/oldp.name
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)==('2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c'if U else'3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d')
assert sha(new)==('687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f'if U else'619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5')
proposal=js(P/'proposal.json');lock=js(P/'PREPARED_LOCK.json');source=js(P/'INPUT_LOCK.json');producer=js(P/'verification.json')
for p,h in lock['files'].items():assert sha(blob(P/p))==h,p
for p,h in lock['source_scripts'].items():assert sha(blob(H/p))==h,p
assert sha(blob(P/'INPUT_LOCK.json'))==proposal['target_lock_sha256']
for p,h in source['files'].items():assert sha(blob(ROOT/p))==h,p
assert len(source['files'])==(172 if U else 169)
meta=js(T/'manifest.json');assert meta['parent_sha256']==sha(old)and set(meta['refs'])==REFS
for p,h in meta['source_files'].items():assert sha(blob(ROOT/p))==h,p
Y,X=np.indices((384,384));Y-=160;X-=160
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
ARM={213:[(-16,2),(-9,2),(-6,8),(-5,14),(-9,17),(-14,15)],215:[(-21,-29),(-10,-29),(-11,-21),(-10,-14),(-9,-8),(-8,-2),(-12,1),(-16,-8),(-20,-16)]}
DECO={213:[(2,-10),(15,-10),(16,3),(5,3)],215:[(0,-23),(15,-23),(15,-5),(4,-5)]}
HANDS={213:[[(-16,2),(-9,2),(-9,8),(-16,8)],[(2,10),(9,10),(9,15),(2,15)]],215:[[(-21,-29),(-10,-29),(-10,-21),(-21,-21)],[(-2,6),(7,6),(7,12),(-2,12)]]}
quant=[]
def register(sd,nd,forms,special=False):
 art=H/sd/'generated.png';blob(art);im=Image.open(art).convert('RGBA');rm=js(H/nd/'report.json')
 assert rm['source_sha256']==sha(art.read_bytes())
 full=np.array(im.resize((192,128)if special else(192,192),Image.Resampling.NEAREST));result={}
 for ci,(form,pal)in enumerate(forms):
  for ri,n in enumerate(KEYS):
   cell=full[:,ri*96:(ri+1)*96]if special else full[ri*96:(ri+1)*96,ci*96:(ci+1)*96]
   ind=(1+np.square(cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,pal+1:pal+16]).sum(3).argmin(2)).astype(np.uint8);ind[cell[:,:,3]<128]=0
   z=np.zeros((384,384),np.uint8)
   if special:z[96:224,112:208]=ind
   else:z[112:208,112:208]=ind
   equal(z,H/nd/f'{form}_{n:03}_indices.png')
   result[form,n]=z;counts['generated_cells_requantized']+=1;quant.append({'source':rel(art),'source_size':list(im.size),'ref':n,'form':form,'fixed_resize':[192,128]if special else[192,192],'registered_sha256':sha(z.tobytes())})
 return result
masters={};joints=[]
if not U:
 reg=register('nova_base_inputs01','nova_base_native01',[('base',0),('fourth',16)])
 donor=register('nova_fourth_costume_inputs01','nova_fourth_costume_native01',[('fourth',16)],True)
 polys={213:[[(-14,8),(-8,7),(-5,8),(-2,7),(3,8),(8,10),(9,16),(8,24),(-3,24),(-9,18),(-14,15)]],215:[[(-19,-21),(-12,-21),(-12,-16),(-10,-10),(-9,-5),(-8,-3),(-12,0),(-16,-8),(-19,-16)],[(-10,-3),(-6,-2),(-2,-3),(5,-1),(8,4),(7,14),(6,25),(0,25),(-5,16),(-10,19),(-13,11),(-12,5),(-8,2)]]}
 hands={213:[(-15,3,-9,8),(3,10,9,15)],215:[(-20,-28,-10,-21),(-1,6,6,12)]}
 edge={213:[(0,20,1,20)],215:[(-13,-21,-14,-21),(10,-17,9,-17),(10,-16,9,-16),(11,-16,9,-16),(10,-15,9,-14),(11,-15,9,-14),(11,-10,10,-11),(-16,-9,-15,-9),(-9,-1,-8,-1),(-9,0,-8,0)]}
 js(H/'nova_fourth_costume_composed01/report.json');js(H/'nova_layers_probe01/report.json');js(H/'nova_layers_final01/report.json')
 remap=1+np.square(rgb[:16,None]-rgb[None,17:32]).sum(2).argmin(1)
 for n in KEYS:
  base=reg['base',n];fourth=reg['fourth',n].copy();protect=np.zeros_like(base,bool)
  for x0,y0,x1,y1 in hands[n]:protect|=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)&np.isin(fourth,[9,10,11])
  region=polygons(polys[n])&~protect;fourth[region]=donor['fourth',n][region];equal(fourth,H/f'nova_fourth_costume_composed01/fourth_{n:03}_indices.png')
  arm=polygons([ARM[n]]);deco=polygons([DECO[n]]);cut=8 if n==213 else -3;braid=(X>=9)&(Y>=cut)&(Y<(24 if n==213 else 18));head=((Y<cut)&~arm&~deco)|braid
  hand=polygons(HANDS[n])&np.isin(base,[10,12,13]);common=head|hand;over=fourth.copy();over[common]=0;missing=(base>0)&(over==0)&~common
  outline=missing&np.isin(base,[2,15]);over[outline]=remap[base[outline]];pending=missing&~outline
  owner=np.full(base.shape,6,np.uint8);owner[Y>=(16 if n==213 else 7)]=8;owner[(Y<cut)|deco|braid]=5;owner[arm]=7
  ls={0:base,**{pb:np.where(owner==pb,over,0).astype(np.uint8)for pb in(5,6,7,8)}}
  for name,z in [('common',common),('head',head),('hands',hand),('arm',arm),('deco',deco),('outline',outline),('unresolved',pending)]:equal(z.astype(np.uint8)*255,H/f'nova_layers_probe01/{n:03}_{name}_mask.png')
  equal(owner,H/f'nova_layers_probe01/{n:03}_owner.png')
  for pb,z in ls.items():equal(z,H/f'nova_layers_probe01/{n:03}_bank{pb}_indices.png')
  assert {(int(x)-160,int(y)-160)for y,x in zip(*np.nonzero(pending))}=={(x,y)for x,y,_,_ in edge[n]}
  for x,y,sx,sy in edge[n]:
   pb=int(owner[y+160,x+160]);v=fourth[sy+160,sx+160];assert v>0 and ls[pb][y+160,x+160]==0;ls[pb][y+160,x+160]=v;counts['source_edge_samples']+=1
  for pb,z in ls.items():equal(z,H/f'nova_layers_final01/{n:03}_bank{pb}_indices.png')
  masters[n]=ls;joints.append({'ref':n,'new_costume_polygon_protected_skin_exact':True,'new_common_head_hands_and_owner_masks_exact':True,'edge_source_cells':edge[n]})
else:
 reg=register('nova_ultimate_inputs01','nova_ultimate_native01',[('before',16),('after',0)])
 donor=register('nova_ultimate_footwear_inputs01','nova_ultimate_footwear_native01',[('before',16),('after',0)])
 polys={213:[[(-6,16),(2,16),(4,17),(7,17),(8,19),(8,20),(1,20),(-6,19)]],215:[[(-11,9),(-7,9),(-5,11),(-5,12),(-10,12)],[(-2,11),(3,11),(3,13),(6,16),(8,18),(8,20),(2,20),(1,17),(-2,14)]]}
 js(H/'nova_ultimate_footwear_composed01/report.json');joint=js(H/'nova_ultimate_common01/report.json');js(H/'nova_ultimate_common02/report.json')
 lut=np.r_[0,1+np.square(rgb[17:32,None]-rgb[None,1:16]).sum(2).argmin(1)].astype(np.uint8);assert lut.tolist()==joint['before16_to_after0']
 for n in KEYS:
  feet=((Y>=20)&(X>=3))if n==213 else(((Y>=12)&(X<=-5))|((Y>=20)&(X>=3)))
  region=polygons(polys[n])&~feet
  for form in('before','after'):
   z=reg[form,n].copy();z[region]=donor[form,n][region];equal(z,H/f'nova_ultimate_footwear_composed01/{form}_{n:03}_indices.png');reg[form,n]=z
  before=reg['before',n].copy();after=reg['after',n].copy();arm=polygons([ARM[n]]);cut=8 if n==213 else -3
  head=((Y<cut)&~arm)|((X>=9)&(Y<(24 if n==213 else 18)));legs=Y>=(16 if n==213 else 12)
  if n==215:legs|=(Y>=7)&(Y<12)&(X>=-11)&(X<=3)&np.isin(before,[10,12,13])
  hand=polygons(HANDS[n])&np.isin(before,[10,12,13]);common=head|legs|hand;after[common]=lut[before][common]
  for name,z in [('head',head),('legs',legs),('hand',hand),('common',common)]:equal(z.astype(np.uint8)*255,H/f'nova_ultimate_common01/{n:03}_{name}_mask.png')
  for form,z in [('before',before),('after',after)]:equal(z,H/f'nova_ultimate_common01/{form}_{n:03}_indices.png')
  if n==215:
   assert before[166,168]==0 and after[166,168]==8;j=next(j for j in range(1,16)if a.words[16+j]==a.words[8]);before[166,168]=j;counts['same_color_new_outline_cell']+=1
  for form,z in [('before',before),('after',after)]:equal(z,H/f'nova_ultimate_common02/{form}_{n:03}_indices.png')
  diff=np.any(color(a,before,16)!=color(a,after,0),axis=2);ls={0:after,5:np.where(diff,before,0).astype(np.uint8),**{pb:np.zeros_like(before)for pb in(6,7,8)}}
  for pb,z in ls.items():equal(z,H/f'nova_ultimate_common02/{n:03}_bank{pb}_indices.png')
  assert not np.any((after>0)&(before==0));masters[n]=ls;joints.append({'ref':n,'new_footwear_inside_polygon_exact_first_feet_preserved':True,'new_common_head_legs_hand_masks_exact':True,'outline_same_color_cell':[[8,6]]if n==215 else[]})
target={}
for n in sorted(REFS):
 for pb in PBS:
  z=masters[n if n in KEYS else n-1][pb];equal(z,T/f'{n:03}_bank{pb}_indices.png');assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)];target[n,pb]=z
storage=set()if U else{35,36,51,52,53,54,67,68,83,84};maps={};permutations=[]
for g in producer.get('storage_proofs',[]):
 k=g['refs'][0];mp=[int(g['mapping'][str(t)])for t in range(32)];assert sorted(mp)==list(range(32))
 assert sha(raw(a,0,k))==g['source_raw_sha256']and sha(raw(b,0,k))==g['new_raw_sha256']
 for t in range(32):assert np.array_equal(tile(a,k,t),tile(b,k,mp[t]));counts['inverse_full256nibble_tiles_exact']+=1
 for t in g['fixed_tiles']:assert mp[t]==t
 for n in g['refs']:assert n in storage and raw(a,0,n)==raw(a,0,k)and raw(b,0,n)==raw(b,0,k);maps[n]=mp
 permutations.append({'refs':g['refs'],'mapping':mp,'all32_full_tiles_exact':True,'fixed_tiles':g['fixed_tiles']})
assert set(maps)==storage
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne];allow=np.zeros(len(old),bool)
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
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb);counts['target_layers_exact'if n in REFS else'non_art_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in changed:
   if n in storage:
    assert len(op)==len(bp)
    for p,q in zip(op,bp):assert sig(q)==(p['flags'],maps[n][p['tile']],p['x'],p['y'])
    counts['storage_compositions_inverse_exact']+=1
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and q['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(q['flip_y']and t//16==0 and z[0].any());counts['GPU_target_parts'if n in REFS else'GPU_storage_parts']+=1
  else:assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(changed):
 oo=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']];no=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert oo==no and set(no)<=changed;groups.append({'ref':n,'owners':no,'old_tiles':a.banks[0]['frames'][n]['tile_count'],'new_tiles':b.banks[0]['frames'][n]['tile_count']})
for n in sorted(changed):
 for mask in range(16):
  for arm in(1,2):
   if n in REFS:
    exp=color(b,target[n,0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;exp[m]=v[m]
   else:exp=np.array(a.composite(n,mask,arm)[0])
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(exp,actual);counts['target_partial_RGBA_exact'if n in REFS else'storage_partial_RGBA_exact']+=1
   if n in REFS:assert label(actual[:,:,3]>0,np.ones((3,3)))[1]==1
native=None
if not U:
 npth=D/'shibuki_nova_base4_directory_native01/report.json';native=js(npth);assert native['passed']and native['candidate_sha256']==sha(new)and native['stats']['references']==508
 for q in native['references']:assert q['decoded_sha256']==sha(raw(b,q['bank'],q['ref']))
 native={'path':rel(npth),'sha256':sha(npth.read_bytes()),'all508_decoded_hashes_bound':True,'original_loader_directory_initialized':True,'Python_pointer_injection':False}
assert counts['raw_checked']==(512 if U else 508)and counts['non_target_raw_exact']==(508 if U else 494)
assert counts['target_layers_exact']==20 and counts['non_art_layers_exact']==1120 and counts['target_partial_RGBA_exact']==128
assert counts['generated_cells_requantized']==(8 if U else 6)
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows):
 box=(126,124,194,192);cw,ch=280,300;im=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(caption,pic)in enumerate(row):
   bb=pic.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=pic.crop(box).resize((272,272),Image.Resampling.NEAREST);im.paste(v,(x*cw+3,y*ch+22),v)
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
for n in KEYS:
 masks=[15,0]if U else[0,15];names=['before','after']if U else['base','fourth']
 sheet(f'comparison_{n}.png',[[(f'{n} {state} {form}',ar.composite(n,m)[0])for form,m in zip(names,masks)for state,ar in[('old',a),('new',b)]]])
 sheet(f'partial_{n}.png',[[(f'{n} mask{m}',b.composite(n,m)[0])for m in(0,1,2,4,8,15)]])
 sheet(f'alias_{n}.png',[[(f'{nn} {form}',b.composite(nn,m)[0])for nn in(n,n+1)]for form,m in zip(names,masks)])
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':f'시부키 {MODE} 노바 준비4 독립 원화/보존 검사','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha((P/'INPUT_LOCK.json').read_bytes()),'counts':dict(counts),'generated_requantization':quant,'joint_reconstruction':joints,'pair_policy':'현재 수용된 213=214/215=216 신작 동형정책. 원US가 처음부터 동일했다는 주장 없음.','permutations':permutations,'stream_groups':groups,'all128_partial_single_component':True,'all_bank_entry_boundaries_palette_audio_exact':True,'reserved_layers':reserved,'native_directory':native,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'overall_complete':False,'limits':['원화 고정표본/새 의상·공통층을 독립 재구성했으나 자동 미술 수용은 아님.','원MIPS 실행·재현거부 증거의 범위는 별도 evidence.json에 기록. 실제 에뮬레이터/차량/특수 동작 실행 아님.','기본 sequence01의 mask15 강제 오류는 정정02로만 평가하며 옛 순서판을 새 검증 근거로 사용하지 않음.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
