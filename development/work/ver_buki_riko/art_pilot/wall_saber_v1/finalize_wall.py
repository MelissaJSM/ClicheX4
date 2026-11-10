"""Shared-parts assembly of generated wall poses; preserve original effect pixels."""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import D,original,review,rgba,pal,epal,profile,gfx,parts,front,component
from scripts.build_riko_bank1 import WALL_BODY,WALL_EFFECTS
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_bank_patch import patch_bank

def run():
 keys=np.load(D/'key_worlds.npz');fit={r['frame']:r for r in json.loads((D/'fit_registration.json').read_text())}
 worlds={};heads={}
 for n in sorted(WALL_BODY):
  source=50 if n in (50,51,53) else 54 if n in (54,56) else 61
  w=keys[str(source)].copy();hx,hy=fit[source]['head_world'];dx=-4 if n in (51,53) else 0
  w=np.roll(w,dx,axis=1);hx+=dx
  protected=np.zeros_like(w,bool);protected[96+hy:96+hy+19,96+hx:96+hx+23]=front!=0
  # Collapse the generated purple fringe to the established navy shade;
  # retain the exact approved face and hair, including purple eye pixels.
  w[(w==5)&~protected]=3
  w[(w==13)&~protected]=11
  if source==61:
   if w[96-4,96+11]!=12 or protected[96-4,96+11]:raise ValueError('Unexpected shade cleanup source')
   w[96-4,96+11]=15
  if n in (54,56):
   for x,y in [(-23,-6),(-24,-5),(-24,-4),(-25,-3)]:
    if protected[96+y,96+x]:raise ValueError('Grip connector overlaps protected head')
    if not w[96+y,96+x]:w[96+y,96+x]=10
  _,b,safe=original(n)
  if np.any((w!=0)&~safe):raise ValueError(f'Artwork outside safe parts {n}')
  head=w[96+hy:96+hy+19,96+hx:96+hx+23];mask=front!=0
  if not np.array_equal(head[mask],front[mask]):raise ValueError(f'Head changed {n}')
  if len(component(w!=0))!=1:raise ValueError(f'Detached pixels {n}')
  worlds[n]=w;heads[str(n)]=[hx,hy]
 frames={};records={};checks=[]
 for n in sorted(WALL_BODY|WALL_EFFECTS):
  a,b,safe=original(n)
  if n in WALL_BODY:a=worlds[n][96+b[1]:96+b[3],96+b[0]:96+b[2]]
  save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,D/f'bank1_{n:03d}.png')
  frames[n]=(a.tobytes(),(a.shape[1],a.shape[0]));records[str(n)]={'file':f'bank1_{n:03d}.png','sha256':sha256((D/f'bank1_{n:03d}.png').read_bytes())}
 result,packing=patch_bank(gfx,parts,1,5,frames,WALL_EFFECTS,clear_unreferenced=True)
 for n,e in [(51,52),(53,52),(54,55),(56,55),(57,58),(59,60),(61,62),(63,64),(65,64)]:
  hand=(-13,-21) if n in (51,53) else (-22,-7) if n in (54,56) else (-22,1)
  a,b,_=original(e);ys,xs=np.nonzero(a);xs+=b[0];ys+=b[1];j=np.argmin((xs-hand[0])**2+(ys-hand[1])**2)
  checks.append({'body':n,'effect':e,'hand_registration':hand,'nearest_effect':[int(xs[j]),int(ys[j])],
                 'distance':float(np.hypot(xs[j]-hand[0],ys[j]-hand[1])),'static_origin_only':True})
 np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()});review(worlds,D/'effect_review.png')
 board=Image.new('RGBA',(5*240,2*290),(32,36,48));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w).crop((56,52,136,142)).resize((240,270),Image.Resampling.NEAREST),(i%5*240,i//5*290+20));draw.text((i%5*240+4,i//5*290+2),f'bank1 {n}',fill='white')
 board.save(D/'body_review.png')
 inv=json.loads((ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json').read_text())
 sequence=inv['animations'][94]['sequence'];pictures=[];durations=[]
 for s in sequence:
  n=s['frame'];w=worlds[n];cell=Image.new('RGBA',(96,96),(32,36,48));cell.alpha_composite(rgba(w).crop((48,48,144,144)));pictures.append(cell.convert('RGB').resize((384,384),Image.Resampling.NEAREST));durations.append(max(20,round(s['duration_ticks']*1000/60)))
 pictures[0].save(D/'wall_saber_offline.gif',save_all=True,append_images=pictures[1:],duration=durations,loop=0)
 recipe={'scope':'wall_saber_bank1_v1','graphics_bank':1,'parts_bank':5,'source_sha256':profile['source_sha256'],
  'original_graphics_sha256':sha256(gfx),'palette_sha256':sha256((ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes()),
  'frames':records,'preserved_effect_frames':sorted(WALL_EFFECTS),'body_standard':{
  'config_sha256':sha256((ROOT/'config/riko_body_standard.json').read_bytes()),'uniform_scale':.125,'per_pose_bbox_resize':False,
  'anisotropic_scale':False,'head_world_positions':heads},'generated_art':'generated_wall_compact.png',
  'generated_art_sha256':sha256((D/'generated_wall_compact.png').read_bytes()),'art_user_review_pending':True,'runtime_verified':False,
  'shared_variants_currently_repeat_body':[[51,53],[54,56],[57,59,61,63,65]],'long_blade_added':False}
 recipe['shade_cleanup']={'world':[11,-4],'from':12,'to':15,'frames':[57,59,61,63,65],'reason':'isolated gray pixel in white cluster; no silhouette/head changes'}
 recipe['short_connector']={'frames':[54,56],'world_path':[[-23,-6],[-24,-5],[-24,-4],[-25,-3]],'transparent_pixels_only':True,'original_effect_unchanged':True}
 for name,value in [('recipe.json',recipe),('packing_checks.json',packing),('grip_checks.json',checks),
                    ('art_checks.json',{'body_count':len(worlds),'all_connected':True,'all_head_pixels_identical':True,'all_inside_parts':True})]:
  (D/name).write_text(json.dumps(value,indent=2)+'\n','utf8')
 print(json.dumps({'body':len(worlds),'effects':len(WALL_EFFECTS),'minimum_budget_margin':min(r['untouched_tail_bytes'] for r in packing['compression']), 'grips':checks}))

if __name__=='__main__':run()
