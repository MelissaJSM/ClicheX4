"""체이서13 독립 읽기: 생성8셀→소유65층/9Y별칭·16저장순열·원GPU."""
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
P=H/'prepared_chaser_base01';T=H/'chaser_targets01';O=D/'shibuki_chaser13_independent01'
PBS=(0,5,6,7,8);REFS=set(range(162,175));KEYS=(162,166,170,174);RESERVED={105,*range(175,183)}
GROUPS=((162,163,164,165),(166,167,168,169),(170,171,172,173),(174,))
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def shift(z,dy):
 out=np.zeros_like(z);yy,xx=np.nonzero(z);assert not len(yy)or min(yy+dy)>=0 and max(yy+dy)<384
 out[yy+dy,xx]=z[yy,xx];return out
assert not O.exists(),'새 고유 출력 폴더가 필요합니다.'
oldp=H/'prepared_standing_fire_base01/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
assert sha(new)=='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'
proposal=js(P/'proposal.json');lock=js(P/'PREPARED_LOCK.json');source=js(P/'INPUT_LOCK.json');producer=js(P/'verification.json')
for p,h in lock['files'].items():assert sha(blob(P/p))==h,p
for p,h in lock['source_scripts'].items():assert sha(blob(H/p))==h,p
assert sha(blob(P/'INPUT_LOCK.json'))==proposal['target_lock_sha256']=='3d9574ae642111207a937a0e06c66a2c331608d103956c22b94bee6c636a93fb'
for p,h in source['files'].items():assert sha(blob(ROOT/p))==h,p
assert len(source['files'])==332 and source['candidate_sha256']==sha(new)and source['parent_sha256']==sha(old)
meta=js(T/'manifest.json');assert meta['parent_sha256']==sha(old)and set(meta['refs'])==REFS
for p,h in meta['source_files'].items():assert sha(blob(ROOT/p))==h,p
original=Archive(blob(H/'chaser_sources01/original_base.ARC'))
counts=collections.Counter();registered={};samples={};quant=[]
# 생성2장 전체캔버스를192로 고정표본화한다. 제작 모듈을 import하지 않는다.
for page,ns in((1,(162,166)),(2,(170,174))):
 sd=H/f'chaser_base_inputs{page:02}';nd=H/f'chaser_base_native{page:02}'
 sm=js(sd/'input.json');receipt=js(sd/'generation_receipt.json');rm=js(nd/'report.json');art=sd/'generated.png'
 assert sha(blob(art))==receipt['sha256']==rm['source_sha256']and sm['parent']['sha256']==sha(old)
 for name,h in sm['files'].items():assert sha(blob(sd/name))==h
 im=Image.open(art).convert('RGBA');assert im.width==im.height
 full=np.array(im.resize((192,192),Image.Resampling.NEAREST))
 for col,(form,pal)in enumerate((('base',0),('fourth',16))):
  rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
  for row,n in enumerate(ns):
   cell=full[row*96:(row+1)*96,col*96:(col+1)*96]
   idx=(1+np.square(cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:]).sum(3).argmin(2)).astype(np.uint8)
   idx[cell[:,:,3]<128]=0;assert not(idx[0].any()or idx[-1].any()or idx[:,0].any()or idx[:,-1].any())
   z=np.zeros((384,384),np.uint8);z[112:208,112:208]=idx
   assert np.array_equal(z,png(nd/f'{form}_{n:03}_indices.png'))and np.array_equal(cell,png(nd/f'{form}_{n:03}_sample_rgba.png'))
   q=next(q for q in rm['rows']if q['ref']==n and q['form']==form);assert sha(z.tobytes())==q['indices_sha256']and q['body_translation']==[0,0]
   registered[form,n]=z;samples[form,n]=cell;quant.append({'ref':n,'form':form,'source':rel(art),'actual_size':list(im.size),'fixed_canvas':[192,192],'cell':[96,96],'quantized_exact':True})
   counts['generated_cells_requantized']+=1
Y,X=np.indices((384,384));Y-=160;X-=160
CUT={162:-3,166:1,170:-1,174:1}
HAND={162:[(-10,-1),(-5,-1),(-5,2),(-10,2)],166:[(-10,2),(-5,2),(-5,4),(-10,4)],170:[(-10,2),(-5,2),(-5,5),(-10,5)],174:[(-10,1),(-6,1),(-6,6),(-10,6)]}
ARM={162:[(-10,-2),(-3,-2),(2,2),(2,8),(-4,9),(-8,6)],166:[(-10,1),(-2,1),(4,5),(4,10),(-3,10),(-9,6)],170:[(-11,1),(-3,0),(3,4),(2,10),(-5,11),(-9,7)],174:[(-11,0),(-5,0),(-3,6),(-4,12),(-10,12)]}
DECO=polygons([[(0,-21),(15,-21),(15,-3),(0,-3)]])
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32)
remap=1+np.square(rgb[:16,None]-rgb[None,17:32]).sum(2).argmin(1)
joint=js(H/'chaser_layers_probe02/report.json');edge=js(H/'chaser_layers_final02/report.json');masters={};joints=[]
assert sha(blob(H/'chaser_layers_probe02/report.json'))==edge['previous_probe']['sha256']
for n in KEYS:
 base=registered['base',n].copy();fourth=registered['fourth',n];head=(Y<CUT[n])&~DECO;hand=polygons([HAND[n]])&np.isin(base,[10,12,13]);common=head|hand;front=polygons([ARM[n]])
 over=fourth.copy();over[common]=0;missing=(base>0)&(over==0)&~common;outline=missing&np.isin(base,[2,15]);over[outline]=remap[base[outline]];pending=missing&~outline
 owner=np.full(base.shape,6,np.uint8);owner[Y>=(12 if n==174 else 9)]=8;owner[(Y<CUT[n])|DECO]=5;owner[front]=7;owner[(X>=7)&(Y>=CUT[n])&(Y<(10 if n==174 else 8))]=5
 ls={0:base,**{pb:np.where(owner==pb,over,0).astype(np.uint8)for pb in PBS[1:]}}
 for name,z in(('common',common),('head',head),('hand',hand),('front_arm',front),('outline',outline),('unresolved',pending)):
  assert np.array_equal(z,png(H/f'chaser_layers_probe02/{n:03}_{name}_mask.png')>0)
 assert np.array_equal(owner,png(H/f'chaser_layers_probe02/{n:03}_owner.png'))
 for pb,z in ls.items():assert np.array_equal(z,png(H/f'chaser_layers_probe02/{n:03}_bank{pb}_indices.png'))
 q=next(q for q in edge['rows']if q['ref']==n);changed=np.zeros_like(pending)
 for e in q['base_semantic_palette_registration']:
  x,y=e['xy'];assert n==170 and(x,y)==(-5,-4)and samples['base',n][y+48,x+48].tolist()==e['source_RGBA']==[164,105,42,253]
  assert ls[0][y+160,x+160]==e['automatic_nearest_index']==4 and e['semantic_gold_iris_index']==7;ls[0][y+160,x+160]=7;counts['source_iris_registration']+=1
 for e in q['events']:
  x,y=e['xy'];sx,sy=e['source_xy'];pb=e['owner_bank'];value=e['source_index']
  assert abs(x-sx)+abs(y-sy)==1 and pending[y+160,x+160]and owner[y+160,x+160]==pb and fourth[sy+160,sx+160]==value>0
  assert all(ls[v][y+160,x+160]==0 for v in PBS[1:]);ls[pb][y+160,x+160]=value;changed[y+160,x+160]=True;counts['adjacent_source_edge_registration']+=1
 assert np.array_equal(changed,pending)
 for pb,z in ls.items():assert np.array_equal(z,png(H/f'chaser_layers_final02/{n:03}_bank{pb}_indices.png'))and sha(z.tobytes())==q['layer_hashes'][str(pb)]
 masters[n]=ls;joints.append({'ref':n,'reconstructed_common_and_owner_masks':True,'adjacent_registration':q['events'],'iris_registration':q['base_semantic_palette_registration'],'old_body_pixels_used':False})
target={};aliases=[]
for group in GROUPS:
 k=group[0]
 for n in group:
  for pb in PBS:
   z=shift(masters[k][pb],DY[n]);assert np.count_nonzero(z)==np.count_nonzero(masters[k][pb])
   assert np.array_equal(z,png(T/f'{n:03}_bank{pb}_indices.png'))and sha(z.tobytes())==meta['targets'][str(n)][str(pb)]
   assert np.array_equal(a.layer(n,pb)[0],shift(a.layer(k,pb)[0],DY[n]))and np.array_equal(original.layer(n,pb)[0],shift(original.layer(k,pb)[0],DY[n]))
   target[n,pb]=z
  aliases.append({'ref':n,'master':k,'dy':DY[n],'original_US_and_parent_5layers_exact':True,'new_5layers_exact':True})
storage=set(source['storage_only_refs']);assert len(storage)==16 and not storage&REFS;maps={};permutations=[]
for g in producer['storage_proofs']:
 mp={int(k):v for k,v in g['mapping'].items()};assert set(mp)==set(mp.values())==set(range(32));k=g['refs'][0]
 assert sha(raw(a,0,k))==g['source_raw_sha256']and sha(raw(b,0,k))==g['new_raw_sha256']
 for t in range(32):assert np.array_equal(tile(a,k,t),tile(b,k,mp[t]));counts['full256nibble_tiles_inverse_exact']+=1
 for t in g['fixed_tiles']:assert mp[t]==t
 for n in g['refs']:
  assert n in storage and n not in maps and raw(a,0,n)==raw(a,0,k)and raw(b,0,n)==raw(b,0,k);maps[n]=mp
 permutations.append({'refs':g['refs'],'mapping':mp,'fixed_tiles':g['fixed_tiles'],'all32_full_tiles_exact':True})
assert set(maps)==storage
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
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_art_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in changed:
   if n in storage:
    assert len(op)==len(bp)
    for p,q in zip(op,bp):assert sig(q)==(p['flags'],maps[n][p['tile']],p['x'],p['y'])
    counts['storage_compositions_inverse_exact']+=1
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and q['unknown_flags']==0
    z=tile(b,n,t);assert not(t%16==0 and z[:,0].any())and not(q['flip_y']and t//16==0 and z[0].any());counts['GPU_target_parts'if n in REFS else'GPU_storage_parts']+=1
  else:assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(changed):
 oldowners=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']]
 newowners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert set(oldowners)<=changed and oldowners==newowners
 groups.append({'ref':n,'owners':newowners,'old_tiles':a.banks[0]['frames'][n]['tile_count'],'new_tiles':b.banks[0]['frames'][n]['tile_count']})
recipe=js(H/'chaser_storage01/recipe.json')
for g in recipe['groups']:
 for n in g['refs']:assert raw(b,0,n)==blob(H/f'chaser_storage01/{n:03}.raw')and sha(raw(b,0,n))==g['raw_sha256']and b.banks[0]['frames'][n]['tile_count']==g['count']
components=[]
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
   if n in REFS:
    _,cc=label(actual[:,:,3]>0,np.ones((3,3)));components.append({'ref':n,'mask':mask,'arm':arm,'components':int(cc)})
nativep=D/'shibuki_chaser13_directory_native01/report.json';native=js(nativep);assert native['passed']and native['candidate_sha256']==sha(new)and native['stats']['references']==508
for q in native['references']:assert q['decoded_sha256']==sha(raw(b,q['bank'],q['ref']))
assert counts['generated_cells_requantized']==8 and counts['adjacent_source_edge_registration']==6 and counts['source_iris_registration']==1
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==479 and counts['full256nibble_tiles_inverse_exact']==256
assert counts['target_layers_exact']==65 and counts['non_art_layers_exact']==1075 and counts['non_target_compositions_exact']==1642
assert counts['target_partial_RGBA_exact']==416 and counts['storage_partial_RGBA_exact']==512
O.mkdir(exist_ok=False);sheets=[];box=(126,126,194,190);w,h=68,64
def sheet(name,rows):
 cw,ch=w*4+7,h*4+25;im=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(caption,pic)in enumerate(row):
   bb=pic.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=pic.crop(box).resize((w*4,h*4),Image.Resampling.NEAREST);im.paste(v,(x*cw+3,y*ch+22),v)
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
for n in KEYS:
 sheet(f'comparison_{n}.png',[[(f'{n} old base',a.composite(n,0)[0]),(f'{n} new base',b.composite(n,0)[0]),(f'{n} old fourth',a.composite(n,15)[0]),(f'{n} new fourth',b.composite(n,15)[0])]])
 sheet(f'partial_{n}.png',[[(f'{n} {name}',b.composite(n,mask)[0])for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body+legs',10))]])
for i,ns in enumerate(GROUPS):
 sheet(f'alias_{i}.png',[[(f'{n} base Y{DY[n]:+}',b.composite(n,0)[0])for n in ns],[(f'{n} fourth Y{DY[n]:+}',b.composite(n,15)[0])for n in ns]])
for p,hsh in tracked.items():assert sha((ROOT/p).read_bytes())==hsh,p
report={'passed':True,'scope':'시부키 기본/포스 체이서 새4키×2와 원Y9파생,65층 및 기존16참조 전체타일 순열 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha((P/'INPUT_LOCK.json').read_bytes()),'locked_inputs':len(source['files']),'counts':dict(counts),'source_requantization':quant,'source_joint_reconstruction':joints,'aliases':aliases,'permutations':permutations,'stream_groups':groups,'partial_components':components,'all_partial_single_component':all(q['components']==1 for q in components),'reserved_layers':reserved,'native_report':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'all508_decoded_hashes_bound':True,'executed_separately_this_audit':True},'palette_audio_other_entries_all_bank_boundaries_exact':True,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'game_process_opened':False,'resources_or_saves_written':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['생성8셀 고정최근접/팔레트 표본과 공통부·소유/인접6셀/홍채1셀/9Y별칭을 독립 재구성했다. 원화의 창작 품질이나 실제 차량 물리접점을 자동 통과로 판정하지 않는다.','16저장참조는 원raw바이트 불변이 아니라 모든256nibble을 보존한32타일 역순열이다. 표시·좌표·flip·부분RGBA와 비대상은 exact이다.','전체508 원MIPS는 원 RAM-loader/주소초기화/디코드/업로드 큐의 로컬 실행이며 CD·실제 GPU·차량 실기와 다르다. 원 US opcode exact의 기존 BR14 코드 harness를 사용한다.','132/135 등 등장이나 기존 동결 미술 범위에 새 판단을 추가하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'all_partial_single_component':report['all_partial_single_component']}))
