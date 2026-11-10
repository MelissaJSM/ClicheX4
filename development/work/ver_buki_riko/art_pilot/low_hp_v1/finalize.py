"""Native low-HP assembly with common planted boots and shared-stream closure."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import geometry,front,component,rgba,pal,profile,arc,gmeta,gfx,parts
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames,LOW_HP_SCOPE
D=Path(__file__).parent
def run():
 src=np.load(D/'sample_worlds.npz');worlds={};heads={};records=[];frames={}
 base=src['149'].copy()
 high=np.roll(base,-1,axis=0);high[112:]=base[112:]
 low=src['152'].copy();low[110:]=base[110:]
 for n in range(149,155):
  w=(base if n in (149,150) else high if n==151 else low).copy();hy=-21 if n in (149,150) else -22 if n==151 else -20
  # Exact single head view, common planted boot soles, no waist-only displacement.
  protected=np.zeros_like(w,bool);protected[96+hy:96+hy+19,83:106]=front!=0
  w[(w==5)&~protected]=3;w[(w==13)&~protected]=11
  size,b,safe=geometry(n);bad=int(np.count_nonzero((w!=0)&~safe));groups=component(w!=0)
  if bad or len(groups)!=1:raise ValueError(f'{n}: coverage {bad}, components {[len(g) for g in groups]}')
  if not np.array_equal(w[96+hy:96+hy+19,83:106][front!=0],front[front!=0]):raise ValueError('Head changed')
  a=w[96+b[1]:96+b[3],96+b[0]:96+b[2]];save_image(a.tobytes(),size,pal,D/f'frame_{n:03d}.png');frames[n]=(a.tobytes(),size)
  worlds[str(n)]=w;heads[str(n)]=[-13,hy];records.append({'frame':n,'head_world':[-13,hy],'outside':bad,'components':1,'foot_rows_from':149,'foot_world_y_min':16 if n==151 else 14 if n>=152 else None})
 _,packing=patch_frames(arc,gmeta,gfx,parts,frames,(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
 previous=ROOT/'work/ver_buki_riko/scale_frames/20261024T063636725634Z/motion_set.json';recipe=json.loads(previous.read_text('utf8'))
 for r in recipe['frames'].values():shutil.copyfile(previous.parent/r['file'],D/r['file'])
 recipe['scope']=LOW_HP_SCOPE
 for n in range(149,155):recipe['frames'][str(n)]={'file':f'frame_{n:03d}.png','sha256':sha256((D/f'frame_{n:03d}.png').read_bytes())}
 recipe['body_standard']['head_world_positions'].update(heads)
 recipe['low_hp_production']={'frames':list(range(149,155)),'animation_id':6,'generated_art':'generated_low_hp.png','generated_art_sha256':sha256((D/'generated_low_hp.png').read_bytes()),
  'uniform_source_scale':.115,'body_keyframes':[149,151,152],'shared_aliases':[[149,150],[152,153,154]],'boots_planted':True,'upper_body_including_hips_moves_together':True,'runtime_verified':False,'art_user_review_pending':True}
 for name,r in [('motion_set.json',recipe),('packing_checks.json',packing),('art_checks.json',records)]: (D/name).write_text(json.dumps(r,indent=2)+'\n','utf8')
 np.savez(D/'final_worlds.npz',**worlds)
 board=Image.new('RGBA',(6*256,300),(32,36,48));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w).crop((64,52,128,122)).resize((256,280),Image.Resampling.NEAREST),(i*256,20));draw.text((i*256+4,3),n,fill='white')
 board.save(D/'body_review.png')
 seq=json.loads((ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json').read_text())['animations'][6]['sequence'];pics=[];dur=[]
 for s in seq:
  im=Image.new('RGBA',(64,70),(32,36,48));im.alpha_composite(rgba(worlds[str(s['frame'])]).crop((64,52,128,122)));pics.append(im.convert('RGB').resize((256,280),Image.Resampling.NEAREST));dur.append(round(s['duration_ticks']*1000/60))
 pics[0].save(D/'low_hp_offline.gif',save_all=True,append_images=pics[1:],duration=dur,loop=0)
 print(json.dumps({'body':len(frames),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))
if __name__=='__main__':run()
