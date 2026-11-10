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
from src.psx_ryuenjin import NEW_BODY,TURN_SCOPE,TURN_VIEWS
D=Path(__file__).parent;P=D.parent/'ryuenjin_v1';recipe=json.loads((P/'recipe.json').read_text());keys=np.load(D/'key_pixels.npz')
regs={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())};rear=np.array(Image.open(D.parent/'ladder_v1/rear_head_indexed.png'))
frames={};records={};worlds={};checks=[]
for k,r in recipe['frames'].items():
 src=P/r['file'];shutil.copyfile(src,D/src.name);records[k]=r;frames[int(k)]=read_indexed_png(src,pal)
def cape(a,phase):
 out=a.copy()
 for x in range(7):
  out[29:47,x]=0
  for y in range(29,47):
   if a[y,x]:out[y+(phase if x<4 else 0),x]=a[y,x]
 return out
for n in sorted(NEW_BODY):
 _,b,safe=original(n)
 if n in (144,158):
  a=np.array(Image.open(P/f'bank1_{n:03d}.png'));world=np.zeros((192,192),np.uint8);world[96+b[1]:96+b[3],96+b[0]:96+b[2]]=a
  worlds[n]=world;continue
 key=148 if n in (148,150,152,154) else n;r=regs[key];a=keys[str(key)].copy()
 if key==148:a=cape(a,{148:0,150:-1,152:0,154:1}[n])
 x,y=r['position'];h,w=a.shape;bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]))
 if bad:raise ValueError(('Outside',n,bad))
 world=np.zeros((192,192),np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a
 groups=component(world!=0)
 if len(groups)!=1:raise ValueError(('Detached body/cape',n,[len(g) for g in groups]))
 hp=r['head_local'];head=rear if key==148 else front
 if not np.array_equal(a[hp[1]:hp[1]+19,hp[0]:hp[0]+23][head!=0],head[head!=0]):raise ValueError('Head identity')
 picture=world[96+b[1]:96+b[3],96+b[0]:96+b[2]];p=D/f'bank1_{n:03d}.png';save_image(picture.tobytes(),(picture.shape[1],picture.shape[0]),pal,p)
 frames[n]=(picture.tobytes(),(picture.shape[1],picture.shape[0]));records[str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};worlds[n]=world
 recipe['body_standard']['head_world_positions'][str(n)]=[x+hp[0],y+hp[1]]
 checks.append({'frame':n,'view':TURN_VIEWS[str(n)],'head_world':[x+hp[0],y+hp[1]],'body_pixels':int(np.count_nonzero(a))-int(np.count_nonzero(head)),'outside':bad,'components':1,'foot_world':y+h-1})
preserved=recipe['preserved_effect_frames'];_,packing=patch_bank(gfx,parts,1,5,frames,preserved,clear_unreferenced=True)
recipe.update(scope=TURN_SCOPE,frames=records,rise_head_views=TURN_VIEWS,rise_rear_view_config_sha256=sha256((ROOT/'config/riko_ladder_head_views.json').read_bytes()),
 rise_source_scales={'turn_sheet':.074,'rear_key':.038},rise_generated_art='generated_rear.png',rise_generated_art_sha256=sha256((D/'generated_rear.png').read_bytes()),
 rise_parent_recipe_sha256=sha256((P/'recipe.json').read_bytes()),rise_v1_rejected='Front-facing uppercut omits Zero torso turn and rear-facing ascent')
recipe.pop('rise_source_scale',None)
for name in ('generated_wall.png','generated_spin.png','native_jump_edit_target.png','generated_keys.png'):
 shutil.copyfile(P/name,D/name)
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8')
np.savez(D/'final_worlds.npz',**{str(n):a for n,a in worlds.items()})
sheet=Image.new('RGBA',(4*288,2*320),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,a) in enumerate(worlds.items()):
 sheet.alpha_composite(rgba(a).crop((48,48,144,144)).resize((288,288),Image.Resampling.NEAREST),(i%4*288,i//4*320+22));dr.text((i%4*288+4,i//4*320+4),str(n)+' '+TURN_VIEWS[str(n)]+' STATIC',fill='white')
sheet.save(D/'body_review.png');print(json.dumps({'revised_body':len(checks),'preserved_effects':len(preserved),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))
