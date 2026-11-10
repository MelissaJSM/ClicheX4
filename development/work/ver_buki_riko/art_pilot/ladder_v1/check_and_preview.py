"""Audit the built ladder group and render explicitly offline previews."""
from fit_ladder import *
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import LADDER_BODY_FRAMES,LADDER_EFFECT_FRAMES,validate_sword_effect
from scripts.riko_master_sheet import load_model
from src.psx_frame_edit import read_indexed_png
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T063713991893Z'
OLD=ROOT/'out/ver_buki_riko/riko_motion_20261024T060039320512Z'
I=ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json'
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
def run():
 m=load_model(B,ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
 previous=json.loads((OLD/'manifest.json').read_text('utf8'));preserved=[]
 for n,r in previous['frame_inputs'].items():
  name=('idle' if int(n) in (0,1,2,146,147,148) else 'frame')+f'_{int(n):03d}.png'
  assert sha256((B/name).read_bytes())==r['sha256'];preserved.append(int(n))
 effect_checks=[]
 for n in sorted(LADDER_EFFECT_FRAMES):
  f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
  original,size=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[:2];data,_=read_indexed_png(B/f'frame_{n:03d}.png',pal)
  validate_sword_effect(original,data);bad=bytes([(data[0]+1)%16])+data[1:]
  try:validate_sword_effect(original,bad)
  except ValueError:pass
  else:raise AssertionError('Effect mutation accepted')
  effect_checks.append(n)
 inventory=json.loads(I.read_text('utf8'))
 write(D/'reference_roles.json',{'source_sha256':profile['source_sha256'],'inventory_sha256':sha256(I.read_bytes()),
  'body_frames':sorted(LADDER_BODY_FRAMES),'effect_frames':sorted(LADDER_EFFECT_FRAMES),
  'animations':[inventory['animations'][n] for n in (27,28,29,30,31,93,117)],
  'wall_saber_followup':{'animations':[inventory['animations'][n] for n in (94,118)],'graphics_bank':1,'parts_bank':5,'implementation_status':'not_written'},
  'meaning_evidence':{'path':'work/research/decomp/src/main/player_special.c','sha256':sha256((ROOT/'work/research/decomp/src/main/player_special.c').read_bytes()),'functions':['player_zero_check_ladder_slash','player_zero_ladder_slash','player_zero_check_wall_slash','player_zero_wall_slash'],'binary_function_equivalence_rechecked':False}})
 worlds={int(n):v for n,v in np.load(D/'final_worlds.npz').items()}
 connection_checks=[]
 for r in json.loads((D/'grip_registration.json').read_text()):
  if r['effect'] is None:continue
  en=r['effect'];f=bank['frames'][en];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
  data,size,b,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0,en));effect=np.zeros((192,192),np.uint8);effect[96+b[1]:96+b[3],96+b[0]:96+b[2]]=np.frombuffer(data,np.uint8).reshape(size[1],size[0])
  body=worlds[r['frame']];hx,hy=r['hand'];tx,ty=r['trail_nearest'];distance=math.hypot(tx-hx,ty-hy);holes=set()
  for d in np.arange(0,distance+.1,.2):
   x=round(hx+(tx-hx)*d/max(distance,.1));y=round(hy+(ty-hy)*d/max(distance,.1))
   if not body[96+y,96+x] and not effect[96+y,96+x]:holes.add((x,y))
  # Pixel-art diagonals are 8-connected. Restrict the check to a 1.5px strip
  # around the short connector, so a route through the torso cannot pass it.
  seen={(hx,hy)};pending=[(hx,hy)]
  while pending:
   x,y=pending.pop()
   for dx in (-1,0,1):
    for dy in (-1,0,1):
     q=(x+dx,y+dy)
     if q in seen:continue
     t=max(0,min(1,((q[0]-hx)*(tx-hx)+(q[1]-hy)*(ty-hy))/max(distance**2,.01)))
     if math.hypot(q[0]-hx-t*(tx-hx),q[1]-hy-t*(ty-hy))>1.5:continue
     if body[96+q[1],96+q[0]] or effect[96+q[1],96+q[0]]:seen.add(q);pending.append(q)
  assert (tx,ty) in seen,(r['frame'],holes)
  connection_checks.append({'frame':r['frame'],'eight_connected':True,'straight_sample_transparent_cells':sorted(holes)})
 def cell(n,mirror=False):
  im=rgba(worlds[n]);im=im.crop((48,48,144,144))
  if mirror:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  return im
 for aid,label in ((31,'climb'),(28,'exit'),(93,'slash')):
  sequence=inventory['animations'][aid]['sequence'];images=[];durations=[]
  for s in sequence:
   n=s['frame'];pic=Image.new('RGBA',(768,408),(32,36,48));draw=ImageDraw.Draw(pic)
   draw.text((10,8),f'OFFLINE PREVIEW | ANIM {aid} | FRAME {n} | ORIGINAL TICKS {s["duration_ticks"]}',fill='white')
   for j,mirror in enumerate((False,True)):pic.alpha_composite(cell(n,mirror).resize((384,384),Image.Resampling.NEAREST),(j*384,24))
   images.append(pic.convert('RGB'));durations.append(max(20,round(s['duration_ticks']*100/60)*10))
  images[0].save(D/f'{label}_offline.gif',save_all=True,append_images=images[1:],duration=durations,loop=0)
 write(D/'guard_checks.json',{'build':B.relative_to(ROOT).as_posix(),'bin_sha256':m['manifest']['modified_bin']['sha256'],
   'previous_pngs_identical':sorted(preserved),'new_body_count':32,'effects_identical_and_mutation_rejected':effect_checks,
   'full_master_loaded_and_validated':True,'static_grip_to_trail_connections':connection_checks,'new_motion_runtime_verified':False,'preview_tick_rate_assumption':60,
   'preview_gif_timing_is_quantized_not_game_timing':True,'generated_source_sha256':sha256((D/'generated_ladder.png').read_bytes())})
 print(json.dumps({'previous_pngs_preserved':len(preserved),'new_body':32,'effect_checks':effect_checks}))
if __name__=='__main__':run()
