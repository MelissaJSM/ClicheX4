"""Independent fixed-length relocated PL00 reader; no producer modules called."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream,bank_offsets,composition_frame,indexed_atlas
D=Path(__file__).parent;H=D.parent/'shibuki_audit';T=H/'base_run_complete_targets01';P=H/'prepared_base_run01'
O=D/'shibuki_run32_independent01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
oldpath=H/'prepared_dash_base01/PL00_U.ARC';newpath=P/'PL00_U.ARC'
old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
assert sha(new)=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs=set(range(1,33));counts=collections.Counter()
assert sha((T/'LOCK.json').read_bytes())=='44170f9268ab8df6d1aefb26fdaec75981533e16477fa16f1897d7d1d29f3e65'
lock=read(T/'LOCK.json');m=read(T/'targets.json');rows={r['ref']:r for r in m['rows']}
assert sha((T/'targets.json').read_bytes())==lock['target_manifest_sha256'] and set(rows)==refs and m['parent_sha256']==sha(old)
for name,h in lock['files'].items():assert sha((T/name).read_bytes())==h;counts['locked_target_files']+=1
for name,h in m['source_files'].items():assert sha((H/name).read_bytes())==h;counts['registered_source_files']+=1
plock=read(P/'PREPARED_LOCK.json')
for name,h in plock['files'].items():assert sha((P/name).read_bytes())==h
oe,ne=psx_arc(old),psx_arc(new)
assert len(old)==len(new) and old[:2048]==new[:2048]
assert [(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert np.array_equal(np.frombuffer(old,np.uint8)[~allow],np.frombuffer(new,np.uint8)[~allow])
assert a.p==b.p and len(a.g)==len(b.g)==186228 and bank_offsets(a.c)==bank_offsets(b.c)
obases=bank_offsets(a.g,allow_aliases=True);nbases=bank_offsets(b.g,allow_aliases=True)
assert nbases[1]==nbases[2] and nbases[4]==nbases[5] and obases[0]==nbases[0]==56
assert obases[12:]==nbases[12:] and a.g[obases[12]:]==b.g[nbases[12]:]
layout=[];raws={};partial=[]
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
 assert len(ob['frames'])==len(nb['frames'])
 consumed_end=ob['base']+4*len(ob['frames']);changed=[]
 for f,g in zip(ob['frames'],nb['frames']):
  n=f['index'];assert n==g['index'];x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);y=decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128)
  assert x.serialize()==a.g[x.start:x.end] and y.serialize()==b.g[y.start:y.end]
  assert g['offset']%2==0 and 4*len(nb['frames'])<=g['offset']-nb['base']<(1<<20)
  assert g['offset']<y.end<=nb['end'];consumed_end=max(consumed_end,x.end);counts['raw_checked']+=1
  if gb==0 and n in refs:
   assert g['tile_count']<=32;raws[n]=y.data
   if n==1:
    f0=a.banks[0]['frames'][0];assert g['tile_count']==f0['tile_count']==17
    assert y.data==decode_stream(a.g,f0['offset'],f0['limit'],f0['tile_count']*128).data
    counts['ref1_existing_idle0_upload_reuse']+=1
   else:assert f['tile_count']<=g['tile_count'];counts['other_target_upload_count_not_reduced']+=1
  else:
   assert x.data==y.data and f['tile_count']==g['tile_count'];counts['non_target_raw_and_count_exact']+=1
  if x.data!=y.data:changed.append(n)
 if gb:
  oldspan=ob['end']-ob['base'];newspan=nb['end']-nb['base'];trim=oldspan-newspan
  assert trim==({10:344,11:328}.get(gb,0))
  assert consumed_end<=ob['end']-trim
  assert a.g[ob['base']:ob['end']-trim]==b.g[nb['base']:nb['end']]
  counts['other_bank_header_and_compressed_prefix_exact']+=1
 layout.append({'bank':gb,'old_base':ob['base'],'new_base':nb['base'],'base_delta':nb['base']-ob['base'],'old_span':ob['end']-ob['base'],'new_span':nb['end']-nb['base'],'old_consumed_end':consumed_end,'decoded_changed_refs':changed})
assert layout[0]['new_span']-layout[0]['old_span']==672
target={}
for n in range(237):
 for pb in PBS:
  try:px=b.layer(n,pb)[0]
  except(ValueError,IndexError)as ex:
   assert n not in refs
   try:a.layer(n,pb)
   except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
   else:raise AssertionError('Previously valid layer became invalid')
   partial.append({'ref':n,'parts_bank':pb,'reason':str(ex)});continue
  if n in refs:
   p=T/f'{n:03}_bank{pb}_indices.png';im=Image.open(p);want=np.array(im)
   assert im.mode in('P','L') and want.shape==(384,384)and want.max()<16
   assert sha(want.tobytes())==rows[n]['layer_raw_sha256'][str(pb)]
   assert np.array_equal(px,want);target[n,pb]=want;counts['authored_layers_exact']+=1
  else:assert np.array_equal(px,a.layer(n,pb)[0]);counts['non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  x,y=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
  sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
  if pb in PBS and n in refs:
   atlas=np.frombuffer(indexed_atlas(raws[n],b.banks[0]['frames'][n]['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in y['parts']:
    tile=p['page']*256+p['tile'];assert tile<b.banks[0]['frames'][n]['tile_count']and not p['flags']&0x3f
    yy,xx=tile//16*16,tile%16*16
    if tile%16==0:assert not atlas[yy:yy+16,xx].any()
    if p['flip_y']and yy==0:assert not atlas[yy,xx:xx+16].any()
    counts['safe_target_GPU_parts']+=1
  else:assert sem(x)==sem(y);counts['non_target_compositions_exact']+=1
def color(px,start=0):
 words=b.words[start:];table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(words)],np.uint8);return table[px]
def join(n,mask,arm):
 out=color(target[n,0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   layer=color(target[n,pb],32 if pb==7 and arm==2 else 16);z=layer[:,:,3]>0;out[z]=layer[z]
 return out
for n in sorted(refs):
 if n%2==0:
  gunmask=np.array(Image.open(H/f'base_run_shot_inputs01/barrels/{n:03}_mask.png'))>0
  gun=color(np.array(Image.open(H/f'base_run_shot_inputs01/barrels/{n:03}_indices.png')))
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,join(n,mask,arm));counts['partial_RGBA_exact']+=1
   if n%2==0:assert np.array_equal(actual[gunmask],gun[gunmask]);counts['locked_gun_window_RGBA_exact']+=1
for n in(0,141,142):
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0])
for pb in PBS:assert np.array_equal(b.layer(1,pb)[0],a.layer(0,pb)[0])
nativepath=D/'shibuki_run32_directory_native01/report.json';native=read(nativepath)
assert native['passed']and native['candidate_sha256']==sha(new)and native['stats']['references']==508 and not native['python_bank_pointer_injection']
assert counts['raw_checked']==508 and counts['non_target_raw_and_count_exact']==476 and counts['authored_layers_exact']==160 and counts['non_target_layers_exact']==980
assert counts['partial_RGBA_exact']==1024 and counts['locked_gun_window_RGBA_exact']==512 and len(partial)==45
# New independent sheets, all selected frames in identical origin and integer scale.
images=[];box=(116,126,193,188);scale=4;cw,ch=316,276
for page in range(8):
 ns=list(range(page*4+1,page*4+5));im=Image.new('RGB',(cw*6,ch*4),'#263345');dr=ImageDraw.Draw(im)
 for row,n in enumerate(ns):
  panels=[('old base',a.composite(n)[0]),('new base',b.composite(n)[0]),('old Fourth',a.composite(n,15)[0]),('new Fourth',b.composite(n,15)[0]),('idle base',b.composite(0)[0]),('idle Fourth',b.composite(0,15)[0])]
  for col,(label,pic)in enumerate(panels):
   bb=pic.getchannel('A').getbbox();assert bb is None or box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3],(n,bb)
   x,y=col*cw,row*ch;dr.text((x+4,y+4),f'{n:03} {label}',fill='white');q=pic.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);im.paste(q,(x+4,y+24),q)
 path=O/f'readback_{page:02}.png';im.save(path);images.append({'path':rel(path),'sha256':sha(path.read_bytes())})
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
r={'passed':True,'scope':'시부키 기본/포스1..32 원화·자원·고정길이 은행배치의 독립 읽기 검사. 제작함수 미호출.',
 'parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),'counts':dict(counts),
 'layout':layout,'entry2_size_fixed':186228,'bank0_growth':672,'tail_trim':{'10':344,'11':328},'bank12_13_absolute_bytes_exact':True,
 'non_graphics_composition_bytes_exact':True,'protected_0_141_142_exact':True,'ref1_is_existing_idle0_exact':True,'ref1_upload_count_change':{'before':21,'after':17,'reason':'수용idle0의17타일raw/조립을 그대로 재사용'},
 'unreconstructed45_layers_preserved':partial,'native_directory_report':rel(nativepath),'native_directory_report_sha256':sha(nativepath.read_bytes()),
 'target_lock_sha256':sha((T/'LOCK.json').read_bytes()),'prepared_lock_sha256':sha((P/'PREPARED_LOCK.json').read_bytes()),
 'readback_sheets':images,'actual_visual_reviewed':False,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limits':['총열은 고정 입력 정본을 비교했다. 옛 모든개별총열 그림 그대로라는 뜻이 아니다.',
  '일부175..182/105의 부분VRAM·예약참조45층은 독립 PNG로 완전복원하지 않는다. 원raw/count/조립 및 복원불가 동작을 보존했다.',
  '등록160층과 고정source 해시를 확인했으며 이미지생성/정합 전체 과정의 독립 재양자화는 수행하지 않았다.',
  '은행재배치는 기존작업의 로컬가역시험이며 새offset에대한사용자직접승인으로 기록하지 않는다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'sha256':sha((O/'report.json').read_bytes())}))
