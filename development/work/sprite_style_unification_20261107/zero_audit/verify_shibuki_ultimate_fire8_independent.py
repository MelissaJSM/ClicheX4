"""Ultimate85..92 최종40층/등록출처/원83효과 독립 reader. 제작함수 미호출."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,render
P=H/'prepared_standing_fire_ultimate01';T=H/'ultimate_standing_fire_targets01';O=D/'shibuki_ultimate_fire8_independent01'
PBS=(0,5,6,7,8);REFS=set(range(85,93));RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
oldp=H/'prepared_standing_special_ultimate01/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=blob(oldp),blob(newp)
assert sha(old)=='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'
assert sha(new)=='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
a,b=Archive(old),Archive(new);proposal=js(P/'proposal.json');lock=js(P/'PREPARED_LOCK.json');inputs=js(P/'INPUT_LOCK.json');meta=js(T/'manifest.json')
assert sha(blob(P/'INPUT_LOCK.json'))==proposal['target_lock_sha256']==lock['target_lock_sha256']
assert sha(blob(T/'manifest.json'))==proposal['target_manifest_sha256']==inputs['target_manifest_sha256']
assert len(inputs['files'])==390 and set(inputs['refs'])==REFS and inputs['parent_sha256']==sha(old) and inputs['candidate_sha256']==sha(new)
for p,h in lock['files'].items():assert sha(blob(P/p))==h,p
for p,h in lock['source_scripts'].items():assert sha(blob(H/p))==h,p
for p,h in inputs['files'].items():assert sha(blob(ROOT/p))==h,p
for p,h in meta['source_files'].items():assert sha(blob(ROOT/p))==h,p
counts=collections.Counter();target={};source_rows=[];guns={}
for n in sorted(REFS):
 for pb in PBS:
  z=png(T/f'{n:03}_bank{pb}_indices.png');assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)];target[n,pb]=z
  if n!=88:assert np.array_equal(z,png(H/meta['registered_sources'][str(n)]/f'{n:03}_bank{pb}_indices.png'))
 if n!=88:
  folder=H/meta['registered_sources'][str(n)];gun=png(folder/f'{n:03}_gun_indices.png');guard=png(folder/f'{n:03}_gun_guard_mask.png')>0
  assert np.all(guard[gun>0]);guns[n]=(gun,guard)
  for form,mask in(('before',15),('after',0)):
   im=png(folder/f'{form}_{n:03}.png');assert np.array_equal(im,np.array(b.composite(n,mask)[0]));counts['registered_full_RGBA_exact']+=1
  source_rows.append({'ref':n,'registered_source':rel(folder),'five_layers_and_two_full_RGBA_exact':True,'gun_opaque':int((gun>0).sum()),'gun_guard':int(guard.sum())})
original=Archive(read_disc(ROOT/'MegaMan X4.bin',['PL02_U.ARC'])[0]['PL02_U.ARC'])
assert sha(original.data)==sha(blob(T/'original_PL02_U.ARC'))=='fa8accf20e35634120fd4fc59bac1f31b0fdadaf639b06a783e92189e93c8042'
ops=[q for q in parts(original,0,88)if q['tile']in(7,8)];assert len(ops)==2
fx=render(original,88,0,ops);assert set(np.unique(fx))=={0,12}and np.count_nonzero(fx)==83;fx[fx==12]=6
assert np.array_equal(fx,png(T/'088_effect_indices.png')) and np.array_equal(a.layer(88,0)[0][fx>0],fx[fx>0])
effects=[]
for t in(7,8):
 orig=tile(original,88,t);mapped=np.where(orig==12,6,orig);assert set(np.unique(orig))<={0,12}
 assert np.array_equal(mapped,png(T/f'088_effect_tile{t}.png'))and np.array_equal(mapped,tile(b,88,t))
 assert sha(orig.tobytes())==meta['effect88']['tiles'][str(t)]['original_all256_nibble_sha256']
 effects.append({'tile':t,'original256nibble_sha256':sha(orig.tobytes()),'candidate256nibble_sha256':sha(mapped.tobytes()),'only_color12_to6':True})
assert [sig(q)for q in parts(b,0,88)if q['tile']in(7,8)]==[sig(q)for q in ops]
for pb in PBS:
 z=np.zeros_like(target[89,pb]);z[:,:-1]=target[89,pb][:,1:];z[fx>0]=fx[fx>0]if pb==0 else 0
 assert np.array_equal(z,target[88,pb])
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne]
allow=np.zeros(len(old),bool)
for q in oe:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert bf['tile_count']==32
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
   assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0]);reserved.append([n,pb,'rendered_exact']);continue
  want=target[n,pb]if n in REFS else a.layer(n,pb)[0];assert np.array_equal(b.layer(n,pb)[0],want),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 allparts={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
 addresses={q['record_offset']for n in REFS if n in allparts and pb in PBS for q in allparts[n]}
 for n,op in allparts.items():
  bp=parts(b,pb,n)
  if pb in PBS and n in REFS:
   for q in bp:
    t=q['tile']+q['page']*256;assert t<32 and not q['unknown_flags'];z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(q['flip_y']and t//16==0 and z[0].any());counts['GPU_parts_checked']+=1
  else:
   assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
   overlap=sorted(addresses&{q['record_offset']for q in op})
   if overlap:shared.append({'bank':pb,'ref':n,'parent_shared_records':overlap,'preserved':True})
groups=[]
for n in sorted(REFS):
 oldowners=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']];newowners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert set(oldowners)<=REFS and set(newowners)<=REFS
 groups.append({'ref':n,'old':oldowners,'new':newowners,'tile_count':32})
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);hit=v[:,:,3]>0;expected[hit]=v[hit]
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(expected,actual);counts['partial_RGBA_exact']+=1
   if n==88:assert np.array_equal(actual[fx>0],color(b,fx)[fx>0]);counts['effect83_RGBA_exact']+=1
   else:
    gun,guard=guns[n];assert np.array_equal(actual[guard],color(b,gun)[guard]),('gun',n,mask,arm);counts['gun_guard_RGBA_exact']+=1
nativep=H/'ultimate_standing_fire_components_native_checks.json';native=js(nativep);nr=native['resources']['PL02_U.ARC'];assert native['passed']and nr['candidate_sha256']==sha(new)
for bank in nr['banks']:
 for q in bank['native_decoder_checks']:assert q['decoded_sha256']==sha(raw(b,bank['bank'],q['frame']));counts['existing_native_decodes_bound']+=1
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==504 and counts['target_layers_exact']==40 and counts['non_target_layers_exact']==1100 and counts['partial_RGBA_exact']==256
O.mkdir(exist_ok=False);sheets=[];box=(120,121,195,187);cw,ch=310,290
for i in range(4):
 im=Image.new('RGB',(cw*4,ch*2),'#263345');dr=ImageDraw.Draw(im)
 for row,n in enumerate((85+i*2,86+i*2)):
  for col,(caption,pic)in enumerate((('old before',a.composite(n,15)[0]),('new before',b.composite(n,15)[0]),('old after',a.composite(n,0)[0]),('new after',b.composite(n,0)[0]))):
   bb=pic.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   dr.text((col*cw+3,row*ch+3),f'{n} {caption}',fill='white');v=pic.crop(box).resize((300,264),Image.Resampling.NEAREST);im.paste(v,(col*cw+3,row*ch+22),v)
 p=O/f'readback_{i}.png';im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
r={'passed':True,'scope':'Shibuki Ultimate85..92 등록7몸체 양폼→40층 및 원83효과→최종ARC 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha((P/'INPUT_LOCK.json').read_bytes()),'locked_inputs':390,'counts':dict(counts),'source_rows':source_rows,'effect88':{'original_US_full_tiles':effects,'geometry_two_records_exact':True,'color12_to6':True,'new89_shift':[-1,0],'old_parent_body198_difference_not_copied':True},'stream_groups':groups,'non_target_shared_records':shared,'reserved_layers':reserved,'other_entries_audio_palette_all_bank_bounds_exact':True,'native_report':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'executed_here':False},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'overall_complete':False,'limits':['생성14셀과 국소원화의 재양자화를 이번 reader가 다시 수행한 것은 아니다. 잠금390개·최종등록7몸체 양폼·40층·총 보호창과 원효과 전체2타일을 직접 대조했다.','원US의 효과 관계와 새89 X−1 제작 정책을 구분한다. 현재 부모88 몸체198셀 차이를 원래부터 같았다고 주장하지 않는다.','256부분·비대상1100층을 검사했다. 제작자7296RGBA를 중복 재실행한 것은 아니다. 원MIPS8은 기존 보고의 decoded hash를 결속했고 실기/사용자수용은 별도다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
