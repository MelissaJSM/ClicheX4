"""고정 입력을 읽는 특수 3참조 검사. 제작/패킹 모듈은 호출하지 않는다."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream,bank_offsets,composition_frame,indexed_atlas
D=Path(__file__).parent;H=D.parent/'shibuki_audit';T=H/'standing_special_layers01';P=H/'prepared_standing_special_base01'
O=D/'shibuki_standing3_independent01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
oldpath=H/'prepared_hurt_base01/PL00_U.ARC';newpath=P/'PL00_U.ARC'
old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'
assert sha(new)=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs={95,96,97};counts=collections.Counter()
lockpath=H/'standing_special_locked01/LOCK.json';lock=read(lockpath)
assert sha(lockpath.read_bytes())=='6986519e57cba7896f5419634c0d5291d456eef3e262c5fe7a73bba52a900ff5'
assert lock['parent_sha256']==sha(old)and set(lock['refs'])==refs
for name,h in lock['files'].items():assert sha((ROOT/name).read_bytes())==h;counts['locked_source_files']+=1
plock=read(P/'PREPARED_LOCK.json')
for name,h in plock['files'].items():assert sha((P/name).read_bytes())==h
for name,h in plock['source_scripts'].items():assert sha((H/name).read_bytes())==h
oe,ne=psx_arc(old),psx_arc(new)
assert len(old)==len(new)and old[:2048]==new[:2048]
assert [(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert np.array_equal(np.frombuffer(old,np.uint8)[~allow],np.frombuffer(new,np.uint8)[~allow])
assert a.p==b.p and len(a.g)==len(b.g)==186228 and bank_offsets(a.c)==bank_offsets(b.c)
obases=bank_offsets(a.g,allow_aliases=True);nbases=bank_offsets(b.g,allow_aliases=True)
assert nbases[1]==nbases[2]and nbases[4]==nbases[5]and obases[0]==nbases[0]==56
assert obases[13]==nbases[13]==184744 and a.g[184744:]==b.g[184744:]
assert all(nbases[i]-obases[i]==280 for i in range(1,13))
layout=[];raws={};partial=[]
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
 assert len(ob['frames'])==len(nb['frames'])
 consumed_end=ob['base']+4*len(ob['frames']);changed=[]
 for f,g in zip(ob['frames'],nb['frames']):
  n=f['index'];assert n==g['index'];x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);y=decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128)
  assert x.serialize()==a.g[x.start:x.end]and y.serialize()==b.g[y.start:y.end]
  assert g['offset']%2==0 and 4*len(nb['frames'])<=g['offset']-nb['base']<(1<<20)
  assert g['offset']<y.end<=nb['end'];consumed_end=max(consumed_end,x.end);counts['raw_checked']+=1
  if gb==0 and n in refs:
   assert g['tile_count']==32;raws[n]=y.data
   assert y.data==(H/'standing_special_storage03/joint.raw').read_bytes()
   counts['target_joint_upload_exact']+=1
  else:
   assert x.data==y.data and f['tile_count']==g['tile_count'];counts['non_target_raw_and_count_exact']+=1
  if x.data!=y.data:changed.append(n)
 if gb:
  oldspan=ob['end']-ob['base'];newspan=nb['end']-nb['base'];trim=oldspan-newspan
  assert trim==(280 if gb==12 else 0)
  assert consumed_end<=ob['end']-trim
  assert a.g[ob['base']:ob['end']-trim]==b.g[nb['base']:nb['end']]
  counts['other_bank_header_and_compressed_prefix_exact']+=1
 layout.append({'bank':gb,'old_base':ob['base'],'new_base':nb['base'],'base_delta':nb['base']-ob['base'],'old_span':ob['end']-ob['base'],'new_span':nb['end']-nb['base'],'old_consumed_end':consumed_end,'decoded_changed_refs':changed})
assert layout[0]['new_span']-layout[0]['old_span']==280
assert layout[12]['old_consumed_end']==184462 and int(sum(x!=0 for x in a.g[184464:184744]))==264
assert len({b.banks[0]['frames'][n]['offset']for n in refs})==1
target={}
for n in(95,97):
 for pb in PBS:
  im=Image.open(T/f'{n:03}_bank{pb}_indices.png');v=np.array(im)
  assert im.mode in('P','L')and v.shape==(384,384)and v.max()<16
  assert sha(v.tobytes())==lock['targets'][str(n)][str(pb)];target[n,pb]=v
for pb in PBS:
 v=np.zeros((384,384),np.uint8);v[:,1:]=target[95,pb][:,:-1];target[96,pb]=v

# Native source ownership is recomputed directly, without importing its producer.
Y,X=np.indices((384,384));X-=160;Y-=160
rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:32]],np.int32)
remap=np.argmin(((rgb[:16,None]-rgb[None,17:32])**2).sum(2),axis=1)+1
source_rows=[]
for n in(95,97):
 base=np.array(Image.open(H/f'standing_special_native02/base_{n:03}_indices.png'))
 donor=np.array(Image.open(H/f'standing_special_native02/fourth_{n:03}_indices.png'))
 common=(Y<-5)&~((X>=(1 if n==95 else 0))&(X<13)&(Y>=-22)&(Y<-5))
 overlay=donor.copy();overlay[common]=0;missing=(base>0)&(overlay==0)&~common
 assert set(base[missing])<={2,15};overlay[missing]=remap[base[missing]]
 owner=np.full(base.shape,6,np.uint8);owner[(Y>=13)|((Y>=10)&(X>=-8)&(X<6))]=8
 arm=(Y>=0)&(Y<10)&((X<-9)|(X>=6))if n==95 else ((X<=-8)&(Y>=-5)&(Y<9))|((X>=-3)&(X<4)&(Y>=-3)&(Y<8))
 owner[arm]=7;owner[Y<-5]=5
 assert np.array_equal(owner,np.array(Image.open(T/f'{n:03}_ownership.png')))
 assert np.array_equal(common,np.array(Image.open(T/f'{n:03}_common_head_mask.png'))>0)
 assert np.array_equal(missing,np.array(Image.open(T/f'{n:03}_outline_registration_mask.png'))>0)
 assert np.array_equal(base,target[n,0])
 for pb in PBS[1:]:assert np.array_equal(target[n,pb],np.where(owner==pb,overlay,0));counts['source_owned_layers_rebuilt']+=1
 source_rows.append({'ref':n,'outline_cells':int(missing.sum()),'common_head_cells':int(((base>0)&common).sum()),'layer_counts':{str(pb):int((target[n,pb]>0).sum())for pb in PBS}})
for n in range(237):
 for pb in PBS:
  try:px=b.layer(n,pb)[0]
  except(ValueError,IndexError)as ex:
   assert n not in refs
   try:a.layer(n,pb)
   except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
   else:raise AssertionError('Previously valid layer became invalid')
   partial.append({'ref':n,'parts_bank':pb,'reason':str(ex)});continue
  if n in refs:assert np.array_equal(px,target[n,pb]);counts['authored_layers_exact']+=1
  else:assert np.array_equal(px,a.layer(n,pb)[0]);counts['non_target_layers_exact']+=1
sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  x,y=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
  if pb in PBS and n in refs:
   atlas=np.frombuffer(indexed_atlas(raws[n],32)[0],np.uint8).reshape(-1,256)
   for p in y['parts']:
    t=p['page']*256+p['tile'];assert t<32 and not p['flags']&0x3f
    yy,xx=t//16*16,t%16*16
    if t%16==0:assert not atlas[yy:yy+16,xx].any()
    if p['flip_y']and yy==0:assert not atlas[yy,xx:xx+16].any()
    counts['safe_target_GPU_parts']+=1
  else:assert sem(x)==sem(y);counts['non_target_compositions_exact']+=1
for pb in PBS:
 p95=sem(composition_frame(b.c,pb,95));p96=sem(composition_frame(b.c,pb,96))
 assert [(flags,t,x+1,y)for flags,t,x,y in p95]==p96
 assert np.array_equal(np.roll(a.layer(95,pb)[0],1,axis=1),a.layer(96,pb)[0])
def color(px,start=0):
 words=b.words[start:];table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(words)],np.uint8);return table[px]
def join(n,mask,arm):
 out=color(target[n,0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   layer=color(target[n,pb],32 if pb==7 and arm==2 else 16);z=layer[:,:,3]>0;out[z]=layer[z]
 return out
for n in refs:
 for mask in range(16):
  for arm in(1,2):assert np.array_equal(np.array(b.composite(n,mask,arm)[0]),join(n,mask,arm));counts['partial_RGBA_exact']+=1
nativepath=D/'shibuki_standing3_directory_native01/report.json';native=read(nativepath)
assert native['passed']and native['candidate_sha256']==sha(new)and native['stats']['references']==508 and not native['python_bank_pointer_injection']
assert counts['raw_checked']==508 and counts['non_target_raw_and_count_exact']==505 and counts['authored_layers_exact']==15 and counts['non_target_layers_exact']==1125
assert counts['partial_RGBA_exact']==96 and len(partial)==45
images=[];box=(128,130,192,188);scale=5;cw,ch=328,318
def sheet(name,rows):
 im=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for row,panels in enumerate(rows):
  for col,(label,pic)in enumerate(panels):
   bb=pic.getchannel('A').getbbox();assert bb is None or box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3],(name,label,bb)
   x,y=col*cw,row*ch;dr.text((x+4,y+4),label,fill='white');q=pic.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);im.paste(q,(x+4,y+24),q)
 p=O/name;im.save(p);images.append({'path':rel(p),'sha256':sha(p.read_bytes())})
sheet('comparison.png',[[(f'{n} old base',a.composite(n)[0]),('new base',b.composite(n)[0]),('old Fourth',a.composite(n,15)[0]),('new Fourth',b.composite(n,15)[0]),('idle base',b.composite(0)[0]),('idle Fourth',b.composite(0,15)[0])]for n in sorted(refs)])
for n in(95,97):sheet(f'partial_{n:03}.png',[[(f'{n} mask {mask:X}',b.composite(n,mask)[0])for mask in range(start,start+4)]for start in range(0,16,4)])
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
r={'passed':True,'scope':'시부키 기본/포스 95..97 원화 등록층·자원·고정길이 은행 배치의 독립 읽기 검사. 제작함수 미호출.',
 'parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),'counts':dict(counts),
 'layout':layout,'entry2_size_fixed':186228,'bank0_growth':280,'tail_trim':{'12':280},'tail_nonzero_bytes':264,'bank13_absolute_bytes_exact':True,
 'non_graphics_composition_bytes_exact':True,'target_shared32_stream_exact':True,'ref96_is_ref95_x_plus1_all_five_layers':True,
 'source_ownership_reconstruction':source_rows,'unreconstructed45_layers_preserved':partial,'native_directory_report':rel(nativepath),'native_directory_report_sha256':sha(nativepath.read_bytes()),
 'target_lock_sha256':sha(lockpath.read_bytes()),'prepared_lock_sha256':sha((P/'PREPARED_LOCK.json').read_bytes()),
 'readback_sheets':images,'actual_visual_reviewed':False,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limits':['등록된 새 원화에서 공통 머리/외곽 표본/부분 소유를 직접 재구성했다. 생성 원화의 전체 재양자화 검사는 이번 범위가 아니다.',
 '부분 VRAM 예약참조 45층은 독립 PNG로 완전 복원하지 않는다. 원 raw/count/조립 및 동일한 복원불가 동작을 보존했다.',
 '원 MIPS 검사는 독립 report의 실제 주소 초기화·업로드 큐 범위다. CD 읽기·새 부팅·실제 GPU·게임 실기 또는 cached pointer 재사용을 보증하지 않는다.',
 '은행 재배치는 현재 로컬 후보에 대한 검사이며 새 주소의 사용자 직접 승인으로 기록하지 않는다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'sha256':sha((O/'report.json').read_bytes())}))
