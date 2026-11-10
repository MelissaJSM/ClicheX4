"""Assemble generated arms on one common wall body; preserve native shared parts."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,review,rgba,pal,profile,gfx,parts,component
from scripts.build_riko_bank1 import WALL_BODY,WALL_EFFECTS
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_bank_patch import patch_bank
D=Path(__file__).parent
def run():
 source=np.load(D/'sample_worlds.npz');base=source['54'].copy();rear=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/wall_v1/rear_head_indexed.png'))
 yy,xx=np.indices(base.shape);xx-=96;yy-=96
 protected=np.zeros_like(base,bool);protected[70:89,84:107]=rear!=0
 # One shoulder/torso/hip/knee/boot/cape drawing throughout the swing.
 # Only the free arm region comes from the other generated key poses.
 arm=(xx<-4)&(yy>=-25)&(yy<5)&~protected
 keys={}
 for n in (50,54,61):
  w=base.copy();w[arm]=source[str(n)][arm];keys[n]=w
 worlds={};heads={};frames={};records={};checks=[]
 for n in sorted(WALL_BODY):
  k=50 if n in (50,51,53) else 54 if n in (54,56) else 61
  w=keys[k].copy();hx,hy=-12,-26
  if n==50:
   layer=np.where(arm,w,0).astype(np.uint8);w[arm]=0;layer=np.roll(layer,3,axis=1)
   use=(layer!=0)&~protected;w[use]=layer[use]
  # Remove generated purple fringe while protecting the registered head.
  mask=np.zeros_like(w,bool);mask[96+hy:96+hy+19,96+hx:96+hx+23]=rear!=0
  w[(w==5)&~mask]=3;w[(w==13)&~mask]=11
  bad=int(np.count_nonzero((w!=0)&~original(n)[2]));groups=component(w!=0)
  if bad:raise ValueError(f'Coverage {n}: {bad}')
  if len(groups)!=1:raise ValueError(f'Detached {n}: {[len(c) for c in groups]}')
  if not np.array_equal(w[96+hy:96+hy+19,96+hx:96+hx+23][rear!=0],rear[rear!=0]):raise ValueError('Head changed')
  worlds[n]=w;heads[str(n)]=[hx,hy];checks.append({'frame':n,'head_world':[hx,hy],'outside':bad,'components':1})
 for n in sorted(WALL_BODY|WALL_EFFECTS):
  a,b,_=original(n)
  if n in worlds:a=worlds[n][96+b[1]:96+b[3],96+b[0]:96+b[2]]
  size=(a.shape[1],a.shape[0]);save_image(a.tobytes(),size,pal,D/f'bank1_{n:03d}.png');frames[n]=(a.tobytes(),size)
  records[str(n)]={'file':f'bank1_{n:03d}.png','sha256':sha256((D/f'bank1_{n:03d}.png').read_bytes())}
 _,packing=patch_bank(gfx,parts,1,5,frames,WALL_EFFECTS,clear_unreferenced=True)
 recipe={'scope':'wall_saber_bank1_v2','graphics_bank':1,'parts_bank':5,'source_sha256':profile['source_sha256'],
  'original_graphics_sha256':sha256(gfx),'palette_sha256':sha256((ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes()),
  'frames':records,'preserved_effect_frames':sorted(WALL_EFFECTS),'body_standard':{'config_sha256':sha256((ROOT/'config/riko_body_standard.json').read_bytes()),
  'wall_view_config_sha256':sha256((ROOT/'config/riko_wall_head_view.json').read_bytes()),'uniform_scale':.078,'per_pose_bbox_resize':False,'anisotropic_scale':False,'head_world_positions':heads},
  'generated_art':'generated_wall.png','generated_art_sha256':sha256((D/'generated_wall.png').read_bytes()),'shared_body_source_key':54,
  'long_blade_added':False,'art_user_review_pending':True,'runtime_verified':False}
 for name,r in [('recipe.json',recipe),('packing_checks.json',packing),('art_checks.json',checks)]: (D/name).write_text(json.dumps(r,indent=2)+'\n','utf8')
 np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()});review(worlds,D/'effect_review.png')
 board=Image.new('RGBA',(7*240,290),(32,36,48));draw=ImageDraw.Draw(board);old=np.load(ROOT/'work/ver_buki_riko/art_pilot/wall_v1/final_worlds.npz')
 shown={}
 for label in ['cling39','50','51','54','61','65','cling41']:
  if label.startswith('cling'):
   w=np.zeros((192,192),np.uint8);w[32:160,32:160]=old[label[5:]]
  else:w=worlds[int(label)]
  shown[label]=w
 for i,(label,w) in enumerate(shown.items()):
  board.alpha_composite(rgba(w).crop((56,52,136,142)).resize((240,270),Image.Resampling.NEAREST),(i*240,20));draw.text((i*240+4,3),label,fill='white')
 board.save(D/'transition_review.png')
 print(json.dumps({'body':len(worlds),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))
if __name__=='__main__':run()
