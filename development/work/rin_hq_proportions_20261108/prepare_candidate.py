"""Generated artwork -> native fixed-size HQ bank; original timing and other banks stay exact."""
from pathlib import Path
import json,sys,struct,hashlib,argparse
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ui import panel_layout
from scripts.prepare_rin_hunter import repack_bank,verify,WORDS,PAL,LO,HI
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition
sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--pack',action='store_true');p.add_argument('--candidate',default='candidate01');p.add_argument('--source',default='generated_v1.png');p.add_argument('--prompt',default='prompt.txt');args=p.parse_args()
D=W/args.candidate;D.mkdir(exist_ok=True)
original={n:(W/'current'/n).read_bytes()for n in ('ST0D_0Z.ARC','COL0D_0Z.ARC')}
assert entry(original['COL0D_0Z.ARC'],5)[35*32:36*32]==PAL
colors=np.array([[int(w>>s&31)*255//31 for s in (0,5,10)]for w in WORDS[1:]],np.int32)
im=Image.open(W/args.source).convert('RGBA');assert im.size==(1536,1024)
poses=[];registration=[]
for n in range(6):
 cell=im.crop((n%3*512,n//3*512,(n%3+1)*512,(n//3+1)*512));a=np.array(cell);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);cell=Image.fromarray(a);bb=cell.getchannel('A').getbbox();pic=cell.crop(bb)
 if n==0:scale=104/pic.height
 size=(round(pic.width*scale),round(pic.height*scale));pic=pic.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA');a=np.array(pic)
 px=np.where(a[:,:,3]>=128,((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3).argmin(2)+1,0).astype('uint8')
 yy,xx=np.nonzero(px);floor=int(yy.max())+1
 if n<5:
  _,feet=np.nonzero(px[max(0,floor-16):floor]);center=(int(feet.min())+int(feet.max()))/2;world_floor=64;world_center=-.5
 else:
  _,feet=np.nonzero(px[max(0,floor-3):floor]);center=(int(feet.min())+int(feet.max()))/2;world_floor=50;world_center=8
 x=round(128+world_center-center);y=64+world_floor-floor;canvas=np.zeros((144,256),np.uint8)
 assert min(x,y)>=0 and x+size[0]<=256 and y+size[1]<=144
 canvas[y:y+size[1],x:x+size[0]]=px;poses.append(canvas)
 save_image(canvas.tobytes(),(256,144),WORDS,D/f'pose_{n}.png')
 registration.append({'pose':n,'source_bounds':bb,'size':size,'scale':scale,'world_position':[x-128,y-64],'foot_line':world_floor})
np.save(D/'poses.npy',np.array(poses))
(D/'registration.json').write_text(json.dumps(registration,indent=2)+'\n','utf8')
sheet=Image.new('RGB',(3*256,2*310),(32,40,52));draw=ImageDraw.Draw(sheet)
for n in range(6):
 pic=Image.open(D/f'pose_{n}.png').convert('RGBA');pic=pic.crop((80,16,176,136)).resize((192,240),Image.Resampling.NEAREST);x=n%3*256;y=n//3*310;sheet.paste(pic,(x+32,y+35),pic);draw.text((x+8,y+8),f'new pose {n}',fill='white')
sheet.save(D/'poses_review.png')
if not args.pack:print(json.dumps(registration));sys.exit()
# Localized animation windows: all rest-body pixels remain identical.
blink_mask=np.zeros_like(poses[0],bool);blink_mask[37:40,125:128]=True;blink_mask[37:40,130:133]=True
if args.source=='generated_v2.png':blink_mask[37:40,123:128]=True
blink=poses[0].copy();blink[blink_mask]=poses[1][blink_mask]
assert 1<=np.count_nonzero(blink!=poses[0])<=25
world={}
for n in range(14):
 a=poses[0 if n<=5 else 2 if n==6 else 3 if n<=9 else 4 if n<=12 else 5].copy()
 if n in (1,2):a=blink.copy()
 if n in (8,11):
  # Closed lip pixels copied from the generated closed-mouth idle face.
  left=127 if args.source=='generated_v2.png'else 128
  a[41:43,left:131]=poses[0][41:43,left:131]
 world[n]=a;save_image(a.tobytes(),(256,144),WORDS,D/f'world_{n:02d}.png')
raw=original['ST0D_0Z.ARC'];g=entry(raw,0x10102);parts=entry(raw,10);np_=bytearray(parts);targets={};layouts=[];cache={}
for n,a in world.items():
 c=aliased_composition(parts,2,n);yy,xx=np.nonzero(a);x0=max(0,int(xx.min())-1);y0=max(0,int(yy.min())-1);x1=min(a.shape[1],int(xx.max())+2);y1=min(a.shape[0],int(yy.max())+2);aa=a[y0:y1,x0:x1]
 key=sha(aa.tobytes()+bytes([len(c['parts'])]));cached=D/f'cover_{key}.json'
 layout=json.loads(cached.read_text('utf8'))if cached.exists()else panel_layout(aa>0,len(c['parts']))
 if not layout['fits']:
  from scripts.solve_sprite_cover import cover
  layout=cover(aa>0,len(c['parts']),25)
 assert layout['fits'],f'Original part capacity exceeded at {n}'
 cached.write_text(json.dumps(layout)+'\n','utf8');rects=layout['rects'];positions=rects+[rects[-1]]*(len(c['parts'])-len(rects))
 for q,(x,y)in zip(c['parts'],positions):
  wx=x+x0-128;wy=y+y0-64;assert -128<=wx<=127 and -128<=wy<=127;off=q['record_offset'];np_[off:off+4]=bytes((0,0,wx&255,wy&255))
 xa=min(x for x,y in rects);ya=min(y for x,y in rects);xb=max(x+16 for x,y in rects);yb=max(y+16 for x,y in rects);aa=aa[ya:yb,xa:xb];targets[n]=(aa.tobytes(),(aa.shape[1],aa.shape[0]));save_image(aa.tobytes(),(aa.shape[1],aa.shape[0]),WORDS,D/f'frame_{n:02d}.png');layouts.append({'frame':n,'used':len(rects),'capacity':len(c['parts'])})
ng,np_,packing=repack_bank(g[LO:HI],bytes(np_),targets)
new={'ST0D_0Z.ARC':replace_entry(replace_entry(raw,0x10102,g[:LO]+ng+g[HI:]),10,np_),'COL0D_0Z.ARC':original['COL0D_0Z.ARC']}
checks=verify(original,new,targets,world)
for n,b in new.items():(D/n).write_bytes(b)
recipe={'kind':'rin_hunter_proportions','parent':json.loads((W/'source.json').read_text('utf8'))['parent'],'art_source':str(W/args.source),'art_sha256':sha((W/args.source).read_bytes()),'prompt':str(W/args.prompt),'tool':'built-in image_gen','registration':registration,'display_facing':'right_toward_iris','departure_facing':'toward_viewer','layouts':layouts,'packing':packing,'verification':checks,'blink_pixels':int(np.count_nonzero(blink!=poses[0])),'mouth_pixels':{str(n):int(np.count_nonzero(world[n]!=world[n-1]))for n in(8,11)},'palette_preserved':True}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps({'packing':packing,'checks':checks,'blink_pixels':recipe['blink_pixels'],'mouth_pixels':recipe['mouth_pixels']}))
