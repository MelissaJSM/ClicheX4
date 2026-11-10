"""최신 BIN의 X/아머 픽셀을 원점 보존하여 읽기 전용으로 수집한다."""
import argparse, hashlib, json, math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame,compose_indices
from src.psx_ui_atlas import local_composition

TASK=ROOT/'work/sprite_consistency_20261105/x'
OUT=ROOT/'out/sprite_consistency_20261105'
SOURCES={
 'shibuki':('ver_buki_riko','shibuki_riko','bedba81a4c1263388835e10f57a8e30f6b7e9d9ac6f3f3d3dbf77821f4fb7c08'),
 'nana':('ver_rin_nana','rin_nana','b15be8bf18921f06c8e6713c0bdc51a22374764c7d59ec7fca29df97f2e742c1')}
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13)
DRAW_ORDER=((8,8),(1,5),(4,7),(2,6))
GROUPS={
 'idle':[0,115,116,117,118,119],
 'run':list(range(1,33)),
 'air':list(range(33,55))+[93,94],
 'wall':list(range(55,67)),
 'dash':list(range(67,85)),
 'shoot_special':list(range(85,93))+list(range(95,105))+list(range(208,213))+[231,232],
 'hurt_lowhp':list(range(106,115))+list(range(120,126))+list(range(233,237)),
 'arrival':list(range(126,143)),
 'ladder':list(range(143,156))+[183],
 'victory_teleport':list(range(156,162)),
 'ride_chaser':list(range(162,175)),
 'ride_armor':list(range(184,204)),
 'other_action':list(range(204,208)),
 'nova_hover':list(range(213,231)),
 'reserved_or_empty':[105]+list(range(175,183))}
GROUP_NAMES={'idle':'대기','run':'이동·이동사격','air':'공중','wall':'벽타기·벽사격','dash':'대시','shoot_special':'사격·특수기술','hurt_lowhp':'피격·체력부족','arrival':'등장·캡슐 전환','ladder':'사다리','victory_teleport':'승리·전송','ride_chaser':'라이드 체이서','ride_armor':'라이드 아머 머리','other_action':'기타 동작','nova_hover':'노바·호버','reserved_or_empty':'빈/예약 참조'}

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
def relative(path):return path.relative_to(ROOT).as_posix()
def need(ok,why):
 if not ok:raise ValueError(why)
def read(character):
 project,stem,expected=SOURCES[character]
 path=ROOT/f'out/{project}/ultimate_costumes_swapped_20261105_v1/{stem}.bin'
 need(digest(path)==expected,'지원하지 않는 BIN 해시')
 with path.open('rb') as f:
  disc=DiscReader(f,path.stat().st_size);records={q['name'].split(';')[0]:q for q in disc.inspect()['files']}
  assets={name:disc.read(records[name]['lba'],records[name]['size']) for name in ('PL00_U.ARC','PL02_U.ARC','SLUS_005.61')}
 return path,assets,{n:records[n] for n in assets}

class Archive:
 def __init__(self,data):
  self.data=data;self.g=entry(data,2);self.c=entry(data,3);self.p=entry(data,9);self.raw={};self.layers={}
  self.banks=[graphics_bank(self.g,b,allow_bank_aliases=True) for b in range(len(bank_offsets(self.g,allow_aliases=True)))]
  self.words=np.array(struct.unpack_from('<'+'H'*(len(self.p)//2),self.p),np.uint16)
 def layer(self,n,pb=0,gb=0):
  key=(gb,pb,n)
  if key in self.layers:return self.layers[key]
  f=self.banks[gb]['frames'][n];rk=(f['offset'],f['tile_count'])
  if rk not in self.raw:
   decoded=decode_stream(self.g,f['offset'],f['limit'],f['tile_count']*128)
   need(decoded.serialize()==self.g[decoded.start:decoded.end],'압축 스트림 무변경 왕복 불일치')
   self.raw[rk]=decoded
  raw=self.raw[rk];cp=composition_frame(self.c,pb,n);arr=np.zeros((384,384),np.uint8)
  # Armor native renderer supplies a fixed CLUT; part-local CLUT bits are ignored.
  local=local_composition(cp) if pb in (5,6,7,8) and gb==0 else cp
  if cp['parts']:
   pix,size,bb,_=compose_indices(raw.data,f['tile_count'],local,allowed_cluts={0,1,2,3})
   small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);ys,xs=np.nonzero(small)
   yy,xx=ys+bb[1]+160,xs+bb[0]+160
   need(not len(xx) or (xx.min()>=0 and xx.max()<384 and yy.min()>=0 and yy.max()<384),'384 canvas밖 픽셀')
   arr[yy,xx]=small[ys,xs]
  else:bb=None
  rec={'graphics_bank':gb,'composition_bank':pb,'frame':n,'parts':cp['parts'],'bounds':bb,'stream_offset':f['offset'],'stream_end':raw.end,'tile_count':f['tile_count'],'decoded_sha256':sha(raw.data),'indexed_sha256':sha(arr.tobytes())}
  self.layers[key]=(arr,rec);return arr,rec
 def rgba(self,a,start=0):
  words=self.words[start:start+max(16,int(a.max())+1)]
  table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255] for i,w in enumerate(words)],np.uint8)
  return Image.fromarray(table[a])
 def composite(self,n,mask=0,arm=2):
  a,m=self.layer(n);im=self.rgba(a);layers=[m]
  for bit,pb in DRAW_ORDER:
   if not(mask&bit):continue
   a,m=self.layer(n,pb);im.alpha_composite(self.rgba(a,32 if pb==7 and arm==2 else 16));layers.append(m)
  return im,layers

def metrics(im):
 a=np.asarray(im);yy,xx=np.nonzero(a[:,:,3])
 if not len(xx):return {'opaque_pixels':0,'bbox':None,'size':[0,0]}
 return {'opaque_pixels':len(xx),'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'size':[int(xx.max()+1-xx.min()),int(yy.max()+1-yy.min())],'centroid':[float(xx.mean()-160),float(yy.mean()-160)]}
def animation_map(exe):
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text('utf8'));base=cfg['executable']['load_address']
 def at(address,n):
  off=address-base+2048;need(2048<=off<=len(exe)-n,'animation outside exe');return exe[off:off+n]
 animations=[];refs={n:[] for n in range(237)}
 for aid in range(cfg['animation_table_count']):
  address=struct.unpack('<I',at(cfg['animation_table_address']+aid*4,4))[0];pos=0;seen=set();steps=[]
  while pos not in seen:
   need(pos>=0 and len(seen)<512,'bad animation');seen.add(pos)
   duration,event,step,frame=struct.unpack('<bbbB',at(address+pos*4,4));steps.append({'position':pos,'duration_ticks':duration,'event':event,'relative_step':step,'frame':frame})
   if aid not in refs.setdefault(frame,[]):refs[frame].append(aid)
   pos+=step
  animations.append({'id':aid,'address':address,'steps':steps,'loop_to':pos,'event_branch_semantics_verified':False})
 return animations,refs
def page(items,idle,path,cols=4,scale=2):
 boxes=[im.getchannel('A').getbbox() for _,im in items]+[idle.getchannel('A').getbbox()];boxes=[b for b in boxes if b]
 # Shared world window for the entire page, including idle and every effect.
 box=(min([156]+[b[0] for b in boxes])-3,min([156]+[b[1] for b in boxes])-3,max([164]+[b[2] for b in boxes])+3,max([180]+[b[3] for b in boxes])+3)
 need(0<=box[0]<box[2]<=384 and 0<=box[1]<box[3]<=384,'contactsheet window exceeds source')
 w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale;cw,ch=2*w+16,h+38;rows=math.ceil(len(items)/cols)
 board=Image.new('RGB',(cw*cols,ch*rows),(26,32,43));dr=ImageDraw.Draw(board)
 for i,(label,im) in enumerate(items):
  x,y=i%cols*cw,i//cols*ch;dr.text((x+3,y+1),label,font=FONT,fill='white')
  for j,src in enumerate((idle,im)):
   xx=x+j*(w+8);yy=y+32;dr.text((xx+2,y+17),'idle 0' if j==0 else'pose',font=FONT,fill='#afbdd0')
   dr.line((xx+(160-box[0])*scale,yy,xx+(160-box[0])*scale,yy+h),fill='#334654')
   dr.line((xx,yy+(160-box[1])*scale,xx+w,yy+(160-box[1])*scale),fill='#334654')
   crop=src.crop(box).resize((w,h),Image.Resampling.NEAREST);board.paste(crop,(xx,yy),crop)
   if src.getchannel('A').getbbox():need(src.getchannel('A').crop(box).getbbox() is not None,'lost pose')
 board.save(path)
 return {'path':relative(path),'window_world':[v-160 for v in box],'no_clipping':True,'scale':scale,'idle_beside_every_pose':True}

def usage(form,n):
 if n in [105,*range(175,183)]:return '원본 예약/빈 참조; 실제 조립 결과 확인'
 if 184<=n<=203:return '라이드 아머 탑승 머리만; 전체 몸체 비교 금지'
 if n in (126,127,128,129,130,131,132,134,157,158,159,160):return '등장/전송 효과·전환 자세; 대기 체격과 직접 비교 금지'
 if 213<=n<=230 and form=='base':return '무아머 상태에서는 이 아머 전용 동작의 도달성 없음; 물리 참조만 보존 수집'
 if 217<=n<=230 and form=='ultimate_before':return '캡슐 전 미획득 기술; 공용 표시는 15이나 정상 플레이 도달성 없음'
 return '플레이어 표시 참조; 개별 실제 실행 여부 별도'

def export(character,with_masks=False):
 source,assets,records=read(character);out=OUT/character;out.mkdir(parents=True,exist_ok=True);work=TASK/character;work.mkdir(parents=True,exist_ok=True)
 for name,data in assets.items():(work/name).write_bytes(data)
 animations,arefs=animation_map(assets['SLUS_005.61']);write(out/'animations.json',animations)
 arcs={n:Archive(assets[n]) for n in ('PL00_U.ARC','PL02_U.ARC')}
 forms=[('base','기본형','PL00_U.ARC',0,2),('fourth','포스아머 풀파츠 / arm2','PL00_U.ARC',15,2),('fourth_arm1','포스아머 풀파츠 / arm1','PL00_U.ARC',15,1),('ultimate_before','얼티밋 캡슐 전 / 재킷','PL02_U.ARC',15,2),('ultimate_after','얼티밋 획득 후 / 수영복','PL02_U.ARC',0,2)]
 manifest={'schema_version':1,'character':character,'project':SOURCES[character][0],'source_bin':relative(source),'source_sha256':SOURCES[character][2],'origin':[160,160],'canvas':[384,384],'native_scale':1,'runtime_verified':False,'source_readonly':True,'assets':{n:{'sha256':sha(d),'record':records[n]} for n,d in assets.items()},'forms':[],'frames':[],'sheets':[],'exceptions':[],'coverage':{},'notes':['원본 픽셀을 그대로 합성한 정적 자료이며 게임 실행 검증이 아니다.','원점·픽셀크기·팔레트를 유지하고 프레임별 자동 확대/축소를 하지 않는다.','윤곽 bbox 차이는 결함 판정이 아니다. 몸 숙임·원근·이펙트·탑승 머리를 구분한다.','배경 혼합/피격 깜박임/무기별 런타임 CLUT 순환은 정지 팔레트 시트에 재현되지 않는다.','Ultimate의 217..230은 획득 후에도 원래 표시 mask15를 유지한다.']}
 need(set(sum(GROUPS.values(),[]))==set(range(237)),'Missing semantic group')
 for form,label,name,mask,arm in forms:
  arc=arcs[name];folder=out/'native'/form;folder.mkdir(parents=True,exist_ok=True);images={};fm={'id':form,'label':label,'archive':name,'logical_state':form,'idle_ref':0,'idle_path':relative(folder/'000.png'),'arm_type':arm,'sheets':[]}
  for n in range(len(arc.banks[0]['frames'])):
   actual_mask=15 if form=='ultimate_after' and 217<=n<=230 else mask
   try:im,layers=arc.composite(n,actual_mask,arm);status='blank' if im.getchannel('A').getbbox() is None else'rendered'
   except (ValueError,IndexError) as e:
    # No guessed pixels for partial VRAM/reserved composition references.
    manifest['exceptions'].append({'form':form,'ref':n,'error':str(e),'classification':'unreconstructed_reference'});im=Image.new('RGBA',(384,384));layers=[];status='unreconstructed'
   path=folder/f'{n:03}.png';im.save(path);images[n]=im;group=next(k for k,v in GROUPS.items() if n in v)
   manifest['frames'].append({'id':f'{form}_{n:03}','form':form,'ref':n,'group':group,'group_label':GROUP_NAMES[group],'path':relative(path),'origin':[160,160],'display_mask':actual_mask,'arm_type':arm,'status':status,'usage':usage(form,n),'animation_ids':arefs.get(n,[]),'rgba_sha256':sha(im.tobytes()),'png_sha256':sha(path.read_bytes()),**metrics(im),'layers':layers})
  sheets=out/'sheets'/form;sheets.mkdir(parents=True,exist_ok=True)
  for group,refs in GROUPS.items():
   for start in range(0,len(refs),24):
    part=refs[start:start+24];path=sheets/f'{group}_{start//24:02}.png'
    record=page([(f'{n:03} {GROUP_NAMES[group]}',images[n]) for n in part],images[0],path)
    record.update(form=form,group=group,refs=part);manifest['sheets'].append(record);fm['sheets'].append(record['path'])
  manifest['forms'].append(fm);write(out/'manifest.json',manifest);print(character,form,'complete',flush=True)
 # Capsule particles use palette entry rows chosen at runtime; neutral index
 # visualization is separate and explicitly not a claimed live effect color.
 ghost_colors=np.array([0,0xFFFF,0xEAD5,0xC210]+[0xFFFF]*12,np.uint16)
 for name,arc in arcs.items():
  form='capsule_fourth' if name=='PL00_U.ARC' else'capsule_ultimate';folder=out/'native'/form;folder.mkdir(parents=True,exist_ok=True);items=[]
  for gb in range(10,14):
   for n in range(len(arc.banks[gb]['frames'])):
    a,m=arc.layer(n,gb+8,gb);words=ghost_colors
    table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i==0 else 255] for i,w in enumerate(words)],np.uint8)
    im=Image.fromarray(table[a%16]);p=folder/f'bank{gb}_{n:02}.png';im.save(p);items.append((f'bank{gb} frame{n}',im))
    manifest['frames'].append({'id':f'{form}_{gb}_{n}','form':form,'ref':n,'group':'capsule_ghost','path':relative(p),'origin':[160,160],'status':'rendered' if im.getbbox() else'blank','palette_scope':'인덱스 가시화용 중성 팔레트; 실기 CLUT 색상 아님','rgba_sha256':sha(im.tobytes()),**metrics(im),'layers':[m]})
  for start in range(0,len(items),24):
   p=out/'sheets'/f'{form}_{start//24:02}.png';r=page(items[start:start+24],Image.open(out/'native'/('fourth' if name=='PL00_U.ARC' else'ultimate_after')/'000.png'),p);r.update(form=form,group='capsule_ghost',refs=[s[0] for s in items[start:start+24]]);manifest['sheets'].append(r)
 # Preserve bank inventory, including effects not falsely called missing bodies.
 manifest['graphics_banks']={name:[{'bank':b,'count':len(v['frames']),'offset':v['base'],'end':v['end'],'classification':'main_player' if b==0 else'capsule_ghost' if b>=10 else'auxiliary_bank_mapping_pending'} for b,v in enumerate(arc.banks)] for name,arc in arcs.items()}
 manifest['coverage']={'main_forms':len(forms),'main_refs_per_form':237,'main_frame_records':len(forms)*237,'capsule_refs':92,'partial_armor_masks':'pending' if not with_masks else'all16both_arm_types','animation_count':len(animations),'unreconstructed':len(manifest['exceptions'])}
 write(out/'manifest.json',manifest)
 if with_masks:export_masks(character,arcs['PL00_U.ARC'],manifest)
 write(out/'manifest.json',manifest);need(digest(source)==SOURCES[character][2],'입력 BIN이 변경됨')
 print(json.dumps({'character':character,'frames':len(manifest['frames']),'exceptions':manifest['exceptions'],'sheets':len(manifest['sheets'])},ensure_ascii=False),flush=True)

def export_masks(character,arc,manifest):
 out=OUT/character;target=out/'partial_armor';target.mkdir(parents=True,exist_ok=True);records=[]
 manifest['sheets']=[r for r in manifest['sheets'] if r.get('form')!='partial_armor']
 for arm in (1,2):
  for n in range(237):
   images=[]
   for mask in range(16):
    try:im,_=arc.composite(n,mask,arm);status='blank' if im.getbbox() is None else'rendered'
    except (ValueError,IndexError) as e:im=Image.new('RGBA',(384,384));status='unreconstructed'
    records.append({'ref':n,'mask':mask,'arm_type':arm,'rgba_sha256':sha(im.tobytes()),'status':status,**metrics(im)})
    images.append((f'mask {mask:02X}',im))
   # A full16-mask view at the same reference, each alongside its own idle.
   boxes=[q.getbbox() for _,q in images if q.getbbox()];b=(min([150]+[q[0] for q in boxes])-4,min([132]+[q[1] for q in boxes])-4,max([175]+[q[2] for q in boxes])+4,max([184]+[q[3] for q in boxes])+4)
   w,h=(b[2]-b[0])*2,(b[3]-b[1])*2;cw=max(w,132);board=Image.new('RGB',(cw*8,(h+24)*2),(26,32,43));dr=ImageDraw.Draw(board)
   for mask,(_,im) in enumerate(images):
    x,y=mask%8*cw,mask//8*(h+24);dr.text((x+3,y+2),f'{n:03} | mask {mask:02X} | arm{arm}',font=FONT,fill='white');crop=im.crop(b).resize((w,h),Image.Resampling.NEAREST);board.paste(crop,(x+(cw-w)//2,y+24),crop)
   path=target/f'arm{arm}_ref{n:03}.png';board.save(path)
   manifest['sheets'].append({'path':relative(path),'form':'partial_armor','arm_type':arm,'group':'all16masks','refs':[n],'masks':list(range(16)),'window_world':[v-160 for v in b],'scale':2,'no_clipping':True})
  print(character,'partial arm',arm,'complete',flush=True)
 write(target/'coverage.json',{'count':len(records),'records':records,'native_png_omitted':True,'reason':'각237참조×16마스크×2armtype은 동일ref 비교시트로 모두 보존. 중복 native 파일 증식 방지.'})
 manifest['coverage']['partial_armor_masks']={'masks':16,'arm_types':[1,2],'refs_per_mask':237,'compositions':len(records),'coverage':relative(target/'coverage.json')}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--character',choices=list(SOURCES));ap.add_argument('--masks',action='store_true');ap.add_argument('--masks-only',action='store_true');args=ap.parse_args()
 for character in [args.character] if args.character else SOURCES:
  if args.masks_only:
   _,assets,_=read(character);manifest=json.loads((OUT/character/'manifest.json').read_text('utf8'));export_masks(character,Archive(assets['PL00_U.ARC']),manifest);write(OUT/character/'manifest.json',manifest)
  else:export(character,args.masks)
