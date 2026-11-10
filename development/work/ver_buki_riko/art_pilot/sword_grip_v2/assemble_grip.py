"""Assemble the generated short grip against original saber effects; no ROM writes."""
from pathlib import Path
import sys,json,math,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).parent.parent/'sword_v1'))
from inspect_sword import original,rgba,pal,epal,recipe,old,arc,gmeta,gfx,parts
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import GROUND_SLASH_BODY_FRAMES,AIR_SLASH_BODY_FRAMES,SABER_EFFECT_FRAMES,patch_frames
from src.psx_frame_edit import read_indexed_png
D=Path(__file__).parent
BODY=sorted(GROUND_SLASH_BODY_FRAMES|AIR_SLASH_BODY_FRAMES)
PAIRS={n:n+1 for n in BODY if n not in (61,62,81,82,130,131,132,133,134,229,246)}
PAIRS[81]=80
previous=json.loads((D.parent/'sword_v1/registration.json').read_text())
HANDS={r['frame']:r['hand'] for r in previous}
# Explicitly registered palms, not arbitrary nearby opaque pixels.
HANDS.update({62:(1,-21),63:(-6,2),65:(-5,7),83:(-17,-1),85:(-21,8),
 105:(12,-13),107:(0,-22),109:(-10,2),213:(9,-24),215:(-13,3),217:(-8,-3),
 219:(17,-6),221:(12,-13),223:(18,-23),225:(10,-22),227:(9,-18),229:(6,-23),
 230:(11,-7),232:(-16,0),234:(-12,-1),236:(23,-6),238:(18,-7),240:(9,-8),242:(10,-4),244:(3,-2)})
REST_ANGLES={61:-110,62:20,82:-100,130:-120,131:15,132:15,133:145,134:145,229:-65,246:145}
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]

def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n','utf8')

def make_master():
 im=Image.open(D/'generated_grip.png').convert('RGBA');a=np.array(im);ys,xs=np.nonzero(a[:,:,3]>=220)
 box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=np.array(im.crop(box))
 scale=11/crop.shape[0];size=(math.ceil(crop.shape[1]*scale),11)
 xs=np.minimum(np.floor((np.arange(size[0])+.5)/scale).astype(int),crop.shape[1]-1)
 ys=np.minimum(np.floor((np.arange(size[1])+.5)/scale).astype(int),crop.shape[0]-1)
 a=crop[ys[:,None],xs[None,:]];mask=a[:,:,3]>=220
 colors=np.array(rgba(np.arange(16,dtype=np.uint8).reshape(1,16)))[0,:,:3].astype(int)
 result=np.zeros(a.shape[:2],np.uint8)
 result[mask]=np.argmin(((a[mask,:3].astype(int)[:,None,:]-colors[None,1:])**2).sum(2),axis=1)+1
 pivot=[round((483-box[0])*scale-.5),round((989-box[1])*scale-.5)]
 save_image(result.tobytes(),size,pal,D/'grip_native.png')
 write(D/'grip_master.json',{'source':'generated_grip.png','source_sha256':sha256((D/'generated_grip.png').read_bytes()),'crop':box,'uniform_scale':scale,'size':size,'grip_pivot':pivot,'axis':'up','palette_sha256':recipe['palette_sha256']})
 return result,pivot

def orient(master,pivot,angle):
 yy,xx=np.indices((64,64));dx,dy=xx-32,yy-32;t=math.radians(angle+90);c,s=math.cos(t),math.sin(t)
 sx=np.rint(c*dx+s*dy+pivot[0]).astype(int);sy=np.rint(-s*dx+c*dy+pivot[1]).astype(int)
 valid=(sx>=0)&(sy>=0)&(sx<master.shape[1])&(sy<master.shape[0]);a=np.zeros((64,64),np.uint8);a[valid]=master[sy[valid],sx[valid]]
 return a

def world_image(n):
 a,b,safe=original(n);w=np.zeros((192,192),np.uint8);v=np.array(Image.open(old/recipe['frames'][str(n)]['file']))
 w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=v
 cov=np.zeros_like(w,bool);cov[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe
 return w,b,cov

def composed(n,world):
 im=rgba(world);e=PAIRS.get(n)
 if e:
  a,b,s=original(e);im.alpha_composite(rgba(a,epal),(96+b[0],96+b[1]))
 return im

def preview(worlds):
 ns=[61,62,63,65,71,75,83,87,93,99,107,109,111,117,127,134,213,215,217,221,225,229,242,246]
 board=Image.new('RGBA',(6*384,4*312),(35,40,50));draw=ImageDraw.Draw(board)
 for i,n in enumerate(ns):
  pic=composed(n,worlds[n]).crop((32,40,128,114)).resize((384,296),Image.Resampling.NEAREST)
  board.alpha_composite(pic,(i%6*384,i//6*312+16));draw.text((i%6*384+4,i//6*312+2),str(n)+' SHORT GRIP / STATIC',fill='white')
 board.save(D/'grip_effect_review.png')
 pic=rgba(np.array(Image.open(D/'grip_native.png'))).resize((280,520),Image.Resampling.NEAREST)
 pic.save(D/'grip_native_preview.png')

def run():
 master,pivot=make_master();worlds={};regs=[]
 new={**recipe,'frames':dict(recipe['frames']),'preserved_effect_frames':sorted(SABER_EFFECT_FRAMES),'sword_effect_edits':{}}
 for rec in recipe['frames'].values():shutil.copyfile(old/rec['file'],D/rec['file'])
 for n in BODY:
  w,b,cov=world_image(n);hx,hy=HANDS[n];e=PAIRS.get(n);target=None;gap=None
  if e:
   a,eb,safe=original(e);ys,xs=np.nonzero(a);x=xs+eb[0];y=ys+eb[1];dist=(x-hx)**2+(y-hy)**2
   # Overlapping trails already cover the emitter. Use their local centroid for direction.
   if dist.min()<16:
    ids=(dist>=16)&(dist<=100)
    if ids.any():tx,ty=float(x[ids].mean()),float(y[ids].mean())
    else:j=int(np.argmin(dist));tx,ty=int(x[j]),int(y[j])
   else:j=int(np.argmin(dist));tx,ty=int(x[j]),int(y[j])
   angle=math.degrees(math.atan2(ty-hy,tx-hx));j=int(np.argmin(dist));target=[int(x[j]),int(y[j])];gap=math.sqrt(float(dist[j]))
  else:angle=REST_ANGLES[n]
  layer=np.zeros_like(w);layer[96+hy-32:96+hy+32,96+hx-32:96+hx+32]=orient(master,pivot,angle)
  # The only extended segment joins the emitter to the nearest original trail;
  # never a separately posed full sword and never any effect-palette edits.
  if target and 9<gap<=24:
   for d in np.arange(7,gap+.5,.25):
    x=round(hx+math.cos(math.radians(angle))*d);y=round(hy+math.sin(math.radians(angle))*d)
    layer[96+y,96+x]=10
  px,py=recipe['body_standard']['head_world_positions'][str(n)]
  protected=np.zeros_like(cov);protected[96+py:96+py+19,96+px:96+px+23]=front!=0
  glove=np.zeros_like(cov);glove[96+hy-2:96+hy+3,96+hx-2:96+hx+3]=True
  mask=(layer!=0)&cov&~protected&((w==0)|glove);result=w.copy();result[mask]=layer[mask]
  # Short components must meet the original glove and never erase body pixels.
  overlap=int(np.count_nonzero(mask&(w!=0)));assert overlap>0,f'No hand contact {n}'
  outside=int(np.count_nonzero((layer!=0)&~cov));worlds[n]=result
  name=f'frame_{n:03d}.png';data=result[96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes()
  save_image(data,(b[2]-b[0],b[3]-b[1]),pal,D/name);new['frames'][str(n)]={'file':name,'sha256':sha256((D/name).read_bytes())}
  regs.append({'frame':n,'effect':e,'hand':[hx,hy],'angle':round(angle,3),'trail_nearest':target,'gap':gap,'masked_by_part_coverage':outside,'changed_pixels':int((result!=w).sum()),'grip_body_overlap':overlap})
 new['sword_production']={'kind':'closed_hand_short_hilt_to_original_trail','generated_source':'generated_grip.png','source_sha256':sha256((D/'generated_grip.png').read_bytes()),'master':'grip_native.png','master_sha256':sha256((D/'grip_native.png').read_bytes()),'full_blade_removed':True,'effect_pixels_identical_to_original':True,'art_review_pending':True}
 write(D/'recipe.json',new);write(D/'registration.json',regs);np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()});preview(worlds)
 frames={int(n):read_indexed_png(D/r['file'],pal) for n,r in new['frames'].items()}
 _,packing=patch_frames(arc,gmeta,gfx,parts,frames,struct.pack('<16H',*pal))
 write(D/'packing_checks.json',packing)
 print(json.dumps({'body':len(worlds),'effect_edits':0,'outside':[r for r in regs if r['masked_by_part_coverage']],'minimum_spare':min(r['original_bytes']-r['encoded_bytes'] for r in packing['compression'])}))

if __name__=='__main__':run()
