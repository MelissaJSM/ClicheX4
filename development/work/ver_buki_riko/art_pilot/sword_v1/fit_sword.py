from inspect_sword import *
from scripts.extract_zero import save_image
from scripts.build_riko_idle import GROUND_SLASH_BODY_FRAMES,AIR_SLASH_BODY_FRAMES
from scripts.discover_inputs import sha256
import math,shutil
BODY=sorted(GROUND_SLASH_BODY_FRAMES|AIR_SLASH_BODY_FRAMES)
# Explicit gripping hand coordinates in the unchanged player world space.
# Angles are clockwise from right; the master points down at 90 degrees.
KEYS={61:(12,-3,-135),62:(2,-21,10),63:(-10,-5,-135),65:(-16,-3,-150),67:(-16,12,165),82:(-18,0,-90),
83:(-17,-3,-100),85:(-19,4,-100),87:(-14,-3,180),89:(18,0,10),91:(-24,-2,-75),
105:(14,-19,25),107:(1,-25,10),109:(-13,-3,-140),111:(-21,5,145),130:(-13,8,-100),131:(-23,-3,-75),133:(-11,-2,-100),
213:(10,-25,30),215:(-16,-2,-120),217:(-12,-5,-140),219:(17,-9,90),221:(16,-19,90),223:(18,-28,70),225:(16,-28,70),227:(10,-31,60),229:(12,-26,60),
230:(12,-6,-90),232:(-17,0,-100),234:(-12,-2,-125),236:(20,-6,75),238:(18,-6,75),240:(11,-5,-70),242:(4,-9,-70),244:(6,-14,-65),246:(-11,-2,-100)}
for n in range(69,82,2):KEYS[n]=KEYS[67]
for n in range(93,102,2):KEYS[n]=KEYS[91]
for n in range(113,128,2):KEYS[n]=KEYS[111]
KEYS[132]=KEYS[131];KEYS[134]=KEYS[133]
for n in range(91,102,2):KEYS[n]=(10,-2,15)
KEYS[131]=KEYS[132]=(3,-2,55)
KEYS[133]=KEYS[134]=KEYS[246]=(-8,-1,115)
PAIRS={n:n+1 for n in BODY if n not in [61,62,81,82,130,131,132,133,134,229,246]}
PAIRS[81]=80
KEYS.update({61:(12,-5,-135),62:(2,-20,35),63:(-5,0,-120),65:(-4,6,-150),83:(-18,-1,-90),85:(-21,8,-110),87:(-8,2,180),
105:(12,-14,45),107:(0,-23,-10),109:(-11,2,-120),130:(-13,10,-100),131:(12,-1,120),132:(12,-1,120),
133:(-8,2,50),134:(-8,2,50),246:(-8,2,50),
213:(9,-22,20),215:(-14,3,-90),217:(-9,-1,-140),219:(18,-6,80),221:(14,-13,80),223:(18,-23,75),225:(17,-23,75),227:(11,-18,75),229:(8,-22,75),
230:(10,-7,-90),232:(-16,0,-100),234:(-12,-1,-125),236:(23,-6,75),238:(19,-7,75),240:(9,-8,75),242:(10,-4,75),244:(3,-2,55)})
for n in range(67,82,2):KEYS[n]=(-13,12,{67:165,69:165,71:180,73:205,75:230,77:255,79:260,81:260}[n])
for n in range(91,102,2):KEYS[n]=(12,3,15)
KEYS[97]=(12,3,40);KEYS[99]=(12,3,145);KEYS[101]=(12,3,145)
for n in range(111,128,2):KEYS[n]=(-20,5,{111:145,113:145,115:155,117:175,119:195,121:220,123:240,125:250,127:255}[n])
KEYS[117]=(-20,5,245)
KEYS[225]=(10,-22,75)
def make_master():
 im=Image.open(D/'generated_sword.png').convert('RGBA');a=np.array(im);ys,xs=np.nonzero(a[:,:,3]>=220)
 box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
 scale=34/crop.height;size=(math.ceil(crop.width*scale)+1,34)
 src=np.array(crop);xs=np.floor((np.arange(size[0]))/scale).astype(int);ys=np.floor((np.arange(size[1])+.5)/scale).astype(int)
 a=np.zeros((size[1],size[0],4),np.uint8);valid=xs<src.shape[1];a[:,valid]=src[ys[:,None],xs[None,valid]]
 colors=np.array(rgba(np.arange(16,dtype=np.uint8).reshape(1,16)))[0,:,:3].astype(int)
 m=a[:,:,3]>=220;ix=np.zeros(a.shape[:2],np.uint8);ix[m]=np.argmin(((a[m,:3,None].transpose(0,2,1).astype(int)-colors[None,1:])**2).sum(2),1)+1
 # Preserve mint material instead of mapping very pale cyan to gray white.
 cyan=m&(a[:,:,1].astype(int)-a[:,:,0].astype(int)>18)&(a[:,:,2].astype(int)-a[:,:,0].astype(int)>12)&(a[:,:,1]>160)
 ix[cyan]=10
 save_image(ix.tobytes(),size,pal,D/'sword_native.png')
 # Generated grip center: source x474,y319, relative to opaque bounding box.
 pivot=[round((474-box[0])*scale+.5),round((319-box[1])*scale)]
 pivot[0]=min((x for x in range(ix.shape[1]) if ix[pivot[1],x] in (1,3,7,12)),key=lambda x:abs(x-pivot[0]))
 (D/'sword_master.json').write_text(json.dumps({'generated_sha256':sha256((D/'generated_sword.png').read_bytes()),'crop':box,'uniform_scale':scale,'size':size,'grip_pivot':pivot,'palette_sha256':recipe['palette_sha256']},indent=2),'utf8')
 return ix,pivot
def orient(master,pivot,angle):
 # One uniform native sword; inverse nearest rotation avoids holes.
 yy,xx=np.indices((96,96));dx,dy=xx-48,yy-48;t=math.radians(angle-90);c,s=math.cos(t),math.sin(t)
 sx=np.rint(c*dx+s*dy+pivot[0]).astype(int);sy=np.rint(-s*dx+c*dy+pivot[1]).astype(int)
 valid=(sx>=0)&(sy>=0)&(sx<master.shape[1])&(sy<master.shape[0]);a=np.zeros((96,96),np.uint8);a[valid]=master[sy[valid],sx[valid]]
 return a
def run():
 master,pivot=make_master();worlds={};records=[]
 for n in BODY:
  a,b,safe=original(n);body=np.array(Image.open(old/recipe['frames'][str(n)]['file']));h,w=body.shape;world=np.zeros((192,192),np.uint8);world[96+b[1]:96+b[3],96+b[0]:96+b[2]]=body
  allowed=np.zeros_like(world,bool);allowed[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe
  extended=allowed.copy();e=PAIRS.get(n)
  if e:
   ea,eb,esafe=original(e);extended[96+eb[1]:96+eb[3],96+eb[0]:96+eb[2]]|=esafe
  hx,hy,ideal=KEYS[n]
  # Snap the artist-marked palm to an actual glove pixel, excluding the head.
  hx0,hy0=recipe['body_standard']['head_world_positions'][str(n)]
  points=[]
  for dy in range(-4,5):
   for dx in range(-4,5):
    x,y=hx+dx,hy+dy
    if hx0<=x<hx0+23 and hy0<=y<hy0+19:continue
    if world[96+y,96+x]!=0:points.append((dx*dx+dy*dy,x,y))
  if not points:raise ValueError(f'No glove near anchor {n}')
  _,hx,hy=min(points);candidates=[]
  for delta in range(-180,180,5):
   angle=ideal+delta;layer=np.zeros_like(world);layer[96+hy-48:96+hy+48,96+hx-48:96+hx+48]=orient(master,pivot,angle)
   bad=int(np.count_nonzero((layer!=0)&~extended));visible=int(np.count_nonzero((layer!=0)&(world==0)))
   candidates.append((bad*10000+abs(delta)*3-visible*.1,bad,angle,visible,layer))
  _,bad,angle,visible,layer=min(candidates,key=lambda v:v[0]);out=layer.copy();out[world!=0]=world[world!=0]
  worlds[n]=out;records.append({'frame':n,'effect':e,'hand':[hx,hy],'ideal_angle':ideal,'angle':angle,'outside':bad,'outside_body':int(np.count_nonzero((layer!=0)&~allowed)),'visible_weapon_pixels':visible})
 review(worlds,D/'sword_fit.png');(D/'registration.json').write_text(json.dumps(records,indent=2),'utf8');np.savez(D/'sword_worlds.npz',**{str(n):w for n,w in worlds.items()})
 print(json.dumps(records))
def review(worlds,path):
 board=Image.new('RGBA',(6*320,math.ceil(len(worlds)/6)*300),(35,40,50));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  pic=rgba(w[48:120,56:136]).resize((320,288),Image.Resampling.NEAREST);board.alpha_composite(pic,(i%6*320,i//6*300+12));draw.text((i%6*320+4,i//6*300+2),str(n),fill='white')
 board.save(path)
if __name__=='__main__':run()
