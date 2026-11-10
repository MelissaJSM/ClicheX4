"""얼티밋 의상 순서 변경: 별도 UI/캡슐 자원의 조사와 재현 가능한 준비."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.prepare_shibuki_ui import actual
from scripts.prepare_shibuki_ultimate_save_ui import render
from scripts.verify_shibuki_save_icon import rgba
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_player import bank_offsets,composition_frame
from src.psx_disc import file_hash
from src.psx_ui_atlas import tile_pixels

TASK=ROOT/'work/ultimate_costume_swap_20261105/ui'
SOURCES={
 'ver_buki_riko':('out/ver_buki_riko/black_monochrome_riko_20261105_v1/shibuki_riko.bin','852813890c3c9f8e0394026f8c243f6c323f1a9c0f4e1941eaa920b85bdecc4e'),
 'ver_rin_nana':('out/ver_rin_nana/black_red_rin_20261105_v1/rin_nana.bin','aca6d7839ad1956ea837b07d1105a7609817cd30fd0e6ceffe13e6dd611ad6fe')}
SOURCE_RESOURCES={
 'ver_buki_riko':('50b517a51d2deccd92191717c61f2e79cad01d5e9ba39ca1a83812418a9b4057','55989a7a31845ececa284a3545e479e80dd142002399da8d0982f4999b9f4915','c8e527668823b35ef2ca81e36ae4058b0e54fa2be50e159b5af4134ddb866d85'),
 'ver_rin_nana':('277d49d98fbbae45cffb93ea173a8e72d4a75df84608923a611926d4949dd25b','3f99ceadc68130552cd38d2b4c706447f81bba82e7c635132f49e9d10c91f648','95f0734990ebe2bcec99b61f13ebe009d96ddcb74e745f4acd9954a0cadb7cbc')}

def sha(v):return hashlib.sha256(v).hexdigest()
def need(v,msg):
 if not v:raise ValueError(msg)
def read(project,names=('MOJIPAT.ARC','LOAD_U.ARC','PL00_U.ARC','PL02_U.ARC','SLUS_005.61')):
 path,digest=SOURCES[project];path=ROOT/path
 need(file_hash(path)==digest,'Unsupported baseline')
 with path.open('rb') as f:
  d=DiscReader(f,path.stat().st_size);records={r['name'].split(';')[0]:r for r in d.inspect()['files']}
  data={n:d.read(records[n]['lba'],records[n]['size']) for n in names}
 return data,{n:records[n] for n in names}
def sprite_canvas(frame):
 px,size,bb=frame[:3];a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);o=np.zeros((160,160),np.uint8)
 x,y=80+bb[0],80+bb[1];x0,y0=max(0,x),max(0,y);x1,y1=min(160,x+size[0]),min(160,y+size[1])
 if x0<x1 and y0<y1:o[y0:y1,x0:x1]=a[y0-y:y1-y,x0-x:x1-x]
 return o
def ui_canvas(menu,tex,n,row):
 cp=aliased_composition(menu,2,n);o=np.zeros((160,160),np.uint16);po=struct.unpack_from('<I',menu,4)[0]
 for p in cp['parts']:
  pal=np.array(struct.unpack_from('<16H',menu,po+(row+p['clut'])*32),np.uint16)
  a=sprite_canvas(compose_static(tex,local_composition({**cp,'parts':[p]})))
  o[a>0]=pal[a[a>0]]
 return o
def research(project):
 data,recs=read(project);out=TASK/'research'/project;out.mkdir(parents=True,exist_ok=True)
 menu=data['MOJIPAT.ARC'];tex=entry(data['LOAD_U.ARC'],0x10008);pl=data['PL02_U.ARC'];pal=entry(pl,9)
 images=[]
 for title,v in [('UI before',render(menu,tex,0)),('UI after',render(menu,tex,15)),('Game swimsuit',np.array(struct.unpack_from('<16H',pal),np.uint16)[sprite_canvas(actual(pl,0))]),('Game jacket overlay',np.array(struct.unpack_from('<16H',pal,32),np.uint16)[sprite_canvas(actual(pl,0,5))])]:images.append((title,rgba(v)))
 sheet=Image.new('RGB',(960,270),'#263642');dr=ImageDraw.Draw(sheet)
 for i,(title,im) in enumerate(images):
  im=im.crop((40,40,120,116)).resize((240,228),Image.Resampling.NEAREST);sheet.paste(im,(240*i,30),im);dr.text((i*240+3,4),title,fill='white')
 sheet.save(out/'current_save_gameplay.png')
 count=aliased_composition(menu,2,0)['bank_frame_count'];meta=[]
 sheet=Image.new('RGB',(10*140,((count+9)//10)*150),'#263642');dr=ImageDraw.Draw(sheet)
 for n in range(count):
  c=aliased_composition(menu,2,n);a=compose_static(tex,local_composition(c));meta.append({'frame':n,'parts':len(c['parts']),'bounds':a[2],'pixels_sha256':sha(a[0]),'record_offsets':[p['record_offset'] for p in c['parts']]})
  if a[1][0]<=160 and a[1][1]<=160:
   im=rgba(ui_canvas(menu,tex,n,30 if n==52 else 8)).crop((40,32,120,112));im.thumbnail((130,130),Image.Resampling.NEAREST);sheet.paste(im,(n%10*140,n//10*150+20),im)
  dr.text((n%10*140+4,n//10*150+4),str(n),fill='white')
 sheet.save(out/'all_save_frames.png')
 (out/'inventory.json').write_text(json.dumps({'project':project,'baseline':SOURCES[project][0],'baseline_sha256':SOURCES[project][1],'files':{n:{**recs[n],'sha256':sha(v)} for n,v in data.items()},'menu_offsets':list(struct.unpack_from('<'+'I'*(struct.unpack_from('<I',menu)[0]//4),menu)),'save_frames':meta},indent=2),encoding='utf8')
 print(json.dumps({'project':project,'frames':count,'menu_size':len(menu),'tex_size':len(tex),'directory':str(out)}))

def matching_tiles(target,texture):
 """기존 타일의 불투명 픽셀만 완전히 일치하는 등록 위치를 조사한다."""
 ys,xs=np.nonzero(target);x0,x1=int(xs.min())-15,int(xs.max())+1;y0,y1=int(ys.min())-15,int(ys.max())+1
 windows=np.lib.stride_tricks.sliding_window_view(target,(16,16))[y0:y1,x0:x1]
 candidates=[]
 for tile in range(len(texture)//128):
  px=np.frombuffer(tile_pixels(texture,tile),np.uint8).reshape(16,16)
  if np.count_nonzero(px)<4:continue
  for flag,im in [(0,px),(64,px[:,::-1]),(128,px[::-1]),(192,px[::-1,::-1])]:
   mask=im>0;valid=np.all(windows[:,:,mask]==im[mask],axis=-1)
   for y,x in np.argwhere(valid):candidates.append((int(np.count_nonzero(mask)),tile,int(x)+x0,int(y)+y0,flag,im.copy()))
 return sorted(candidates,key=lambda q:q[0],reverse=True)

def matching_research(project):
 d,_=read(project);target=sprite_canvas(actual(d['PL02_U.ARC'],0));tex=entry(d['LOAD_U.ARC'],0x10008);cand=matching_tiles(target,tex);remaining=target.copy();selected=[]
 for _,tile,x,y,flag,im in cand:
  mask=(im>0)&(remaining[y:y+16,x:x+16]>0);score=int(mask.sum())
  if score<4:continue
  selected.append({'tile':tile,'x':x-80,'y':y-80,'flag':flag,'coverage':score});remaining[y:y+16,x:x+16][im>0]=0
 from scripts.prepare_shibuki_ultimate_production import fast_fit
 print(project,'matched',selected,'remaining',int(np.count_nonzero(remaining)))
 for n in range(1,8):
  fit=fast_fit(remaining>0,n)
  if fit is not None:print('fitsnewtiles',n,fit);break

def prepare_capsules(arc,reference=None):
 """Core ARC 이후 실행. 4개 잔상 뱅크만 교체하며 기타 바이트를 보존한다."""
 from scripts.prepare_shibuki_capsule_nova import silhouette_frames,packed_bank,raster
 reference=arc if reference is None else reference
 need(sha(reference) in [v[2] for v in SOURCE_RESOURCES.values()],'Unknown capsule reference')
 g,c=entry(arc,2),entry(arc,3);rg,rc=entry(reference,2),entry(reference,3)
 need(replace_entry(replace_entry(arc,2,rg),3,rc)==reference,'Unrelated core ARC data changed')
 for current,original,ids in ((g,rg,range(10,14)),(c,rc,range(18,22))):
  starts=bank_offsets(original,allow_aliases=True);need(starts==bank_offsets(current,allow_aliases=True),'Core bank boundaries changed')
  for b in ids:
   end=starts[b+1] if b+1<len(starts) else len(original)
   need(current[starts[b]:end]==original[starts[b]:end],'Core unexpectedly changed capsule bank')
 ng,nc=g,c;body=sprite_canvas(actual(reference,0))>0;proof=[];images={}
 for gb in range(10,14):
  images[gb]=silhouette_frames(rg,rc,gb,gb+8,body)
  ng,nc,p=packed_bank(ng,nc,gb,gb+8,images[gb]);proof.append(p)
 for old,new,ids in ((g,ng,range(10,14)),(c,nc,range(18,22))):
  offsets=bank_offsets(old,allow_aliases=True);need(offsets==bank_offsets(new,allow_aliases=True),'Capsule boundary moved')
  allowed=set()
  for b in ids:allowed.update(range(offsets[b],offsets[b+1] if b+1<len(offsets) else len(old)))
  need(len(old)==len(new) and all(i in allowed for i,(a,b) in enumerate(zip(old,new)) if a!=b),'Capsule mutation escaped banks')
 for gb in images:
  for n,v in enumerate(images[gb]):need(np.array_equal(raster(ng,nc,gb,gb+8,n),v),'Capsule readback mismatch')
 changed=replace_entry(replace_entry(arc,2,ng),3,nc)
 need(replace_entry(replace_entry(changed,2,g),3,c)==arc,'Non capsule entries changed')
 return changed,{'capsule_refs':48,'banks':proof,'gameplay_banks_byte_identical':True,'animation_and_palette_entries_byte_identical':True,'other_entries_byte_identical':True,'after_swimsuit_silhouette':True,'runtime_verified':False},images

def capsule_command(project):
 d,recs=read(project);out=TASK/'capsules_v1'/project;need(not out.exists(),'Fresh capsule output required')
 new,proof,images=prepare_capsules(d['PL02_U.ARC']);out.mkdir(parents=True)
 (out/'PL02_U.ARC').write_bytes(new)
 board=Image.new('RGB',(12*100,4*120),'#263642');draw=ImageDraw.Draw(board);colors=np.array([0,0xffff,0xfdc8,0xe920]+[0x8000]*12,np.uint16)
 for row,gb in enumerate(images):
  for n,v in enumerate(images[gb]):
   im=rgba(colors[v]).crop((36,28,136,132));board.paste(im,(n*100,row*120+16),im);draw.text((n*100,row*120),f'{gb}/{n}',fill='white')
 board.resize((1800,720),Image.Resampling.NEAREST).save(out/'capsules.png')
 proposal={'project':project,'baseline':SOURCES[project][0],'baseline_sha256':SOURCES[project][1],'files':{'PL02_U.ARC':{'before':sha(d['PL02_U.ARC']),'after':sha(new),'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'size':len(new),'record':recs['PL02_U.ARC']}},'verification':proof,'integration':'Call prepare_capsules(core_arc, baseline_arc), not a whole entry merge'}
 (out/'proposal.json').write_text(json.dumps(proposal,indent=2),encoding='utf8');print(json.dumps({'project':project,'path':str(out),'verification':proof}),flush=True)

def save_sources(files):
 """동일 256타일 아틀라스에서 보존된 공통 UI를 재등록해53을 확보한다."""
 from scripts.prepare_cliche_logo_v4 import old_records,pack_bank
 from scripts.prepare_shibuki_ultimate_production import fast_fit
 from src.psx_ui_atlas import write_tile
 menu=files['MOJIPAT.ARC'];texture=entry(files['LOAD_U.ARC'],0x10008);exe=files['SLUS_005.61']
 need(tuple(sha(files[n]) for n in ('MOJIPAT.ARC','LOAD_U.ARC','PL02_U.ARC')) in SOURCE_RESOURCES.values(),'Unsupported save resource combination')
 records=old_records(menu,2);need(len(records)==53,'Expected original 53 save frames')
 comps={n:aliased_composition(menu,2,n) for n in range(53)}
 originals={n:sprite_canvas(compose_static(texture,local_composition(c))) for n,c in comps.items()}
 # The old full-jacket overlay has tiny deliberate eye holes, revealed by
 # the player base beneath it. A standalone save object must include those
 # exact existing base pixels instead of leaving holes after suppressing44.
 pal=entry(files['PL02_U.ARC'],9);basepal=np.array(struct.unpack_from('<16H',pal),np.uint16);armorpal=np.array(struct.unpack_from('<16H',pal,32),np.uint16)
 jacket_world=basepal[sprite_canvas(actual(files['PL02_U.ARC'],0))]
 for b in (8,5,7,6):
  a=sprite_canvas(actual(files['PL02_U.ARC'],0,b));jacket_world[a>0]=armorpal[a[a>0]]
 jacket=originals[52].copy();need(np.array_equal(armorpal[jacket][jacket>0],jacket_world[jacket>0]),'Existing jacket differs from live body')
 holes=(jacket==0)&(jacket_world!=0)
 for y,x in np.argwhere(holes):
  ids=np.flatnonzero(armorpal==jacket_world[y,x]);need(len(ids)>0,'Jacket base eye needs a new palette');jacket[y,x]=ids[0]
 # Native direct loading rectangles and the 48px repeated menu background
 # consume texels absent from the composed-frame list, including blank cells.
 # Actual native background 0x80016124 uses u0..111 and u112..207,
 # height48, v208. The rightmost 48px contains player icon tiles.
 direct={y*16+x for y in range(13,16) for x in range(13)};table=0xDED04
 for row in range(9):
  x,y,t,w,h,clut=struct.unpack_from('<hhBBBB',exe,table+row*8)
  starts=list(exe[table+72:table+84]) if row==6 else [t]
  direct.update(start+dy*16+dx for start in starts for dy in range(h) for dx in range(w))
 target_ids={44,45,46,47,48,52}
 # Exact duplicate glyph/blank cells outside every direct-draw rectangle
 # can share one tile. Each composed record is redirected; its raster and
 # palette remain identical. This is needed only in the first mode atlas.
 aliases={}
 for source,target in {152:149,153:150,154:151,160:16,166:16,176:16,182:16}.items():
  if source not in direct and tile_pixels(texture,source)==tile_pixels(texture,target):aliases[source]=target
 for n in range(len(records)):
  records[n]=[q[:1]+bytes([aliases.get(q[1],q[1])])+q[2:] if q[0]&3==0 else q for q in records[n]]
 other_tiles={p['page']*256+p['tile'] for n,c in comps.items() if n not in target_ids for p in c['parts']}
 owned={p['page']*256+p['tile'] for n in target_ids for p in comps[n]['parts']}-other_tiles-direct
 spare={y*16+x for y in range(13,16) for x in range(13,16)}-(other_tiles|direct|owned)
 need(not (spare&(other_tiles|direct|owned)),'Right-side spare cells became referenced')
 available=owned|spare|set(aliases);reserved=set(range(256))-available;out=bytearray(texture)
 cache={tile_pixels(texture,t):t for t in sorted(reserved)};free=sorted(available);alloc=[]
 def allocate(px):
  if px in cache:return cache[px]
  t=next((v for v in free if (v%16 or not any(px[::16])) and (v>=16 or not any(px[:16]))),None)
  need(t is not None,f'Exact save atlas exhausted: allocated {len(alloc)}, free {free}')
  free.remove(t);write_tile(out,t,px);cache[px]=t;alloc.append(t);return t
 def fit_array(arr,limit):
  best=None
  # Exact grid fits avoid solver variance; use the bounded existing native
  # cover solver only when a smaller number of tiles is needed.
  for count in range(max(1,limit-3),limit+1):
   fit=fast_fit(arr>0,count)
   if fit is not None:best=fit;break
  need(best is not None,'Exact save cover exceeds original part count');return best
 def new_records(arr,rects,clut=0):
  rest=arr.copy();rr=[]
  for x,y in rects:
   v=rest[y:y+16,x:x+16].copy();rest[y:y+16,x:x+16]=0
   if not v.any():continue
   yy,xx=np.nonzero(v);l,u=int(xx.min()),int(yy.min());r,b=int(xx.max())+1,int(yy.max())+1
   tight=np.zeros((16,16),np.uint8);tight[:b-u,:r-l]=v[u:b,l:r]
   t=allocate(tight.tobytes());rr.append(struct.pack('<BBbb',clut<<2,t,x+l-80,y+u-80))
  need(not rest.any(),'Save cover omitted pixels');return rr
 layouts={}
 for n in sorted(target_ids):
  cs={q['clut'] for q in comps[n]['parts']};need(len(cs)==1,'Mixed palette frame cannot be merged')
  arr=jacket if n==52 else originals[n]
  fit=fit_array(arr,len(comps[n]['parts']));records[n]=new_records(arr,fit,next(iter(cs)));layouts[n]=fit
 swim=sprite_canvas(actual(files['PL02_U.ARC'],0));remaining=swim.copy();extra=[]
 for _,t,x,y,flag,v in matching_tiles(swim,bytes(out)):
  # Only an allocated/protected tile remains stable through this build.
  if t in free:continue
  score=int(np.count_nonzero((v>0)&(remaining[y:y+16,x:x+16]>0)))
  if score<12:continue
  extra.append(struct.pack('<BBbb',flag,t,x-80,y-80));remaining[y:y+16,x:x+16][v>0]=0
 fit=fit_array(remaining,8);records.append(extra+new_records(remaining,fit))
 offsets=struct.unpack_from('<4I',menu);bank,proof=pack_bank(records,offsets[3]-offsets[2]);nm=menu[:offsets[2]]+bank+menu[offsets[3]:]
 nt=bytes(out)
 for n in range(53):
  c=aliased_composition(nm,2,n);got=sprite_canvas(compose_static(nt,local_composition(c)))
  need(np.array_equal(got,jacket if n==52 else originals[n]),f'Existing save frame {n} pixels/origin changed')
  if n not in target_ids:
   need([nm[q['record_offset']:q['record_offset']+4] for q in c['parts']]==records[n],f'Untargeted frame {n} data changed')
 need(np.array_equal(sprite_canvas(compose_static(nt,local_composition(aliased_composition(nm,2,53)))),swim),'New swimsuit differs')
 need(np.array_equal(ui_canvas(nm,nt,52,30),jacket_world),'New complete jacket differs from gameplay')
 need(np.array_equal(ui_canvas(nm,nt,53,31),basepal[swim]),'New swimsuit colors differ from gameplay')
 need(all(tile_pixels(nt,t)==tile_pixels(texture,t) for t in reserved),'Protected/direct atlas cell changed')
 need(nm[:offsets[2]]==menu[:offsets[2]] and nm[offsets[3]:]==menu[offsets[3]:],'Other menu bank changed')
 # Every old normal/Fourth bit combination remains visually identical.
 from scripts.verify_shibuki_save_icon import icon
 for arm in (1,2):
  for mask in range(16):need(np.array_equal(icon(menu,texture,mask,arm),icon(nm,nt,mask,arm)),'Normal/Fourth save UI changed')
 return {'MOJIPAT.ARC':nm,'LOAD_U.ARC':replace_entry(files['LOAD_U.ARC'],0x10008,nt)}, {'save_frames_preserved':52,'normal_fourth_combinations_preserved':32,'new_swimsuit_frame':53,'new_frame_parts':len(records[53]),'repacked_same_pixels':sorted(target_ids-{52}),'retained_existing_jacket_frame':52,'jacket_original_opaque_pixels_preserved':True,'jacket_missing_base_pixels_composited':int(holes.sum()),'both_outfits_match_gameplay_idle_rgb555_exact':True,'available_owned_tiles':sorted(owned),'verified_unreferenced_right_spare_tiles':sorted(spare),'exact_duplicate_aliases':aliases,'allocated_tiles':alloc,'direct_uv_tiles_preserved':sorted(direct),'palette_bytes_preserved':True,'other_banks_preserved':True,'bank':proof,'layouts':layouts,'runtime_verified':False}

def save_command(project):
 data,recs=read(project);out=TASK/'save_v1'/project;need(not out.exists(),'Fresh save output required')
 changed,proof=save_sources(data);out.mkdir(parents=True)
 for n,v in changed.items():(out/n).write_bytes(v)
 m=changed['MOJIPAT.ARC'];t=entry(changed['LOAD_U.ARC'],0x10008)
 board=Image.new('RGB',(800,320),'#263642');dr=ImageDraw.Draw(board)
 for i,(n,row,title) in enumerate([(52,30,'Before capsule: jacket'),(53,31,'After capsule: swimsuit')]):
  im=rgba(ui_canvas(m,t,n,row)).crop((40,32,120,112)).resize((320,320),Image.Resampling.NEAREST);board.paste(im,(i*400+30,10),im);dr.text((i*400+10,5),title,fill='white')
 board.save(out/'save_preview.png')
 (out/'proposal.json').write_text(json.dumps({'project':project,'baseline':SOURCES[project][0],'baseline_sha256':SOURCES[project][1],'files':{n:{'before':sha(data[n]),'after':sha(v),'path':(out/n).relative_to(ROOT).as_posix(),'size':len(v),'record':recs[n]} for n,v in changed.items()},'verification':proof},indent=2),encoding='utf8')
 print(json.dumps({'project':project,'verification':proof}),flush=True)

SAVE_BEGIN,SAVE_END=0x8001BD1C,0x8001BD9C
SAVE_SOURCE_HASH='a303f37846647141e78ea45da0597d77793b9ff0900b30bcdab68176e5c5b958'
def exeoff(address):return address-0x80010000+2048
def save_code():
 from src.psx_korean_font import Assembly
 a=Assembly();i,b=a.imm,a.branch
 i(40,'v0','a0',2)
 i(15,'t0','zero',0x8017);i(35,'t0','t0',0x21BC);a.nop()
 i(36,'t1','t0',0);i(36,'t2','t0',0x29);i(9,'v1','zero',44)
 b(4,'t1','zero','x_path');i(9,'v0','zero',0x7808)
 b(4,'t2','zero','common');i(9,'v1','zero',43)
 a.jump(2,SAVE_BEGIN+22*4);i(9,'v0','zero',0x784B)
 a.label('x_path');b(4,'t2','zero','common');a.nop()
 i(36,'t1','t0',3);a.nop();i(12,'t1','t1',15);a.reg(0x2B,'t1','zero','t1')
 i(9,'v1','t1',52);i(9,'v0','t1',0x784E)
 a.label('common');i(40,'v1','a0',0x47);i(41,'v0','a0',0x42)
 i(41,'s2','a0',0xA);a.jump(2,0x8001BDC0);a.emit(0xA493000E)
 # Patch the zero-special jump using the actual common label, avoiding
 # assumptions about instruction count during later maintenance.
 a.words[11]=(2<<26)|((SAVE_BEGIN+a.labels['common']*4)>>2&0x3ffffff)
 code=a.finish();need(len(code)<=SAVE_END-SAVE_BEGIN,'Save display function budget exceeded')
 return code+bytes(SAVE_END-SAVE_BEGIN-len(code))

def patch_save_executable(exe):
 need(exe[:8]==b'PS-X EXE' and len(exe)==1179648,'Unexpected executable format')
 a,b=exeoff(SAVE_BEGIN),exeoff(SAVE_END)
 need(sha(exe[a:b])==SAVE_SOURCE_HASH,'Save constructor source changed')
 p=exeoff(0x8001BE60);need(exe[p:p+4]==bytes.fromhex('3c004014'),'Save overlay branch changed')
 out=bytearray(exe);out[a:b]=save_code()
 # bnez v0, function epilogue: Ultimate now has one complete selected object.
 struct.pack_into('<I',out,p,(5<<26)|(2<<21)|((0x8001BFD8-0x8001BE64)//4))
 allowed=set(range(a,b))|set(range(p,p+4))
 need(all(i in allowed for i,(x,y) in enumerate(zip(exe,out)) if x!=y),'Save EXE edit escaped two existing spans')
 return bytes(out)

def save_cpu_command(project):
 import unicorn as uc
 from unicorn import mips_const as m
 data,_=read(project);old=data['SLUS_005.61'];new=patch_save_executable(old);out=TASK/'save_code'/project;out.mkdir(parents=True,exist_ok=True)
 machine=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN);machine.mem_map(0,0x200000);machine.mem_write(0x10000,old[2048:])
 STOP=0x80008000;ALLOC=0x8002AE50;OBJ=0x1FA000;SAVE=0x1FB000;STACK=0x1FF000;allocations=[];writes=[];fail=False
 def on_code(u,address,size,_):
  if address==ALLOC:
   addr=0 if fail else 0x80000000|OBJ+len(allocations)*256
   allocations.append(addr);u.reg_write(m.UC_MIPS_REG_V0,addr);u.reg_write(m.UC_MIPS_REG_PC,u.reg_read(m.UC_MIPS_REG_RA))
 def on_write(u,access,address,size,value,_):
  p=address&0x1fffffff;need((OBJ<=p<OBJ+1024) or STACK-64<=p<STACK,'Display routine wrote non-object/state memory');writes.append((p,size))
 machine.hook_add(uc.UC_HOOK_CODE,on_code);machine.hook_add(uc.UC_HOOK_MEM_WRITE,on_write)
 def run(exe,character,special,mask,mode,entrypoint,allocation_failed=False):
  nonlocal fail;fail=allocation_failed;allocations.clear();writes.clear()
  machine.mem_write(0x1BCAC,exe[exeoff(0x8001BCAC):exeoff(0x8001C008)]);machine.ctl_remove_cache(0x8001BCAC,0x8001C008)
  sb=bytearray(256);sb[0]=character;sb[0x29]=special;sb[3]=mask;sb[2]=2
  machine.mem_write(SAVE,bytes(sb));machine.mem_write(0x1721BC,struct.pack('<I',0x80000000|SAVE));machine.mem_write(0x141BDF,b'\x12');machine.mem_write(0x1721C1,b'\x34');machine.mem_write(OBJ,bytes(1024))
  for name,v in [('A0',77),('A1',123),('A2',mode),('SP',0x80000000|STACK),('RA',STOP)]+[(f'S{i}',0x12345600+i) for i in range(8)]:machine.reg_write(getattr(m,'UC_MIPS_REG_'+name),v)
  machine.emu_start(entrypoint,STOP,count=3000)
  need(machine.reg_read(m.UC_MIPS_REG_PC)==STOP,'Save constructor did not return')
  need(machine.mem_read(SAVE,256)==sb,'Saved gameplay fields changed')
  need(machine.reg_read(m.UC_MIPS_REG_SP)==0x80000000|STACK,'Stack pointer changed')
  for i in range(8):need(machine.reg_read(getattr(m,'UC_MIPS_REG_S'+str(i)))==0x12345600+i,'Callee saved register changed')
  return bytes(machine.mem_read(OBJ,1024)),list(allocations)
 checks=0
 for character in (0,1,255):
  for special in (0,1,255):
   for mask in range(16):
    for mode in (0,1):
     for failed in (False,True):
      for func in (0x8001BCAC,0x8001BE10):
       a,aa=run(old,character,special,mask,mode,func,failed);z,za=run(new,character,special,mask,mode,func,failed)
       if character==0 and special:
        if func==0x8001BCAC:
         expected=bytearray(a)
         if not failed:expected[0x47]=52+bool(mask);struct.pack_into('<H',expected,0x42,0x784E+bool(mask))
         need(z==expected and aa==za,'Ultimate selected save frame wrong')
        else:need(z==bytes(1024) and not za,'Ultimate duplicate overlay not suppressed')
       else:need((a,aa)==(z,za),'Normal/Fourth/Rin/empty native constructor changed')
       checks+=1
 rejected=[]
 for label,where in [('constructor',exeoff(SAVE_BEGIN)),('overlay',exeoff(0x8001BE60))]:
  bad=bytearray(old);bad[where]^=1
  try:patch_save_executable(bytes(bad))
  except ValueError:rejected.append(label)
  else:raise ValueError('Corrupt save input accepted')
 proof={'passed':True,'cpu_cases':checks,'original_function_sha256':sha(old[exeoff(0x8001BCAC):exeoff(0x8001C008)]),'source_range':[hex(SAVE_BEGIN),hex(SAVE_END)],'same_function_allocation':True,'cave_bytes':0,'overlay_branch':hex(0x8001BE60),'states':['normal X','all Fourth masks','normal Zero','Black Zero','Ultimate pre','Ultimate post','empty slot','allocation failure'],'gameplay_saved_fields_byte_identical':True,'stack_and_callee_saved_registers':True,'rejected_inputs':rejected,'runtime_verified':False}
 (out/'SLUS_005.61').write_bytes(new);(out/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf8');print(json.dumps(proof),flush=True)

def prepare_command(project):
 data,recs=read(project);out=TASK/'prepared_v1'/project;need(not out.exists(),'Fresh final UI output required')
 changed,proof=save_sources(data);again,_=save_sources(data);need(changed==again,'Save repack is not reproducible')
 changed['SLUS_005.61']=patch_save_executable(data['SLUS_005.61'])
 cpu=TASK/'save_code'/project/'verification.json';need(cpu.exists() and json.loads(cpu.read_text('utf8'))['passed'],'CPU proof missing')
 reject=[]
 for name in ('MOJIPAT.ARC','LOAD_U.ARC','PL02_U.ARC'):
  bad=dict(data);v=bytearray(bad[name]);v[-1]^=1;bad[name]=bytes(v)
  try:save_sources(bad)
  except ValueError:reject.append(name)
  else:raise ValueError('Bad source resource accepted')
 out.mkdir(parents=True)
 for n,v in changed.items():(out/n).write_bytes(v)
 m,t=changed['MOJIPAT.ARC'],entry(changed['LOAD_U.ARC'],0x10008)
 board=Image.new('RGB',(800,340),'#263642');dr=ImageDraw.Draw(board)
 for i,(n,row,title) in enumerate([(52,30,'Before capsule: jacket'),(53,31,'After capsule: swimsuit')]):
  im=rgba(ui_canvas(m,t,n,row)).crop((40,32,120,112)).resize((320,320),Image.Resampling.NEAREST);board.paste(im,(i*400+30,20),im);dr.text((i*400+10,5),title,fill='white')
 board.save(out/'save_preview.png')
 proof.update({'reproduced_resource_hashes':True,'rejected_sources':reject,'cpu_report':cpu.relative_to(ROOT).as_posix(),'capsule_integration':'prepare_capsules(core_arc, baseline_arc)','needs_display_code':True,'runtime_verified':False})
 recipe={'project':project,'baseline':SOURCES[project][0],'baseline_sha256':SOURCES[project][1],'files':{n:{'before':sha(data[n]),'after':sha(v),'path':(out/n).relative_to(ROOT).as_posix(),'size':len(v),'record':recs[n]} for n,v in changed.items()},'verification':proof,'capsule_proposal':(TASK/'capsules_v1'/project/'proposal.json').relative_to(ROOT).as_posix()}
 (out/'proposal.json').write_text(json.dumps(recipe,indent=2),encoding='utf8');print(json.dumps({'project':project,'output':str(out),'files':{n:sha(v) for n,v in changed.items()},'passed':True}),flush=True)

def combine_command(project):
 d,recs=read(project);baseline=d['PL02_U.ARC'];core_dir=ROOT/'work/ultimate_costume_swap_20261105/core/prepared_complete_v1'/project
 core=(core_dir/'PL02_U.ARC').read_bytes();core_expected={'ver_buki_riko':'2f0fc0f0fe7cbee5cb6586b17b3ae88eee973f0fbc1f8933168dc3a76cd5a068','ver_rin_nana':'a8269047ab937d5bbd6b5e97e7cdeb0241b9e60b1612eb2bb93d692d79fef7d2'}[project]
 need(sha(core)==core_expected,'Core final source changed');out=TASK/'combined_capsules_v1'/project;need(not out.exists(),'Fresh combined output required')
 result,proof,_=prepare_capsules(core,baseline);again,_,_=prepare_capsules(core,baseline);need(result==again,'Combined capsule reproduction differs')
 expected=(TASK/'capsules_v1'/project/'PL02_U.ARC').read_bytes();changed_core={i for i,(a,b) in enumerate(zip(baseline,core)) if a!=b};changed_caps={i for i,(a,b) in enumerate(zip(core,result)) if a!=b}
 need(not changed_core&changed_caps,'Core and capsule bytes overlap')
 need(all(result[i]==core[i] for i in changed_core),'Core correction lost')
 for kind,ids in ((2,range(10,14)),(3,range(18,22))):
  a,b=entry(result,kind),entry(expected,kind);starts=bank_offsets(a,allow_aliases=True)
  for bi in ids:
   end=starts[bi+1] if bi+1<len(starts) else len(a);need(a[starts[bi]:end]==b[starts[bi]:end],'Final capsule bank differs from proof')
 rejected=[]
 for label,wrong,ref in [('already_capsule_patched',result,baseline),('unsupported_reference',core,baseline[:-1]),('changed_other_entry',core[:-1]+bytes([core[-1]^1]),baseline)]:
  try:prepare_capsules(wrong,ref)
  except ValueError:rejected.append(label)
  else:raise ValueError('Wrong capsule input accepted')
 proof.update({'core_source':(core_dir/'PL02_U.ARC').relative_to(ROOT).as_posix(),'core_sha256':sha(core),'core_changed_bytes_preserved':len(changed_core),'capsule_changed_bytes':len(changed_caps),'overlapping_changed_bytes':0,'capsule_banks_match_frozen_review':True,'reproducible':True,'rejected_inputs':rejected})
 out.mkdir(parents=True);(out/'PL02_U.ARC').write_bytes(result)
 p={'project':project,'baseline':SOURCES[project][0],'baseline_sha256':SOURCES[project][1],'files':{'PL02_U.ARC':{'before':sha(baseline),'after':sha(result),'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'size':len(result),'record':recs['PL02_U.ARC']}},'verification':proof,'integration':'Contains core final plus capsule overlay. Do not merge either source proposal a second time.'}
 (out/'proposal.json').write_text(json.dumps(p,indent=2),encoding='utf8');print(json.dumps({'project':project,'sha256':sha(result),'verification':proof}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['research','matching','capsules','save','save-cpu','prepare','combine']);p.add_argument('--project',choices=SOURCES)
 a=p.parse_args()
 for project in ([a.project] if a.project else SOURCES):({'research':research,'matching':matching_research,'capsules':capsule_command,'save':save_command,'save-cpu':save_cpu_command,'prepare':prepare_command,'combine':combine_command}[a.command])(project)
