"""Fit the generated compact recoil once; derive sparks/flash from the shared body."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,geometry,rgba,pal,component,arc,gmeta,gfx,parts
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames,HURT_SCOPE
from src.psx_hurt import derive_hurt_frames
D=Path(__file__).parent

def run():
 a,hp=normalize(sample(Image.open(D/'generated_hurt_compact.png'),.05),front)
 hx,hy=-11,-24;x,y=hx-hp[0],hy-hp[1]
 w=np.zeros((192,192),np.uint8);w[96+y:96+y+a.shape[0],96+x:96+x+a.shape[1]]=a
 protected=np.zeros_like(w,bool);protected[96+hy:96+hy+19,96+hx:96+hx+23]=front!=0
 w[(w==5)&~protected]=3;w[(w==13)&~protected]=11
 size,b,safe=geometry(135);bad=int(np.count_nonzero((w!=0)&~safe));groups=component(w!=0)
 if bad or len(groups)!=1:raise ValueError(f'Coverage {bad}, components {[len(g) for g in groups]}')
 base=w[96+b[1]:96+b[3],96+b[0]:96+b[2]]
 frames=derive_hurt_frames(gfx,parts,(base.tobytes(),size))
 for n,(pixels,size) in frames.items():save_image(pixels,size,pal,D/f'frame_{n:03d}.png')
 _,packing=patch_frames(arc,gmeta,gfx,parts,frames,(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
 previous=ROOT/'work/ver_buki_riko/art_pilot/low_hp_v1/motion_set.json';recipe=json.loads(previous.read_text('utf8'))
 for r in recipe['frames'].values():shutil.copyfile(previous.parent/r['file'],D/r['file'])
 recipe['scope']=HURT_SCOPE
 for n in frames:
  recipe['frames'][str(n)]={'file':f'frame_{n:03d}.png','sha256':sha256((D/f'frame_{n:03d}.png').read_bytes())}
  recipe['body_standard']['head_world_positions'][str(n)]=[hx,hy]
 recipe['hurt_production']={'frames':sorted(frames),'animation_ids':[33,36,37],'partial_animation_ids':[34],
  'death_first_eight_ticks_reuses_animation':33,'generated_art':'generated_hurt_compact.png',
  'generated_art_sha256':sha256((D/'generated_hurt_compact.png').read_bytes()),'uniform_source_scale':.05,
  'body_keyframes':[135],'derived_effect_frames':[136,137,138], 'runtime_verified':False,'art_user_review_pending':True}
 for name,r in [('motion_set.json',recipe),('packing_checks.json',packing),('art_checks.json',{'outside':bad,'components':len(groups),'head_world':[hx,hy],'uniform_scale':.05})]:
  (D/name).write_text(json.dumps(r,indent=2)+'\n','utf8')
 board=Image.new('RGBA',(5*288,340),(32,36,48));dr=ImageDraw.Draw(board)
 for i,n in enumerate([147,135,138,136,137]):
  if n==147:
   im=Image.open(ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis/idle_147.png').convert('RGBA');bounds=(-24,-24,32,24)
  else:
   im=Image.open(D/f'frame_{n:03d}.png').convert('RGBA');bounds=geometry(n)[1]
  cell=Image.new('RGBA',(72,80));cell.alpha_composite(im,(36+bounds[0],40+bounds[1]));board.alpha_composite(cell.resize((288,320),Image.Resampling.NEAREST),(i*288,20));dr.text((i*288+5,3),str(n),fill='white')
 board.save(D/'body_review.png')
 print(json.dumps({'frames':len(frames),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))

if __name__=='__main__':run()
