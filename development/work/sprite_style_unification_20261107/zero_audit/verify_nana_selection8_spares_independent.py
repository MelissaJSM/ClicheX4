"""나나 UI1..8 identity 사본과 검증된 미소비14칸 사용 독립 reader."""
from pathlib import Path
import json,hashlib,struct,sys,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_nana_selection8/prepared01';O=D/'nana_selection8_spares_independent01'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_ui_atlas import aliased_composition
sha=lambda z:hashlib.sha256(z).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={}
def blob(p):
 z=p.read_bytes();inputs[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
proposal=js(S/'proposal.json');lock=js(S/'PREPARED_LOCK.json');ilock=js(S/'INPUT_LOCK.json');assert len(ilock['files'])==31
for group in(lock,ilock):
 for q in group['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
for k in('parent','candidate','game_old','game_new','source_report','source_code','unused_capacity_native_proof','root_visual','builder_v5_guard'):
 q=proposal[k];assert sha(blob(ROOT/q['path']))==q['sha256']
old=blob(ROOT/proposal['parent']['path']);new=blob(S/'ST0E_U1.ARC')
assert sha(old)=='a577566919c4dad695950347151ce3a57af8c3247172b04c1f36c5ec6f7101b5'
assert sha(new)=='55b5d04d9a3452f2f12fe5ab21024de58c61f43eaa8b078f873ce4c7d2182f52'
a=Archive(blob(ROOT/proposal['game_old']['path']));b=Archive(blob(ROOT/proposal['game_new']['path']));assert a.p==b.p
capacity=js(D/'nana_selection8_capacity01/conclusions.json');assert capacity['input']['sha256']==sha(old)
caprep=js(D/'nana_selection8_capacity01/report.json');native=js(D/'nana_selection8_capacity01/native_initializers.json');assert native['passed']and native['parent_report_sha256']==sha((D/'nana_selection8_capacity01/report.json').read_bytes())
allowed_spares=set(capacity['additional_unconsumed_slots']);assert len(allowed_spares)==28
plan=js(W/'staging_rn_v37.json');assets,_=read_disc(ROOT/plan['source_bin'],['COL0E_U1.ARC']);pal=entry(assets['COL0E_U1.ARC'],5);assert pal[512:544]==a.p[:32]==b.p[:32]
assert len(old)==len(new);oe,ne=psx_arc(old),psx_arc(new)
assert[(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne]
permitted=np.zeros(len(old),bool)
for q in oe:
 t=int(q['type'],16)
 if t not in(10,0x10102):assert entry(old,t)==entry(new,t)
 else:permitted[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~permitted)
og,ng=entry(old,0x10102),entry(new,0x10102);op,np_=entry(old,10),entry(new,10)
assert len(og)==len(ng)==116736 and len(op)==len(np_)and og[:90112]==ng[:90112]
assert sha(og)==capacity['texture_entry_sha256']and sha(og[90112:])==capacity['X_tail_sha256']
starts=struct.unpack('<3I',entry(old,12));assert starts==(0,40960,90112)and entry(old,12)==entry(new,12)
bc=struct.unpack_from('<I',op)[0]//4;ob=struct.unpack_from('<'+'I'*bc,op);nb=struct.unpack_from('<'+'I'*bc,np_);assert ob==nb and bc==3 and op[:ob[2]]==np_[:nb[2]]
def tile(tex,t):
 z=np.zeros((16,16),np.uint8)
 for y in range(16):
  for x in range(16):
   off=(t//16*16+y)*128+t%16*8+x//2;assert 0<=off<len(tex);z[y,x]=(tex[off]>>(4*(x%2)))&15
 return z
def static(g,p,bank,n):
 tex=g[starts[bank]:];c=aliased_composition(p,bank,n);idx=np.zeros((384,384),np.uint16);out=np.zeros((384,384,4),np.uint8)
 for q in c['parts']:
  assert not q['unknown_flags'];z=tile(tex,q['page']*256+q['tile'])
  if q['flip_x']:z=z[:,::-1]
  if q['flip_y']:z=z[::-1]
  x,y=q['x']+160,q['y']+160;assert 0<=x<=368 and 0<=y<=368;hit=z>0;idx[y:y+16,x:x+16][hit]=z[hit]+16*q['clut']
  if bank in(0,2):
   row=(16 if bank==2 else 0)+q['clut'];words=struct.unpack_from('<16H',pal,row*32);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]+[255]for w in words],np.uint8);colors[0]=0;out[y:y+16,x:x+16][hit]=colors[z][hit]
 return idx,out,c
mapping={i:i+84 for i in range(1,9)};counts=collections.Counter();protected=set();oldtarget=set();newtarget=set();frames=[];pictures={};gpu=[]
for bank in range(3):
 total=aliased_composition(op,bank,0)['bank_frame_count'];assert total==aliased_composition(np_,bank,0)['bank_frame_count']
 for n in range(total):
  oi,oc,ops=static(og,op,bank,n);ni,nc,nps=static(ng,np_,bank,n);counts['all_UI_frames']+=1
  if bank==2 and n in mapping:
   ref=mapping[n];assert np.array_equal(oi,a.layer(ref)[0])and np.array_equal(ni,b.layer(ref)[0])
   assert np.array_equal(oc,np.array(a.composite(ref,0)[0]))and np.array_equal(nc,np.array(b.composite(ref,0)[0]))
   oldtarget.update(q['page']*256+q['tile']for q in ops['parts']);newtarget.update(q['page']*256+q['tile']for q in nps['parts'])
   for q in nps['parts']:
    t=q['page']*256+q['tile'];z=tile(ng[90112:],t)
    assert not(t%16==0 and z[:,0].any())and not((704+t)%176<16 and z[0].any())
    assert q['clut']==0;gpu.append({'ref':n,'tile':t,'xy':[q['x'],q['y']],'flip_x':q['flip_x'],'flip_y':q['flip_y'],'mode1_UV_guard_passed':True})
   frames.append({'UI':n,'game':ref,'dx':0,'dy':0,'whole_sprite_mirror':False,'index_RGBA_exact':True,'old_parts':len(ops['parts']),'new_parts':len(nps['parts'])})
   pictures[n]=(oc,nc,np.array(b.composite(ref,0)[0]));counts['target_UI_frames']+=1
  else:
   assert np.array_equal(oi,ni)and np.array_equal(oc,nc)and len(ops['parts'])==len(nps['parts'])
   for q,w in zip(ops['parts'],nps['parts']):
    assert op[q['record_offset']:q['record_offset']+4]==np_[w['record_offset']:w['record_offset']+4];counts['non_target_records']+=1
    if bank==2:protected.add(q['page']*256+q['tile'])
   counts['non_target_UI_frames']+=1
   if bank==2:counts['non_target_X_UI_frames']+=1
owned=oldtarget-protected;assert len(owned)==39 and oldtarget&protected=={0,1,2,16,17}
assert owned==set(caprep['exclusive_target_tiles'])and set(caprep['all_banks_unconsumed_X_tiles'])>=allowed_spares
changed=[]
for t in range(208):
 same=np.array_equal(tile(og[90112:],t),tile(ng[90112:],t))
 if not same:changed.append(t)
 if t not in owned|allowed_spares:assert same
used_spares=newtarget-owned;assert used_spares==set(proposal['spare_slots_used'])and used_spares<=allowed_spares
assert len(changed)==53 and len(gpu)==58 and newtarget<=owned|allowed_spares
assert counts['all_UI_frames']==80 and counts['non_target_UI_frames']==72 and counts['non_target_X_UI_frames']==17
for t in(0,1,2,16,17):assert np.array_equal(tile(og[90112:],t),tile(ng[90112:],t))
O.mkdir(exist_ok=False);sheets=[]
for start in(1,3,5,7):
 cw,ch=360,320;bd=Image.new('RGB',(cw*3,ch*2),'#263345');dr=ImageDraw.Draw(bd)
 for row,n in enumerate((start,start+1)):
  for col,(title,z)in enumerate(zip(('old UI','new UI','new game identity'),pictures[n])):
   im=Image.fromarray(z);bb=im.getbbox();box=(118,124,202,194);assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   im=im.crop(box).resize((336,280),Image.Resampling.NEAREST);x,y=col*cw,row*ch;dr.text((x+4,y+3),f'{n} / {mapping[n]} {title}',fill='white');bd.paste(im,(x+8,y+28),im)
 p=O/f'comparison_{start:02}.png';bd.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
for p,h in inputs.items():assert sha((ROOT/p).read_bytes())==h,p
r={'passed':True,'scope':'Nana UI1..8 고정 atlas 사본8의 원점/공유5/미소비14슬롯 독립 읽기','candidate':rel(S/'ST0E_U1.ARC'),'candidate_sha256':sha(new),'parent_sha256':sha(old),'new_game_sha256':sha(b.data),'locked_inputs':31,'counts':dict(counts),'frames':frames,'old_exclusive39':sorted(owned),'shared5_preserved':[0,1,2,16,17],'additional28_allowed':sorted(allowed_spares),'additional14_used':sorted(used_spares),'changed53_tiles':changed,'all_other155_whole_tiles_exact':True,'GPU58_parts':gpu,'other_texture_prefix90112_exact':True,'all_entry_and_bank_boundaries_unchanged':True,'non_target_geometry_records_RGBA_exact':True,'RN_return19_20_dy0_and_Zero_banks_preserved':True,'native_capacity_proof':{'path':rel(D/'nana_selection8_capacity01/native_initializers.json'),'sha256':sha((D/'nana_selection8_capacity01/native_initializers.json').read_bytes()),'candidate_entry12_and_bank_starts_exact':True,'executed_here':False},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':inputs,'producer_functions_called':False,'new_MIPS_executed':False,'runtime_verified':False,'limits':['새 선택화면 아트 생성이 아니라 RN37의 이미 동결된 게임85..92를 dx0/dy0 그대로 저장한 사본이다. 58개 조립으로 바뀐 것은 대상8에 한정된다.','원loader→14종 initializer는 앞선 별도 용량보고에서 실행했다. 이번 후보는 그 디렉터리/길이/은행 위치 그대로이며 새GPU 화면실기는 아직 아니다.','공유5를 재사용하거나 바꾸지 않았다. 기존독점39와 전은행 미소비28중14칸을 사용했고 나머지 전체155칸은256nibble exact다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'changed_tiles':len(changed),'gpu':len(gpu)}))
