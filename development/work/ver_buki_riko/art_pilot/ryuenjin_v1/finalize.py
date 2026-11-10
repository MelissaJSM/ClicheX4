from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,gfx,parts,pal
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_bank_patch import patch_bank
from src.psx_frame_edit import read_indexed_png
from src.psx_ryuenjin import NEW_BODY,EFFECTS,SCOPE
D=Path(__file__).parent;P=D.parent/'hyouretsuzan_v1';old=ROOT/'out/ver_buki_riko/riko_bank1_20261025T090314908139Z'
recipe=json.loads((P/'recipe.json').read_text());worlds={};placements={};checks=[]
def head_loc(a):
 matches=[]
 for y in range(a.shape[0]-18):
  for x in range(a.shape[1]-22):
   if np.array_equal(a[y:y+19,x:x+23][front!=0],front[front!=0]):matches.append((x,y))
 if len(matches)!=1:raise ValueError(('Native head not unique',matches))
 return matches[0]
def cropped(path):
 a=np.array(Image.open(path));ys,xs=np.nonzero(a);return a[ys.min():ys.max()+1,xs.min():xs.max()+1]
key,hp=normalize(sample(Image.open(D/'generated_rise_compact.png'),.038),front)
for c in component(key!=0)[1:]:
 for y,x in c:key[y,x]=0
save_image(key.tobytes(),(key.shape[1],key.shape[0]),pal,D/'key_148.png')
def cape(a,phase):
 a=a.copy();out=a.copy();h,w=a.shape
 for x in range(25,w):
  out[28:min(h,49),x]=0
  for y in range(28,min(h,49)):
   if a[y,x]:out[y+(phase if x>=27 else 0),x]=a[y,x]
 return out
for n in sorted(NEW_BODY):
 if n==144:a=cropped(P/'key_140.png');tx,ty=-16,-15;source='ice landing140'
 elif n==146:a=cropped(old/'frame_033.png');tx,ty=-19,-13;source='native crouch33'
 elif n==156:a=cropped(old/'frame_024.png');tx,ty=-19,-27;source='native apex24'
 elif n==158:a=cropped(old/'frame_027.png');tx,ty=-16,-27;source='native fall27'
 else:
  a=cape(key,{148:0,150:-1,152:0,154:1,156:0}[n]);tx,ty=-22,-37;source='new rising key at one scale'
 hp=head_loc(a);h,w=a.shape;_,bounds,safe=original(n)
 bad=int(np.count_nonzero((a!=0)&~safe[96+ty:96+ty+h,96+tx:96+tx+w]))
 if bad:raise ValueError(('Outside',n,bad))
 world=np.zeros((192,192),np.uint8);world[96+ty:96+ty+h,96+tx:96+tx+w]=a
 groups=component(world!=0)
 if len(groups)!=1:raise ValueError(('Disconnected',n,[len(g) for g in groups]))
 worlds[n]=world;placements[str(n)]=[tx+hp[0],ty+hp[1]]
 checks.append({'frame':n,'source':source,'head_world':placements[str(n)],'body_pixels':int(np.count_nonzero(a))-309,'outside':bad,'components':1,'foot_world':ty+h-1})
frames={};records={}
for k,r in recipe['frames'].items():
 src=P/r['file'];shutil.copyfile(src,D/src.name);records[k]=r;frames[int(k)]=read_indexed_png(src,pal)
for n,world in worlds.items():
 _,b,_=original(n);a=world[96+b[1]:96+b[3],96+b[0]:96+b[2]];p=D/f'bank1_{n:03d}.png';save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,p)
 records[str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};frames[n]=(a.tobytes(),(a.shape[1],a.shape[0]))
for n in sorted(EFFECTS):
 a,_,_=original(n);p=D/f'bank1_{n:03d}.png';save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,p)
 records[str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};frames[n]=(a.tobytes(),(a.shape[1],a.shape[0]))
preserved=set(recipe['preserved_effect_frames'])|EFFECTS
_,packing=patch_bank(gfx,parts,1,5,frames,preserved,clear_unreferenced=True)
recipe.update(scope=SCOPE,frames=records,preserved_effect_frames=sorted(preserved),rise_source_scale=.038,
 rise_generated_art='generated_rise_compact.png',rise_generated_art_sha256=sha256((D/'generated_rise_compact.png').read_bytes()),rise_parent_recipe_sha256=sha256((P/'recipe.json').read_bytes()))
recipe['body_standard']['head_world_positions'].update(placements);recipe['body_standard']['head_sizes'].update({n:[23,19] for n in placements})
for name in ('generated_wall.png','generated_spin.png','native_jump_edit_target.png','generated_keys.png'):
 shutil.copyfile(P/name,D/name)
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8')
np.savez(D/'final_worlds.npz',**{str(n):a for n,a in worlds.items()})
sheet=Image.new('RGBA',(4*288,2*320),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,a) in enumerate(worlds.items()):
 sheet.alpha_composite(rgba(a).crop((48,48,144,144)).resize((288,288),Image.Resampling.NEAREST),(i%4*288,i//4*320+22));dr.text((i%4*288+4,i//4*320+4),str(n)+' STATIC',fill='white')
sheet.save(D/'body_review.png');print(json.dumps({'new_body_references':len(worlds),'preserved_effects':len(preserved),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))
