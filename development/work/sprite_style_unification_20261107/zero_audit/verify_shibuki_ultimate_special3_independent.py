"""Shibuki Ultimate 95..97 source-to-layer 독립 읽기. 제작 함수 미호출."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
H=D.parent/'shibuki_audit';P=H/'prepared_standing_special_ultimate01';T=H/'ultimate_special_targets01';O=D/'shibuki_ultimate_special3_independent01'
PBS=(0,5,6,7,8);REFS={95,96,97};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def readj(p):return json.loads(readb(p))
def png(p):readb(p);return np.asarray(Image.open(p))
oldp=H/'prepared_ultimate_return01/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=readb(oldp),readb(newp)
assert sha(old)=='f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc'
assert sha(new)=='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'
a,b=Archive(old),Archive(new);proposal=readj(P/'proposal.json');lock=readj(P/'PREPARED_LOCK.json')
for p,h in lock['files'].items():assert sha(readb(P/p))==h,p
for p,h in lock['scripts'].items():assert sha(readb(H/p))==h,p
meta=readj(T/'manifest.json');assert set(meta['refs'])==REFS and meta['parent_sha256']==sha(old)
assert sha(readb(T/'manifest.json'))==proposal['target_manifest_sha256']=='8c40bd581cb7029cfa574519922af098738486f1b2b8a4e948c57ae98b6ddbf3'
for p,h in meta['source_files'].items():assert sha(readb(ROOT/p))==h,p
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8)
inv=np.r_[0,1+((rgb[1:16,None]-rgb[None,17:32])**2).sum(2).argmin(1)].astype(np.uint8)
yy,xx=np.indices((384,384));yy-=160;xx-=160
S=H/'ultimate_special_inputs01';inputmeta=readj(S/'input.json')
for name,h in inputmeta['files'].items():assert sha(readb(S/name))==h
img=Image.open(S/'generated.png').convert('RGBA');assert img.size==(1254,1254)
sample=np.array(img.resize((192,192),Image.Resampling.NEAREST));registered={};counts=collections.Counter()
for col,(form,pal)in enumerate((('before',16),('after',0))):
 for row,n in enumerate((95,97)):
  cell=sample[row*96:(row+1)*96,col*96:(col+1)*96]
  delta=cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[pal+1:pal+16]
  values=(np.square(delta).sum(3).argmin(2)+1).astype(np.uint8);values[cell[:,:,3]<128]=0
  assert not values[[0,-1]].any()and not values[:,[0,-1]].any()
  canvas=np.zeros((384,384),np.uint8);canvas[112:208,112:208]=values
  assert np.array_equal(canvas,png(H/f'ultimate_special_native01/{form}_{n:03}_indices.png'))
  registered[form,n]=canvas;counts['generated_cells_requantized_exact']+=1
HEAD={95:[(-18,-27),(14,-27),(14,4),(9,4),(8,2),(5,1),(4,-2),(-7,-2),(-8,1),(-12,1),(-13,-3),(-18,-3)],97:[(-18,-27),(14,-27),(14,5),(9,5),(7,3),(6,-1),(3,-3),(-2,-3),(-3,-2),(-8,-2),(-9,-4),(-14,-4),(-18,-7)]}
HANDS={95:[[(-18,5),(-12,5),(-11,7),(-12,8),(-18,8)],[(7,5),(12,5),(12,8),(7,8)]],97:[[(-15,-4),(-12,-5),(-10,-4),(-10,0),(-12,2),(-15,1)],[(-3,-3),(1,-3),(2,-2),(2,1),(-1,2),(-3,0)]]}
body={};sources=[];C=H/'ultimate_special_common_probe01'
for n in(95,97):
 bef=registered['before',n].copy();aft=registered['after',n].copy();head=polygons([HEAD[n]]);legs=(yy>=12)&(yy<25);hands=polygons(HANDS[n])
 if n==97:hands&=np.isin(bef,(10,11,12,13))
 common=head|legs|hands;aft[common]=lut[bef][common]
 for name,mask in [('head',head),('legs',legs),('hands',hands),('common',common),('outside',(aft>0)&(bef==0))]:assert np.array_equal(mask,png(C/f'{n:03}_{name}_mask.png')>0)
 assert np.array_equal(bef,png(C/f'before_{n:03}_indices.png'))and np.array_equal(aft,png(C/f'after_{n:03}_indices.png'))
 add=np.zeros(bef.shape,bool)
 if n==97:
  assert bef[164,165]==0 and aft[164,165]==8 and inv[8]==8
  assert registered['after',97][164,165]==8
  bef[164,165]=8;add[164,165]=True
 assert np.array_equal(add,png(T/f'{n:03}_shared_hair_addition_mask.png')>0)
 assert not np.any((aft>0)&(bef==0))and label(aft>0,np.ones((3,3)))[1]==1
 body['before',n],body['after',n]=bef,aft
 sources.append({'ref':n,'common_masks_directly_reconstructed':True,'source_after_hair_cell_shared':n==97,'wholebody_translation':[0,0],'source_outside_common_exact':True})
for form in('before','after'):
 z=body[form,95];assert not z[:,-1].any();v=np.zeros_like(z);v[:,1:]=z[:,:-1];body[form,96]=v
target={}
for n in sorted(REFS):
 bef,aft=body['before',n],body['after',n]
 assert np.array_equal(bef,png(T/f'before_{n:03}_indices.png'))and np.array_equal(aft,png(T/f'after_{n:03}_indices.png'))
 target[n,0]=aft;target[n,5]=np.where(np.all(color(a,bef,16)==color(a,aft),axis=2),0,bef).astype(np.uint8)
 for pb in(6,7,8):target[n,pb]=np.zeros_like(aft)
 for pb in PBS:
  assert np.array_equal(target[n,pb],png(T/f'{n:03}_bank{pb}_indices.png'))and sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]
assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for q in ae:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert (ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']];counts['other_graphics_banks_byte_exact']+=1
 for f,g in zip(ab['frames'],bb['frames']):
  n=f['index'];assert n==g['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert g['tile_count']==32
  else:assert raw(a,gb,n)==raw(b,gb,n)and f['tile_count']==g['tile_count'];counts['non_target_raw_exact']+=1
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as ex:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
    else:raise AssertionError('new invalid layer')
    reserved.append({'ref':n,'layer':pb,'state':'same_render_exception'});continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0])
   counts['reserved_layers_renderable_exact']+=1;reserved.append({'ref':n,'layer':pb,'state':'rendered_exact'});continue
  want=target[n,pb]if n in REFS else a.layer(n,pb)[0]
  assert np.array_equal(b.layer(n,pb)[0],want),(n,pb);counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 oldparts={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
 addr={q['record_offset']for n in REFS if n in oldparts and pb in PBS for q in oldparts[n]}
 for n,op in oldparts.items():
  bp=parts(b,pb,n)
  if pb in PBS and n in REFS:
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0
    v=tile(b,n,t);assert not(t%16==0 and v[:,0].any());assert not(q['flip_y']and t//16==0 and v[0].any());counts['GPU_parts_checked']+=1
  else:
   assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
   overlap=sorted(addr&{q['record_offset']for q in op})
   if overlap:shared.append({'bank':pb,'ref':n,'parent_shared_record_offsets':overlap,'whole_semantics_exact':True})
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   assert np.array_equal(expected,np.asarray(b.composite(n,mask,arm)[0]));counts['partial_RGBA_exact']+=1
 for form,mask,pal in(('before',15,16),('after',0,0)):assert np.array_equal(color(b,body[form,n],pal),np.asarray(b.composite(n,mask)[0]))
for pb in PBS:assert np.array_equal(np.roll(b.layer(95,pb)[0],1,axis=1),b.layer(96,pb)[0])
O.mkdir(exist_ok=True);sheets=[];box=(132,128,188,187);w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*5+10,h*5+26
for mode in('before','after'):
 mask=15 if mode=='before'else 0;board=Image.new('RGB',(cw*3,ch*3),'#263345');dr=ImageDraw.Draw(board)
 for row,n in enumerate(sorted(REFS)):
  for col,(caption,im)in enumerate((('old',a.composite(n,mask)[0]),('new',b.composite(n,mask)[0]),('idle',b.composite(0,mask)[0]))):
   bb=im.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   x,y=col*cw,row*ch;dr.text((x+4,y+4),f'{n} {mode} {caption}',fill='white');v=im.crop(box).resize((w*5,h*5),Image.Resampling.NEAREST);board.paste(v,(x+4,y+22),v)
 p=O/f'{mode}_readback.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==509 and counts['target_layers_exact']==15 and counts['non_target_layers_exact']==1125 and counts['partial_RGBA_exact']==96 and len(reserved)==45
for p,hsh in tracked.items():assert sha((ROOT/p).read_bytes())==hsh,p
report={'passed':True,'scope':'Shibuki Ultimate 95..97 생성4셀→공통부/후폼 머리1셀→15층 독립 읽기 검사','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'prepared_lock_sha256':sha((P/'PREPARED_LOCK.json').read_bytes()),'source_files_count':len(meta['source_files']),'counts':dict(counts),'source_reconstruction':sources,'new96_policy':'새95의 x+1은 원US 기반 신규 제작 정책이다. 현재 부모의 서로 다른95/96을 동일했다고 쓰지 않는다.','old_shared_non_target_compositions':shared,'other_entries_audio_palette_bank_boundaries_exact':True,'part_counts':{str(n):{str(pb):len(parts(b,pb,n))for pb in PBS}for n in sorted(REFS)},'reserved45_layers_preserved':reserved,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'native_MIPS_executed_here':False,'runtime_verified':False,'user_accepted':False,'limitations':['생성4셀의 고정1254→192 전체변환과16색 양자화를 직접 재구성했다. 생성 도구 자체를 재실행한 것은 아니다.','96부분RGBA와 비대상1125층/팔레트 불변을 검사했으며 제작자 전체7296RGBA 재실행이 아니다.','원MIPS/원표 재생·실기·사용자수용은 별도다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))
