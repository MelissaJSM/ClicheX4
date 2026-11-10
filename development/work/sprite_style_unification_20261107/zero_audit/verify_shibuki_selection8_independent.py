"""선택8 새 고정 atlas의 직접 픽셀/타일/flip/원점 독립 reader."""
from pathlib import Path
import json,hashlib,struct,sys,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';S=H/'prepared_selection_standing01';O=D/'shibuki_selection8_independent01'
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
proposal=js(S/'proposal.json');lock=js(S/'PREPARED_LOCK.json')
for q in lock['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
for k in('parent','candidate','game_old','game_new','source_report','source_code'):
 q=proposal[k];assert sha(blob(ROOT/q['path']))==q['sha256']
old=blob(ROOT/proposal['parent']['path']);new=blob(S/'ST0E_U1.ARC')
assert sha(old)=='ea2167e98f8ae045c4353cca18cc571614e34949160cd85cc14ac9a6cb8e1c54'
assert sha(new)=='47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'
a=Archive(blob(ROOT/proposal['game_old']['path']));b=Archive(blob(ROOT/proposal['game_new']['path']))
assert sha(b.data)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
plan=js(W/'staging_br_v22.json');assets,_=read_disc(ROOT/plan['source_bin'],['COL0E_U1.ARC']);pal=entry(assets['COL0E_U1.ARC'],5)
assert pal[512:544]==a.p[:32]==b.p[:32]
assert len(old)==len(new);oe,ne=psx_arc(old),psx_arc(new)
assert[(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne]
for q in oe:
 t=int(q['type'],16)
 if t not in(10,0x10102):assert entry(old,t)==entry(new,t)
og,ng=entry(old,0x10102),entry(new,0x10102);op,np_=entry(old,10),entry(new,10)
assert len(og)==len(ng)and len(op)==len(np_)and og[:90112]==ng[:90112]
starts=struct.unpack('<3I',entry(old,12));assert starts==(0,40960,90112)
bc=struct.unpack_from('<I',op)[0]//4;ob=struct.unpack_from('<'+'I'*bc,op);nb=struct.unpack_from('<'+'I'*bc,np_);assert ob==nb and bc==3
assert op[:ob[2]]==np_[:nb[2]]
def tile(tex,t):
 z=np.zeros((16,16),np.uint8)
 for y in range(16):
  for x in range(16):
   off=(t//16*16+y)*128+t%16*8+x//2;assert 0<=off<len(tex);z[y,x]=(tex[off]>>(4*(x%2)))&15
 return z
def static(g,p,bank,n):
 tex=g[starts[bank]:(starts[bank+1]if bank<2 else len(g))];c=aliased_composition(p,bank,n);idx=np.zeros((384,384),np.uint16);out=np.zeros((384,384,4),np.uint8)
 for q in c['parts']:
  assert not q['unknown_flags'];z=tile(tex,q['page']*256+q['tile'])
  if q['flip_x']:z=z[:,::-1]
  if q['flip_y']:z=z[::-1]
  x,y=q['x']+160,q['y']+160;assert 0<=x<=368 and 0<=y<=368;hit=z>0;idx[y:y+16,x:x+16][hit]=z[hit]+16*q['clut']
  if bank in(0,2):
   row=(16 if bank==2 else 0)+q['clut'];words=struct.unpack_from('<16H',pal,row*32);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]+[255]for w in words],np.uint8);colors[0]=0;out[y:y+16,x:x+16][hit]=colors[z][hit]
 return idx,out,c
mapping={1:(85,-1),2:(86,0),3:(87,0),4:(88,0),5:(89,0),6:(90,-1),7:(91,-2),8:(92,0)}
def orient(z,dy):
 out=np.zeros_like(z);y,x=np.nonzero(z[:,:,3]>0 if z.ndim==3 else z>0);out[y+dy,x]=z[y,x];return out
counts=collections.Counter();owned=set();protected=set();oldtarget=set();newtarget=set();frames=[];pictures={};gpu=[]
for bank in range(3):
 total=aliased_composition(op,bank,0)['bank_frame_count'];assert total==aliased_composition(np_,bank,0)['bank_frame_count']
 for n in range(total):
  oi,oc,ops=static(og,op,bank,n);ni,nc,nps=static(ng,np_,bank,n);counts['all_UI_frames']+=1
  if bank==2 and n in mapping:
   ref,dy=mapping[n];assert np.array_equal(oi,orient(a.layer(ref)[0],dy))and np.array_equal(ni,orient(b.layer(ref)[0],dy))
   assert np.array_equal(oc,orient(np.array(a.composite(ref,0)[0]),dy))and np.array_equal(nc,orient(np.array(b.composite(ref,0)[0]),dy))
   oldtarget.update(q['page']*256+q['tile']for q in ops['parts']);newtarget.update(q['page']*256+q['tile']for q in nps['parts'])
   for q in nps['parts']:
    t=q['page']*256+q['tile'];z=tile(ng[90112:],t)
    # PS1 endpoint U/V decrement at flipped rectangle edges must not wrap to
    # the previous tile. The fixed-atlas zero guards preserve those endpoints.
    assert not(t%16==0 and z[:,0].any())and not(t%256<16 and z[0].any())
    assert q['clut']==0
    gpu.append({'UI_ref':n,'tile':t,'xy':[q['x'],q['y']],'flip_x':q['flip_x'],'flip_y':q['flip_y'],'safe_UV_endpoint':True})
   frames.append({'UI':n,'game':ref,'dx':0,'dy':dy,'whole_sprite_mirror':False,'old_and_new_index_RGBA_exact':True,'old_parts':len(ops['parts']),'new_parts':len(nps['parts'])})
   pictures[n]=(oc,nc,orient(np.array(b.composite(ref,0)[0]),dy));counts['target_UI_frames']+=1
  else:
   assert np.array_equal(oi,ni)and np.array_equal(oc,nc)
   assert len(ops['parts'])==len(nps['parts'])
   for q,w in zip(ops['parts'],nps['parts']):
    assert op[q['record_offset']:q['record_offset']+4]==np_[w['record_offset']:w['record_offset']+4];counts['non_target_records']+=1
    if bank==2:protected.add(q['page']*256+q['tile'])
   counts['non_target_UI_frames']+=1
   if bank==2:counts['non_target_X_UI_frames']+=1
owned=oldtarget-protected;assert len(owned)==49 and oldtarget&protected=={4}and not tile(og[90112:],4).any()
alltiles=range(len(og[90112:])//128);changed=[]
for t in alltiles:
 same=np.array_equal(tile(og[90112:],t),tile(ng[90112:],t))
 if t not in owned:assert same
 if not same:changed.append(t)
assert set(changed)<=owned and newtarget<=owned|{4}and len(newtarget-{4})==48 and len(gpu)==52
counts['target_GPU_parts']=len(gpu);counts['flipped_target_parts']=sum(q['flip_x']or q['flip_y']for q in gpu)
O.mkdir(exist_ok=True);sheets=[]
for start in(1,3,5,7):
 cw,ch=360,320;bd=Image.new('RGB',(cw*3,ch*2),'#263345');dr=ImageDraw.Draw(bd)
 for row,n in enumerate((start,start+1)):
  for col,(title,z)in enumerate(zip(('old UI','new UI','new game transformed'),pictures[n])):
   im=Image.fromarray(z).crop((118,124,202,194)).resize((336,280),Image.Resampling.NEAREST);x,y=col*cw,row*ch;dr.text((x+4,y+3),f'{n} / {mapping[n][0]} {title}',fill='white');bd.paste(im,(x+8,y+28),im)
 path=O/f'comparison_{start:02}.png';bd.save(path);sheets.append({'path':rel(path),'sha256':sha(path.read_bytes()),'actually_viewed':False})
for p,h in inputs.items():assert sha((ROOT/p).read_bytes())==h
r={'passed':True,'scope':'선택1..8 고정 atlas의 새85..92 사본 독립 읽기; 미술/실기 별도','candidate':rel(S/'ST0E_U1.ARC'),'candidate_sha256':sha(new),'parent_sha256':sha(old),'new_game_sha256':sha(b.data),'counts':dict(counts),'frames':frames,'exclusive_target_tiles':sorted(owned),'protected_shared_blank_tile4_exact':True,'changed_tiles':changed,'nonowned_whole_tiles_exact':len(list(alltiles))-len(owned),'all_new_tile_patterns_with_flips_render_exact':True,'GPU_parts':gpu,'other_entries_and_bank_bounds_exact':True,'other_texture_bytes_exact':90112,'other_parts_banks_byte_exact':True,'original_measured_Y_offsets':[-1,0,0,0,0,-1,-2,0],'BR_return19_20_dy_plus1_not_changed':True,'readback_sheets':sheets,'inputs':inputs,'producer_functions_called':False,'new_MIPS_executed':False,'runtime_verified':False,'full_art_completion':False,'limits':['52파트의 CPU 인덱스 합성·UV끝단과 반전 의미를 검사했으며 새 원MIPS나 실제 선택창을 실행하지 않았다.','새 타깃의 파트수63→52는 동일표시를 위한 배치 변경이며 고유원화 개수/품질완료율이 아니다.','기존 공개/활성 파일·원본·후보·입력은 수정하지 않았다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'changed_tiles':len(changed)}))
