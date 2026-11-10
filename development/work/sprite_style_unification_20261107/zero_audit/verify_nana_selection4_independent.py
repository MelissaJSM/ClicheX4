"""RN 선택 사본4: 직접 정적 텍셀/반전/원점 및 비대상 읽기 검사."""
from pathlib import Path
import json,hashlib,struct,sys,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_ui_atlas import aliased_composition
O=D/'nana_selection4_independent01';S=W/'nana_selection_sync34_03'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={}
def blob(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def js(p):return json.loads(blob(p))
plan=js(W/'staging_rn_v34.json');producer=js(S/'report.json')
source=ROOT/plan['source_bin']
file_sha=hashlib.sha256()
with source.open('rb')as f:
 for chunk in iter(lambda:f.read(1048576),b''):file_sha.update(chunk)
assert file_sha.hexdigest()==plan['source_sha256']
assets,_=read_disc(source,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))
oldgame=assets['PL00_U.ARC'];newgame=blob(ROOT/plan['resources']['PL00_U.ARC']['path']);a,b=Archive(oldgame),Archive(newgame)
assert sha(oldgame)==producer['parent_game']=='18be60ea9e6745abf2309611cc9617e76acda4ebd984f7abf2995c457ec06908'
assert sha(newgame)==producer['new_game']=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9'
old=blob(ROOT/plan['resources']['ST0E_U1.ARC']['path']);new=blob(S/'ST0E_U1.ARC')
assert sha(old)=='3c1234593444c0be72413f2e6e81b0c049509eedcbb40bf4e4d6413613b16e11'
assert sha(new)=='a577566919c4dad695950347151ce3a57af8c3247172b04c1f36c5ec6f7101b5'
assert len(old)==len(new);oe,ne=psx_arc(old),psx_arc(new)
assert [(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne]
for q in oe:
 t=int(q['type'],16)
 if t not in(10,0x10102):assert entry(old,t)==entry(new,t)
og,ng=entry(old,0x10102),entry(new,0x10102);op,np_=entry(old,10),entry(new,10)
assert len(og)==len(ng)and len(op)==len(np_)and og[:90112]==ng[:90112]
offsets=struct.unpack('<3I',entry(old,12));assert offsets==(0,40960,90112)
count=struct.unpack_from('<I',op)[0]//4;obanks=struct.unpack_from('<'+'I'*count,op);nbanks=struct.unpack_from('<'+'I'*count,np_)
assert obanks==nbanks and count==3
for bank in(0,1):
 lo=obanks[bank];hi=min((x for x in obanks if x>lo),default=len(op));assert op[lo:hi]==np_[lo:hi]
assert op[:obanks[0]]==np_[:nbanks[0]]
pal=entry(assets['COL0E_U1.ARC'],5)
assert pal[512:544]==a.p[:32]==b.p[:32]
def tile(texture,t):
 z=np.zeros((16,16),np.uint8)
 for y in range(16):
  for x in range(16):
   off=(t//16*16+y)*128+(t%16)*8+x//2
   assert 0<=off<len(texture);z[y,x]=(texture[off]>>(4*(x%2)))&15
 return z
def rgba(z,words):
 colors=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]+[255]for v in words],np.uint8);colors[0]=0
 return colors[z]
def static(g,p,bank,n):
 lo=offsets[bank];hi=offsets[bank+1]if bank+1<3 else len(g);tex=g[lo:hi];c=aliased_composition(p,bank,n)
 idx=np.zeros((384,384),np.uint8);out=np.zeros((384,384,4),np.uint8)
 for q in c['parts']:
  assert not q['unknown_flags'];z=tile(tex,q['page']*256+q['tile'])
  if q['flip_x']:z=z[:,::-1]
  if q['flip_y']:z=z[::-1]
  x,y=q['x']+160,q['y']+160;assert 0<=x<=368 and 0<=y<=368;nz=z>0
  idx[y:y+16,x:x+16][nz]=z[nz]+q['clut']*16
  if bank in(0,2):
   row=(16 if bank==2 else 0)+q['clut'];words=struct.unpack_from('<16H',pal,row*32);pix=rgba(z,words);out[y:y+16,x:x+16][nz]=pix[nz]
 return idx,out,c
def orient(z,n,extra_y=0):
 out=np.zeros_like(z);mask=z[:,:,3]>0 if z.ndim==3 else z>0;y,x=np.nonzero(mask)
 tx=319-x if n in(19,20)else x;ty=y+(-1 if n==18 else 0)+extra_y
 assert not len(x)or(tx.min()>=0 and tx.max()<384 and ty.min()>=0 and ty.max()<384)
 out[ty,tx]=z[y,x];return out
mapping={18:207,19:156,20:157,21:158};counts=collections.Counter();reserved=set();cases=[];images={};oldgeos={};newgeos={}
for bank in range(3):
 total=aliased_composition(op,bank,0)['bank_frame_count'];assert total==aliased_composition(np_,bank,0)['bank_frame_count']
 for n in range(total):
  oi,oc,ops=static(og,op,bank,n);ni,nc,nps=static(ng,np_,bank,n);counts['all_UI_frames']+=1
  if bank==2 and n in mapping:
   ref=mapping[n];oldidx=a.layer(ref)[0];newidx=b.layer(ref)[0]
   assert np.array_equal(oi,orient(oldidx,n))and np.array_equal(ni,orient(newidx,n))
   assert np.array_equal(oc,orient(np.array(a.composite(ref,0)[0]),n))and np.array_equal(nc,orient(np.array(b.composite(ref,0)[0]),n))
   if n in(19,20):
    matches=[dy for dy in range(-3,4)if np.array_equal(oc,orient(np.array(a.composite(ref,0)[0]),n,dy))]
    assert matches==[0]
   else:matches=None
   part_transforms=[]
   # Match target display records to gameplay geometry in order; UV/tiles may be repacked.
   from src.psx_player import composition_frame
   gp=composition_frame(b.c,0,ref)['parts'];assert len(gp)==len(nps['parts'])
   for q,w in zip(gp,nps['parts']):
    expectedx=-q['x']-16 if n in(19,20)else q['x'];expectedy=q['y']-1 if n==18 else q['y']
    assert(w['x'],w['y'],w['flip_x'],w['flip_y'])==(expectedx,expectedy,not q['flip_x']if n in(19,20)else q['flip_x'],q['flip_y'])
    assert q['clut']==w['clut']==0
    t=w['page']*256+w['tile'];z=tile(ng[90112:],t)
    assert not(t%16==0 and z[:,0].any())and not(t%256<16 and z[0].any())
    counts['target_GPU_parts']+=1
    part_transforms.append({'game_xy':[q['x'],q['y']],'UI_xy':[w['x'],w['y']],'game_flip_x':q['flip_x'],'UI_flip_x':w['flip_x'],'tile':t})
   cases.append({'UI':n,'game':ref,'old_measured_transform_exact':True,'new_index_and_RGBA_exact':True,'mirror_y_candidates':matches,'parts':part_transforms})
   images[n]=(oc,nc,orient(np.array(b.composite(ref,0)[0]),n),np.array(b.composite(ref,0)[0]));counts['target_copies']+=1
  else:
   assert np.array_equal(oi,ni)and np.array_equal(oc,nc)
   assert len(ops['parts'])==len(nps['parts'])
   for q,w in zip(ops['parts'],nps['parts']):
    assert op[q['record_offset']:q['record_offset']+4]==np_[w['record_offset']:w['record_offset']+4];counts['non_target_record_sequences']+=1
    if bank==2:reserved.add(q['page']*256+q['tile'])
   counts['non_target_UI_frames']+=1
for t in reserved:assert np.array_equal(tile(og[90112:],t),tile(ng[90112:],t))
assert len(reserved)==134 and counts['target_copies']==4
O.mkdir(exist_ok=False);sheets=[]
for n,ims in images.items():
 union=np.zeros((384,384),bool)
 for z in ims:union|=z[:,:,3]>0
 ys,xs=np.where(union);box=(int(xs.min())-2,int(ys.min())-2,int(xs.max())+3,int(ys.max())+3);w,h=box[2]-box[0],box[3]-box[1]
 cw,ch=w*4+12,h*4+28;board=Image.new('RGB',(cw*4,ch),'#263345');draw=ImageDraw.Draw(board)
 for col,(caption,z)in enumerate(zip(('old UI','new UI','game transformed','game original'),ims)):
  x=col*cw;draw.text((x+4,4),f'{n} {caption}',fill='white');im=Image.fromarray(z).crop(box).resize((w*4,h*4),Image.Resampling.NEAREST);board.paste(im,(x+4,24),im)
 p=O/f'copy_{n}.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
for p,h in inputs.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'RN 선택 사본4의 기존 원점과 실제 신규 몸체, 모든 UI 비대상/소비타일/파트 반전 의미 독립 읽기','candidate':rel(S/'ST0E_U1.ARC'),'candidate_sha256':sha(new),'parent_sha256':sha(old),'source_BIN_sha256':plan['source_sha256'],'old_game_sha256':sha(oldgame),'new_game_sha256':sha(newgame),'counts':dict(counts),'mapping_cases':cases,'protected_whole_tiles_exact':len(reserved),'other_entries_and_directory_sizes_exact':True,'other_composition_banks_exact':True,'portrait_background_bytes_exact':90112,'original_measured_RN_mirror_y':0,'BR_mapping_applied':False,'original_palette_exact':True,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':inputs,'producer_functions_called':False,'new_MIPS_executed':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['정적 UI 텍셀·색·원점·파트반전·UV경계 검사이며 실제 선택창 게임 화면을 실행한 검사는 아니다.','원래 RN19/20은 거울반전 뒤 Y불변이다. BR의 Y+1 정책과 구분해 부모 실제픽셀에서 확인했다.','이 사본4 외 다른 Nana 선택 모션의 최신 원화 동기화 완료를 주장하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'protected_tiles':len(reserved)}))
