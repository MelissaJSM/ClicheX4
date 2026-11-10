"""나나 헌터베이스12참조를 공유 얼굴·같은 축척과 원래 UI 공간에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_selection_portrait import RGB
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ui import panel_layout
from scripts.prepare_rin_hunter import repack_bank
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba
PARENT=ROOT/'out/ver_rin_nana/nana_select_portrait_20261030T021840031458Z'
PARENT_SHA='147882a5c152e91175f63e82e03d4df941d7c2a806dfda482e4b094797e3895b'
ART=ROOT/'work/ver_rin_nana/illustrations/nana_hunter_v1'
ART_SHA='44f2b03a797b85d50e5e871bb492bb58376da708bd6252d254ac515ef00649d0'
RESOURCES={'ST0D_0X.ARC':(9612,276480,'73f6fc52bced68afcac7cb4ca5be47187a04a43a09b2f8f09c67e858e60d6ca6'),'COL0D_0X.ARC':(176,6144,'1f68a6287960864272b6593edecbd6c8854a26a5052016a3191107d48a4e9350')}
LO,HI=63488,75776
WORDS=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)for r,g,b in RGB];PAL=struct.pack('<16H',*WORDS)
COLORS=np.array([[int(w>>s&31)*255//31 for s in(0,5,10)]for w in WORDS[1:]],np.int32)

def sources():
 m=json.loads((PARENT/'manifest.json').read_text('utf8'))
 if m['task']!='x_nana'or digest(PARENT/'rin_nana.bin')!=PARENT_SHA or m['modified_bin']['sha256']!=PARENT_SHA:raise ValueError('Accepted Nana parent changed')
 records=[];original={}
 with(PARENT/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,m['modified_bin']['size']);iso={q['path']:q for q in d.inspect()['files']}
  for n,(lba,size,h)in RESOURCES.items():
   q=iso['/ARC/'+n+';1']
   if(q['lba'],q['size'])!=(lba,size):raise ValueError('HQ location changed')
   raw=d.read(lba,size)
   if sha256(raw)!=h:raise ValueError('HQ source changed')
   original[n]=raw;records.append({**q,'sha256':h})
 return m,records,original

def poses(out):
 if digest(ART/'generated.png')!=ART_SHA:raise ValueError('Nana HQ original art changed')
 sheet=Image.open(ART/'generated.png').convert('RGBA')
 if sheet.size!=(1536,1024):raise ValueError('Unexpected HQ sheet geometry')
 result=[];registration=[]
 for n in range(6):
  im=sheet.crop((n%3*512,n//3*512,n%3*512+512,n//3*512+512));a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);im=Image.fromarray(a);box=im.getchannel('A').getbbox();im=im.crop(box)
  scale=78/im.height if n==4 else 94/498;size=(round(im.width*scale),round(im.height*scale));im=im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA');a=np.array(im);px=np.where(a[:,:,3]>=128,((a[:,:,:3].astype(np.int32)[:,:,None,:]-COLORS)**2).sum(3).argmin(2)+1,0).astype('uint8')
  yy,xx=np.nonzero(px);floor=int(yy.max())+1;_,feet=np.nonzero(px[max(0,floor-(3 if n==4 else 18)):floor]);cx=(int(feet.min())+int(feet.max()))/2;wx=-8.5 if n==4 else -.5;fy=49 if n==3 else 48;x=round(128+wx-cx);y=64+fy-floor
  canvas=np.zeros((144,256),np.uint8)
  if x<0 or y<0 or x+size[0]>256 or y+size[1]>144:raise ValueError('HQ pose clips work canvas')
  canvas[y:y+size[1],x:x+size[0]]=px;result.append(canvas);registration.append({'pose':n,'source_bbox':box,'scale':scale,'size':size,'world_bounds':[x-128,y-64,x+size[0]-128,y+size[1]-64],'floor':fy,'foot_center':wx})
  save_image(canvas.tobytes(),(256,144),WORDS,out/f'pose_{n}.png')
 board=Image.new('RGB',(6*256,144*4),(38,43,58));dr=ImageDraw.Draw(board)
 for n,a in enumerate(result):
  im=Image.open(out/f'pose_{n}.png').convert('RGBA').crop((96,8,164,120)).resize((272,448),0);board.paste(im,(n*256,50),im);dr.text((n*256+5,10),str(n),fill='white')
 board.save(out/'poses_4x.png');(out/'registration.json').write_text(json.dumps(registration,indent=2)+'\n','utf8')
 return result,registration

def prepare(out,preview=False):
 out=out.resolve()
 if not out.is_relative_to(ART)or out.exists():raise ValueError('Fresh Nana HQ output required')
 out.mkdir();a,registration=poses(out)
 if preview:return
 m,records,original=sources();world={}
 eye=np.zeros_like(a[0],bool);eye[30:33,128:132]=True;eye[31:33,134:136]=True
 shifted=np.zeros_like(a[1]);shifted[:,1:]=a[1][:,:-1]
 eye &=np.isin(a[0],[1,2,4,5,6,11,13,14,15])&np.isin(shifted,[1,2,4,5,6,11,13,14,15])
 closed=a[0].copy();closed[eye]=shifted[eye];half=a[0].copy();line=eye.copy();line[:31]=False;line[32:]=False;half[line]=closed[line]
 gesture=a[2].copy();gesture[:39]=a[0][:39];gesture[72:]=a[0][72:]
 mouth=(slice(34,36),slice(130,134));open_gesture=gesture.copy();open_gesture[mouth]=a[2][mouth];mid_gesture=gesture.copy();mid_gesture[35,131]=open_gesture[35,131]
 neutral_talk=a[0].copy();neutral_talk[mouth]=open_gesture[mouth]
 reaction=a[3].copy();reaction_closed=reaction.copy();reaction_closed[36:38,129:132]=a[0][33:35,130:133];reaction_half=reaction_closed.copy();reaction_half[37,129]=reaction[37,129]
 for n,image in enumerate([a[0],half,closed,gesture,mid_gesture,open_gesture,reaction_closed,reaction_half,reaction,a[4],a[0][:,::-1].copy(),neutral_talk]):world[n]=image.copy()
 raw=original['ST0D_0X.ARC'];g=entry(raw,0x10102);p=entry(raw,10);np_=bytearray(p);targets={};layouts=[]
 # Related facial variants share identical windows, avoiding body/eye tile drift.
 groups=[[0,1,2,11],[3,4,5],[6,7,8],[9],[10]];covers={}
 for group in groups:
  union=np.logical_or.reduce([world[n]>0 for n in group]);yy,xx=np.nonzero(union);x0=max(0,int(xx.min())-1);y0=max(0,int(yy.min())-1);x1=min(256,int(xx.max())+2);y1=min(144,int(yy.max())+2);mask=union[y0:y1,x0:x1];count=min(len(aliased_composition(p,2,n)['parts'])for n in group);layout=panel_layout(mask,count)
  key=sha256(mask.tobytes()+struct.pack('<III',mask.shape[0],mask.shape[1],count));cache=ART/f'cover_{key}.json'
  if not layout['fits']:
   if cache.exists():layout=json.loads(cache.read_text('utf8'))
   else:
    from scripts.solve_sprite_cover import cover
    layout=cover(mask,count,20)
    if layout['fits']:cache.write_text(json.dumps(layout,indent=2)+'\n','utf8')
  if not layout['fits']:raise ValueError(f'HQ group{group} does not fit original windows')
  for n in group:covers[n]=(x0,y0,layout['rects'])
 for n,image in world.items():
  c=aliased_composition(p,2,n);x0,y0,rects=covers[n];positions=rects+[rects[-1]]*(len(c['parts'])-len(rects))
  for q,(x,y)in zip(c['parts'],positions):
   wx=x+x0-128;wy=y+y0-64
   if not -128<=wx<=127 or not -128<=wy<=127:raise ValueError('HQ signed coordinate overflow')
   off=q['record_offset'];np_[off:off+4]=bytes((0,0,wx&255,wy&255))
  bx=min(x for x,y in rects)+x0;by=min(y for x,y in rects)+y0;ex=max(x+16 for x,y in rects)+x0;ey=max(y+16 for x,y in rects)+y0;piece=image[by:ey,bx:ex];targets[n]=(piece.tobytes(),(piece.shape[1],piece.shape[0]));save_image(image.tobytes(),(256,144),WORDS,out/f'world_{n:02}.png');save_image(piece.tobytes(),targets[n][1],WORDS,out/f'frame_{n:02}.png');layouts.append({'frame':n,'windows':len(rects),'original_windows':len(c['parts']),'bounds':[bx-128,by-64,ex-128,ey-64]})
 ng,np_,packing=repack_bank(g[LO:HI],bytes(np_),targets)
 new={'ST0D_0X.ARC':replace_entry(replace_entry(raw,0x10102,g[:LO]+ng+g[HI:]),10,np_)};col=original['COL0D_0X.ARC'];cp=entry(col,5);new['COL0D_0X.ARC']=replace_entry(col,5,cp[:35*32]+PAL+cp[36*32:]);v=verify(original,new,world)
 for name,data in new.items():(out/name).write_bytes(data)
 (out/'palette.bin').write_bytes(PAL);board=Image.new('RGB',(6*180,2*250),(38,43,58));dr=ImageDraw.Draw(board)
 for n,image in world.items():
  im=Image.open(out/f'world_{n:02}.png').convert('RGBA').crop((80,0,176,128));im=im.resize((192,256),0);x=n%6*180;y=n//6*250;board.paste(im,(x-6,y+5),im);dr.text((x+5,y+5),str(n),fill='white')
 board.save(out/'review.png');recipe={'kind':'nana_hunter','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'generated_source':(ART/'generated.png').relative_to(ROOT).as_posix(),'generated_sha256':ART_SHA,'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ART/'prompt.txt'),'tool':'built-in image_gen','registration':registration,'display_facing':'right; departure front three-quarter','layouts':layouts,'packing':packing,'verification':v,'files':[{'source':r,'file':r['name'].split(';')[0],'sha256':sha256(new[r['name'].split(';')[0]])}for r in records]};(out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'packing':packing,'verification':v}))

def verify(original,new,world):
 if set(original)!=set(new)or any(len(original[n])!=len(new[n])for n in original):raise ValueError('HQ resource scope/length differs')
 a,b=original['ST0D_0X.ARC'],new['ST0D_0X.ARC'];g,ng=entry(a,0x10102),entry(b,0x10102);p,np_=entry(a,10),entry(b,10)
 if g[:LO]!=ng[:LO]or g[HI:]!=ng[HI:]or replace_entry(replace_entry(a,0x10102,ng),10,np_)!=b or len(p)!=len(np_):raise ValueError('Other HQ texture/data changed')
 col=original['COL0D_0X.ARC'];cp=entry(col,5)
 if replace_entry(col,5,cp[:35*32]+PAL+cp[36*32:])!=new['COL0D_0X.ARC']:raise ValueError('Other HQ palette changed')
 protected=0;checks=[];allowed=set()
 for bank in range(struct.unpack_from('<I',p)[0]//4):
  count=aliased_composition(p,bank,0)['bank_frame_count']
  for n in range(count):
   c,nc=aliased_composition(p,bank,n),aliased_composition(np_,bank,n)
   if bank!=2:
    if c!=nc:raise ValueError('Other HQ bank changed')
    protected+=1;continue
   if len(c['parts'])!=len(nc['parts'])or nc['bank_frame_count']!=12 or any(q['clut']or q['flip_x']or q['flip_y']or q['unknown_flags']for q in nc['parts']):raise ValueError('Target part count/flags/palette changed')
   for q in c['parts']:allowed.update(range(q['record_offset'],q['record_offset']+4))
   px,sz,bb,_=compose_static(ng[LO:HI],local_composition(nc));got={(i%sz[0]+bb[0],i//sz[0]+bb[1]):v for i,v in enumerate(px)if v};arr=world[n];want={(int(x)-128,int(y)-64):int(arr[y,x])for y,x in np.argwhere(arr)}
   if got!=want:raise ValueError('HQ world pixels/clipping differ')
   pic,_=render_static_rgba(ng[LO:HI],nc,{0:WORDS});colors=[tuple((w>>s&31)*255//31 for s in(0,5,10))+(255 if i else 0,)for i,w in enumerate(WORDS)]
   if pic.tobytes()!=bytes(v for i in px for v in colors[i]):raise ValueError('Native part palette render differs')
   checks.append({'frame':n,'bounds':bb,'size':sz,'opaque_pixels':len(got),'native_clut_verified':True})
 if any(x!=y and i not in allowed for i,(x,y)in enumerate(zip(p,np_))):raise ValueError('HQ animation header changed')
 eye=np.zeros((144,256),bool);eye[30:33,128:132]=True;eye[31:33,134:136]=True
 for n in(1,2):
  diff=world[n]!=world[0]
  if np.any(diff&~eye)or not 1<=np.count_nonzero(diff)<=16:raise ValueError('Idle blink moves body/mouth or misses eyes')
 for base,ids,rect in((3,[4,5],(130,34,134,36)),(6,[7,8],(129,36,132,38)),(0,[11],(130,34,134,36))):
  mask=np.zeros((144,256),bool);x,y,ex,ey=rect;mask[y:ey,x:ex]=True
  for n in ids:
   diff=world[n]!=world[base]
   if np.any(diff&~mask)or not 1<=np.count_nonzero(diff)<=8:raise ValueError('Speaking frame changes beyond mouth')
 return {'frames':checks,'other_hq_frame_records_preserved':protected,'other_texture_banks_exact':True,'palette_row':35,'all_target_cluts_zero':True,'fixed_archive_and_composition_lengths':True,'animation_headers_exact':True,'idle_eye_only_changes':[int(np.count_nonzero(world[n]!=world[0]))for n in(1,2)],'runtime_verified':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--preview-only',action='store_true');v=p.parse_args();prepare(v.output,v.preview_only)
