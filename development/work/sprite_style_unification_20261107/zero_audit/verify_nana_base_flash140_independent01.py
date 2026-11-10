"""현재 idle 알파→140 부분 섬광의 독립 읽기. 제작 함수 호출 없음."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit';U=N/'base_flash140_restore01';P=U/'packed_flash_candidate_v1';O=D/'nana_base_flash140_independent01';assert not O.exists()
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};counts=collections.Counter();PBS=(0,5,6,7,8);RESERVED={105,*range(175,183)}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
oldp=N/'base_nova_repaint/packed_nova_candidate_v1/PL00_U.ARC';newp=P/'PL00_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3'
assert sha(new)=='2822a9387a69119e6a3f6ba0f3cc830676280309b139494221940e0e9a005c59'
lock=js(P/'INPUT_FROZEN.json');assert sha(blob(P/'INPUT_FROZEN.json'))=='ff245e9b24bca7ff18858a9ae6321228b840e29b4bebe30ba688f87f9e6d4690'and len(lock['files'])==31
assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)
for row in lock['files']:assert sha(blob(R/row['path']))==row['sha256'],row['path']
proposal=js(P/'proposal.json');verification=js(P/'verification.json');assert verification['after']==sha(new)
idle=a.layer(0,0)[0];flash=a.layer(140,0)[0];fx=(flash>0)&(idle==0)
assert (flash[flash>0]==13).all()and(flash[idle>0]==13).all()and int(fx.sum())==46
assert a.words[13]==a.words[29]==a.words[45]
targets={0:flash.copy()};extras=[]
for pb in PBS[1:]:
 mask=(a.layer(0,pb)[0]>0)&(idle==0);targets[pb]=np.where(mask,13,0).astype(np.uint8)
 extras.append({'layer':pb,'alpha_pixels':int(mask.sum()),'world_coordinates':[[int(x-160),int(y-160)]for y,x in np.argwhere(mask)]})
assert [r['alpha_pixels']for r in extras]==[72,3,1,73]
for pb,z in targets.items():assert np.array_equal(z,png(P/f'layer{pb}_140.png'))and np.array_equal(z,b.layer(140,pb)[0])
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
groups=[]
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index']and af['tile_count']==bf['tile_count'];counts['raw_checked']+=1
  if gb==0 and n==140:assert bf['tile_count']==10
  else:assert raw(a,gb,n)==raw(b,gb,n);counts['non_target_raw_exact']+=1
  og=[q['index']for q in ab['frames']if q['offset']==af['offset']];ng=[q['index']for q in bb['frames']if q['offset']==bf['offset']];assert og==ng
  if gb==0 and n==140:groups=ng
assert groups==[140]
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
  assert np.array_equal(b.layer(n,pb)[0],targets[pb]if n==140 else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n==140 else'non_target_layers_exact']+=1
oldusers=collections.defaultdict(set);newusers=collections.defaultdict(set);edge_exceptions=[]
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  for q in op:oldusers[q['record_offset']].add((pb,n))
  for q in bp:newusers[q['record_offset']].add((pb,n))
  if pb in PBS and n==140:
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<10 and p['unknown_flags']==0;z=tile(b,140,t)
    assert not(t%16==0 and z[:,0].any())
    if p['flip_y']and t//16==0 and z[0].any():
     assert sig(p)in[sig(q)for q in op]and np.array_equal(z,tile(a,140,t));edge_exceptions.append({'bank':pb,'record':list(sig(p)),'parent_tile_exact':True})
    counts['GPU_parts']+=1
  else:assert[sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
oldbody=[sig(q)for q in parts(a,0,140)];newbody=[sig(q)for q in parts(b,0,140)]
assert newbody==[(flags,6 if t==1 else t,x,y)for flags,t,x,y in oldbody]
assert np.array_equal(tile(b,140,6),tile(a,140,1))and np.array_equal(tile(b,140,8),tile(a,140,8))
changedtiles=[t for t in range(10)if not np.array_equal(tile(a,140,t),tile(b,140,t))];assert changedtiles==[0,1,6,7,9]
assert[sig(p)for p in parts(b,5,140)]==[(0,1,-4,-23)]
headowners=[n for n in range(237)if n!=140 and(0,1,-4,-23)in[sig(p)for p in parts(a,5,n)]];assert headowners
shared_old=sorted({q for p in parts(a,0,140)for q in oldusers[p['record_offset']]if q!=(0,140)})
shared_new=sorted({q for p in parts(b,0,140)for q in newusers[p['record_offset']]if q!=(0,140)})
assert any(n in(208,209)for pb,n in shared_old)
for n in range(208,213):
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0])and[sig(p)for p in parts(a,pb,n)]==[sig(p)for p in parts(b,pb,n)]
maskcases=[]
for mask in range(16):
 for arm in(1,2):
  expected=color(a,targets[0])
  for bit,pb in((8,8),(1,5),(4,7),(2,6)):
   if mask&bit:z=color(a,targets[pb],32 if pb==7 and arm==2 else 16);m=z[:,:,3]>0;expected[m]=z[m]
  currentidle=np.array(a.composite(0,mask,arm)[0]);alpha=currentidle[:,:,3]>0;direct=np.where(alpha|fx,13,0).astype(np.uint8);actual=np.array(b.composite(140,mask,arm)[0]);assert np.array_equal(actual,expected)and np.array_equal(actual,color(a,direct))
  assert np.array_equal(actual[fx],np.array(a.composite(140,0,arm)[0])[fx]);counts['partial_RGBA_exact']+=1
  maskcases.append({'mask':mask,'arm':arm,'idle_alpha_pixels':int(alpha.sum()),'flash_alpha_pixels':int((direct>0).sum()),'added_outside_oldflash_pixels':int(((direct>0)&(flash==0)).sum()),'RGBA_sha256':sha(actual.tobytes())})
assert np.array_equal(np.array(a.composite(140,0)[0]),np.array(b.composite(140,0)[0]))
native=js(U/'native_components_v1_native_checks.json');nr=native['resources']['PL00_U.ARC'];assert native['passed']and nr['candidate_sha256']==sha(new)and nr['GPU_part_edge_checks']==18
for row in nr['banks'][0]['native_decoder_checks']:assert row['frame']==140 and row['decoded_sha256']==sha(raw(b,0,140))
repro=js(P/'reproduction.json');assert repro['passed']and repro['candidate_sha256']==sha(new)and repro['separate_process_reproduction_exact']and len(repro['rejected_inputs'])==7 and all(q['rejected']for q in repro['rejected_inputs'])
assert [counts[k]for k in('raw_checked','non_target_raw_exact','target_layers_exact','non_target_layers_exact','non_target_compositions_exact','GPU_parts','partial_RGBA_exact')]==[508,507,5,1135,1782,18,32],counts
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows,scale=5):
 boxes=[im.getbbox()for row in rows for _,im in row if im.getbbox()];crop=(min(z[0]for z in boxes)-3,min(z[1]for z in boxes)-3,max(z[2]for z in boxes)+3,max(z[3]for z in boxes)+3);w,h=crop[2]-crop[0],crop[3]-crop[1];cw,ch=w*scale+10,h*scale+25;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(out)
 for y,row in enumerate(rows):
  for x,(caption,im)in enumerate(row):
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=im.crop(crop).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(v,(x*cw+5,y*ch+22),v)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':crop,'integer_scale':scale})
sheet('readback.png',[[('base idle',a.composite(0,0)[0]),('base flash old',a.composite(140,0)[0]),('base flash new',b.composite(140,0)[0])],[('Fourth idle',a.composite(0,15)[0]),('Fourth old flash',a.composite(140,15)[0]),('Fourth new flash',b.composite(140,15)[0])]])
for i in range(4):sheet(f'partial_{i}.png',[[(f'idle mask{m}',a.composite(0,m)[0]),(f'flash mask{m}',b.composite(140,m)[0])]for m in range(i*4,i*4+4)],4)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'passed':True,'scope':'Nana 기본/포스140 현재idle 각마스크 알파+원46효과 독립 재구성/부분/공유 보존 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'counts':dict(counts),'source_new_art':False,'extra_alpha_by_layer':extras,'palette_light_words_equal':[int(a.words[i])for i in(13,29,45)],'mask_cases':maskcases,'base140_RGBA_exact':True,'effect46_world_indices_RGBA_exact':True,'effect_tile8_full256_exact':True,'raw_owners':[140],'tile_count':10,'changed_tiles':changedtiles,'body_tile1_to6_full256_exact':True,'head_template_record':[0,1,-4,-23],'existing_head_template_owners':headowners,'old_body_record_outside_owners':shared_old,'new_body_record_outside_owners':shared_new,'protected208_212_all_raw_layers_semantic_records_exact':True,'non_target_composition_byte_records_equal':True,'entry_bank_boundaries_palette_audio_exact':True,'reserved_layers':reserved,'GPU_preserved_parent_edge_exceptions':edge_exceptions,'native_producer1_raw_hash_bound':True,'reproduction_producer1_7reject_bound':True,'new_MIPS_execution':False,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'limits':['32개 대상 부분RGBA와1135비대상층/1782비대상 의미레코드를 직접 확인했다.7296전체RGBA 추가실행은 제작자 별도 근거이다.','원US140도 부분층이 비어 있으므로 원US복원이 아닌 현재 선택의상 실루엣 파생 정책이다.','208..212는 별도dispatcher의 분신소멸이며 본체만 그리는 기존 공유 정책을 보호했다.','원MIPS/재현거부는 후보해시와 직접raw에 결속한 기존 실행근거이며 이reader에서 새로 실행하지 않았다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'raw_sha256':sha(raw(b,0,140)),'mask15':maskcases[-1]}))
