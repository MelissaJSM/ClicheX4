from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,gfx,parts,pal
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import front,component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_bank_patch import patch_bank
from src.psx_frame_edit import read_indexed_png
from src.psx_ice import BODY,SCOPE,PRESERVED_BODY,PRESERVED_EFFECTS,flash_from_recovery
D=Path(__file__).parent;P=D.parent/'air_spin_v4';old=ROOT/'out/ver_buki_riko/riko_bank1_20261025T090314908139Z'
recipe=json.loads((P/'recipe.json').read_text());keys=np.load(D/'key_pixels.npz');reg={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())}
worlds={};placements={};checks=[]
def head_loc(a):
 matches=[]
 for y in range(a.shape[0]-18):
  for x in range(a.shape[1]-22):
   if np.array_equal(a[y:y+19,x:x+23][front!=0],front[front!=0]):matches.append((x,y))
 if len(matches)!=1:raise ValueError(('Native head not unique',matches))
 return matches[0]
def cropped(path):
 a=np.array(Image.open(path));ys,xs=np.nonzero(a);return a[ys.min():ys.max()+1,xs.min():xs.max()+1]
def cape(a,phase,air):
 a=a.copy();out=a.copy();h,w=a.shape
 # Postprocess the outer cloth only; the body, shoulder attachment and head are fixed.
 for x in range(26,w):
  for y in range(3,26 if air else 28):
   if y<h:out[y,x]=0
 for x in range(26,w):
  dy=phase if x>=29 else 0
  for y in range(3,min(h,26 if air else 28)):
   if a[y,x]:out[y+dy,x]=a[y,x]
 return out
idle=cropped(old/'idle_147.png')
recovery=cropped(old/'frame_246.png')
for n in sorted(BODY):
 if n in (132,88):continue
 if n<132:
  a=(idle if n==86 else recovery).copy();hp=head_loc(a);target_y=24-a.shape[0];target_x=-12-hp[0]
 elif n<=137:
  phase={133:0,134:0,135:-1,136:0,137:1}[n];a=cape(keys['134'],phase,True);hp=head_loc(a);target_x=-12-hp[0];target_y=-30-hp[1]
 else:
  phase={138:-1,139:0,140:1,141:0,142:-1,143:0}[n];a=cape(keys['140'],phase,False);hp=head_loc(a);target_x=-12-hp[0];target_y=24-a.shape[0]
 _,bounds,safe=original(n);h,w=a.shape;choices=[]
 for dy in (0,) if n<132 or n>=138 else range(-2,3):
  for dx in range(-5,6):
   x,y=target_x+dx,target_y+dy;bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]));choices.append((bad*10000+abs(dx)+abs(dy)*3,bad,x,y))
 _,bad,x,y=min(choices);world=np.zeros((192,192),np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a
 if bad:raise ValueError(('Outside',n,bad))
 groups=component(world!=0)
 if len(groups)!=1:raise ValueError(('Detached body/cape',n,[len(g) for g in groups]))
 worlds[n]=world;placements[str(n)]=[x+hp[0],y+hp[1]];checks.append({'frame':n,'head_world':placements[str(n)],'outside':bad,'components':[len(g) for g in groups],'foot_world':y+h-1})
worlds[88]=np.frombuffer(flash_from_recovery(worlds[87].tobytes(),(192,192))[0],np.uint8).reshape(192,192);placements['88']=placements['87']
frames={};records={}
for key,r in recipe['frames'].items():
 src=P/r['file'];shutil.copyfile(src,D/src.name);records[key]=r;frames[int(key)]=read_indexed_png(src,pal)
for n,world in worlds.items():
 _,b,_=original(n);a=world[96+b[1]:96+b[3],96+b[0]:96+b[2]];p=D/f'bank1_{n:03d}.png';save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,p);records[str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};frames[n]=(a.tobytes(),(a.shape[1],a.shape[0]))
preserved=(set(recipe['preserved_effect_frames'])-BODY)|PRESERVED_BODY|PRESERVED_EFFECTS
for n in sorted(PRESERVED_BODY|PRESERVED_EFFECTS):
 a,_,_=original(n);p=D/f'bank1_{n:03d}.png';save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,p);records[str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};frames[n]=(a.tobytes(),(a.shape[1],a.shape[0]))
_,packing=patch_bank(gfx,parts,1,5,frames,preserved,clear_unreferenced=True)
recipe.update(scope=SCOPE,frames=records,preserved_effect_frames=sorted(preserved),external_ice_effect={'animation':121,'parts_bank':6,'modified':False},
 preserved_non_effect_frames=sorted(PRESERVED_BODY),
 ice_source_scale=.063,ice_generated_art='generated_keys.png',ice_generated_art_sha256=sha256((D/'generated_keys.png').read_bytes()),ice_parent_recipe_sha256=sha256((P/'recipe.json').read_bytes()))
recipe['body_standard']['head_world_positions'].update(placements);recipe['body_standard']['head_sizes'].update({n:[23,19] for n in placements})
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8')
np.savez(D/'final_worlds.npz',**{str(n):a for n,a in worlds.items()})
sheet=Image.new('RGBA',(6*256,4*300),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,a) in enumerate(worlds.items()):
 sheet.alpha_composite(rgba(a).crop((56,40,136,128)).resize((240,264),Image.Resampling.NEAREST),(i%6*256,i//6*300+22));dr.text((i%6*256+4,i//6*300+4),str(n)+' STATIC',fill='white')
sheet.save(D/'body_review.png');print(json.dumps({'new_body_references':len(worlds),'preserved_effects':len(preserved),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))
