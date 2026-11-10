"""Register one generated launch body; derive palette-aware effect frames."""
from pathlib import Path
import sys,json,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,geometry,rgba,pal,component,arc,gmeta,gfx,parts
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames,LAUNCH_SCOPE,check_motion_scale
from src.psx_hurt_launch import derive_launch,MULTI_FRAMES,compose_launch
from src.psx_player import graphics_bank,composition_frame,decode_stream
D=Path(__file__).parent

def run():
 scale=float(sys.argv[1]) if len(sys.argv)>1 else .047
 a,hp=normalize(sample(Image.open(D/'generated_launch.png'),scale),front)
 size,b,safe=geometry(139);options=[]
 for hx in range(-12,-3):
  for hy in range(-30,-18):
   x,y=hx-hp[0],hy-hp[1];h,w=a.shape;bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]));options.append((bad*1000+abs(hx+10)+abs(hy+28),bad,hx,hy,x,y))
 feasible=[];errors={}
 for option in sorted(options):
  if option[1]:continue
  _,_,_,_,tx,ty=option;test=np.zeros((192,192),np.uint8);test[96+ty:96+ty+a.shape[0],96+tx:96+tx+a.shape[1]]=a
  try:derive_launch(gfx,parts,(test[96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes(),size))
  except ValueError as exc:
   errors[str(exc)]=errors.get(str(exc),0)+1;continue
  feasible.append(option);break
 if not feasible:raise ValueError(f'No common placement fits all launch derivatives: {errors}; best {min(options)}')
 _,bad,hx,hy,x,y=feasible[0];world=np.zeros((192,192),np.uint8);world[96+y:96+y+a.shape[0],96+x:96+x+a.shape[1]]=a
 protected=np.zeros_like(world,bool);protected[96+hy:96+hy+19,96+hx:96+hx+23]=front!=0
 world[(world==5)&~protected]=3;world[(world==13)&~protected]=11
 save_image(world.tobytes(),(192,192),pal,D/'registration_candidate.png')
 groups=component(world!=0)
 if bad or len(groups)!=1:raise ValueError(f'Coverage {bad}, components {[len(g) for g in groups]}, head {hx,hy}')
 base=world[96+b[1]:96+b[3],96+b[0]:96+b[2]]
 frames,streams=derive_launch(gfx,parts,(base.tobytes(),size))
 v=ROOT/'work/ver_buki_riko/hurt_runtime/20261024T083240245441Z/vram_135.bin';video=v.read_bytes()
 palette=struct.pack('<16H',*pal)+video[480*2048+32:480*2048+128];words=struct.unpack('<64H',palette)
 (D/'preview_palette.bin').write_bytes(palette)
 for n,(pixels,sz) in frames.items():save_image(pixels,sz,words if n in MULTI_FRAMES else pal,D/f'frame_{n:03d}.png')
 previous=ROOT/'work/ver_buki_riko/art_pilot/hurt_v1/motion_set.json';recipe=json.loads(previous.read_text('utf8'))
 for r in recipe['frames'].values():shutil.copyfile(previous.parent/r['file'],D/r['file'])
 recipe['scope']=LAUNCH_SCOPE
 for n in frames:
  recipe['frames'][str(n)]={'file':f'frame_{n:03d}.png','sha256':sha256((D/f'frame_{n:03d}.png').read_bytes())}
  recipe['body_standard']['head_world_positions'][str(n)]=[hx,hy]
 recipe['launch_production']={'frames':sorted(frames),'animation_ids':[34],'generated_art':'generated_launch.png','generated_art_sha256':sha256((D/'generated_launch.png').read_bytes()),
  'uniform_source_scale':scale,'body_keyframes':[139],'derived_effect_frames':[140,141,142,143,144,145],'runtime_verified':False,'art_user_review_pending':True,
  'preview_palette':{'file':'preview_palette.bin','sha256':sha256(palette),'source_vram':str(v.relative_to(ROOT)),'source_vram_sha256':sha256(video),'clut2_preview_only_not_actual_launch_proof':True,'palette_rows_patched':[]}}
 (D/'motion_set.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8')
 _,packing=patch_frames(arc,gmeta,gfx,parts,frames,struct.pack('<16H',*pal))
 (D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8')
 (D/'art_checks.json').write_text(json.dumps({'outside':bad,'components':len(groups),'head_world':[hx,hy],'uniform_scale':scale},indent=2),'utf8')
 bank=graphics_bank(gfx,0);board=Image.new('RGBA',(8*288,340),(32,36,48));dr=ImageDraw.Draw(board)
 for i,n in enumerate([135,*frames]):
  im=Image.open(D/f'frame_{n:03d}.png').convert('RGBA');f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;bounds=compose_launch(raw,f['tile_count'],composition_frame(parts,0,n))[2]
  cell=Image.new('RGBA',(72,80));cell.alpha_composite(im,(36+bounds[0],40+bounds[1]));board.alpha_composite(cell.resize((288,320),Image.Resampling.NEAREST),(i*288,20));dr.text((i*288+5,3),str(n),fill='white')
 board.save(D/'body_review_palette_snapshot.png')
 print(json.dumps({'frames':len(frames),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression']),'head':[hx,hy]}))

if __name__=='__main__':run()
