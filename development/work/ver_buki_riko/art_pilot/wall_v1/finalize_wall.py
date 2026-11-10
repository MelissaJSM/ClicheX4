from fit_wall import *
import shutil
from PIL import ImageDraw
from scripts.discover_inputs import sha256
from scripts.project import write_json
from scripts.build_riko_idle import patch_frames

def save_evidence(path,document):
 if path.exists():
  if json.loads(path.read_text('utf8'))!=json.loads(json.dumps(document)):
   raise ValueError('Existing artwork evidence differs; use a versioned directory')
 else:write_json(path,document)

source=np.load(D/'worlds_probe.npz');worlds={int(n):source[n].copy() for n in source.files}
records=json.loads((D/'fit_registration.json').read_text('utf8'))
# Composite the complete generated cape one pixel left in35 to keep its tip
# inside the existing parts. No body scaling, clipped tip, or new drawn pixels.
mask=np.zeros((128,128),dtype=np.uint8)
im=Image.fromarray(mask);draw=ImageDraw.Draw(im)
draw.polygon([(64+7,64-13),(64+8,64-7),(64+8,64+1),(64+27,64+3),(64+27,64-13)],fill=1)
mask=np.array(im).astype(bool)
hx,hy=records[0]['head_world'];mask[64+hy:64+hy+19,64+hx:64+hx+23]&=front==0
layer=worlds[35].copy();layer[~mask]=0;body=worlds[35].copy();body[mask]=0
layer=np.roll(layer,-1,axis=1);joined=layer.copy();joined[body!=0]=body[body!=0];worlds[35]=joined

def cape_mask(points):
 im=Image.new('L',(128,128));ImageDraw.Draw(im).polygon([(x+64,y+64) for x,y in points],fill=1);return np.array(im).astype(bool)

mask39=cape_mask([(2,-7),(5,-4),(7,-2),(8,3),(9,7),(28,7),(28,-7)])
mask41=cape_mask([(0,-6),(2,-2),(3,2),(3,6),(8,10),(16,10),(16,-6)])
for n,base,mask in [(40,39,mask39),(42,41,mask41),(43,41,mask41)]:
 result=worlds[base].copy();result[mask]=worlds[n][mask];worlds[n]=result

previous=json.loads((ROOT/'work/ver_buki_riko/art_pilot/dash_cape_v5/recipe.json').read_text('utf8'))
recipe={**previous,'scope':'jump_run_dash_wall_v1','frames':dict(previous['frames'])}
old=ROOT/'work/ver_buki_riko/art_pilot/dash_cape_v5'
for r in previous['frames'].values():shutil.copyfile(old/r['file'],D/r['file'])
heads=dict(previous['body_standard']['head_world_positions']);frames={};checks=[]
for r in records:
 n=r['frame'];world=worlds[n];size,b,safe=geometry[n];bad=np.count_nonzero((world!=0)&~safe)
 if bad:raise ValueError(f'{n}: {bad} pixels outside original coverage')
 if len(component(world!=0))!=1:raise ValueError(f'{n}: detached component')
 x,y=r['head_world'];head=front if n<38 else np.array(Image.open(D/'rear_head_indexed.png'))
 # Only reference foreground is protected; the sprite may have arms behind it.
 actual=world[y+64:y+64+19,x+64:x+64+23]
 if np.any(actual[head!=0]!=head[head!=0]):raise ValueError(f'{n}: reference head changed')
 data=world[64+b[1]:64+b[3],64+b[0]:64+b[2]].tobytes();name=f'frame_{n:03}.png';save_image(data,size,words,D/name)
 frames[n]=(data,size);heads[str(n)]=r['head_world'];recipe['frames'][str(n)]={'file':name,'sha256':sha256((D/name).read_bytes())}
 checks.append({'frame':n,'outside_coverage':int(bad),'connected_components':1,'head_world':r['head_world'],'head_view':'front' if n<38 else 'wall_side','native_size':size,'opaque_pixels':int(np.count_nonzero(world))})
_,patch=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['body_standard']={**previous['body_standard'],'head_world_positions':heads}
view_config=ROOT/'config/riko_wall_head_view.json'
if view_config.exists():
 view=json.loads(view_config.read_text('utf8'))
 if view['reference_png_sha256']!=sha256((D/'rear_head_indexed.png').read_bytes()):raise ValueError('Wall head standard needs an explicit revision')
 recipe['body_standard']['wall_view_config_sha256']=sha256(view_config.read_bytes())
recipe['wall_production']={'source':'generated_wall_v3.png','generated_source_sha256':sha256((D/'generated_wall_v3.png').read_bytes()),'uniform_source_scale':.13,
 'new_frames':list(range(35,44)),'original_animation_ids':[13,14,15],'reused_jump_frames':[22,23],
 'existing_47_references_preserved':True,'art_user_review_pending':True,'runtime_verified':False,
 'cape_compositing':{'35':'complete generated cape translated left by1 native pixel','39_40':'common body39 with generated cape40','41_42_43':'common body41 with generated full cape42/43'},
 'source_normalization':'nearest-neighbor uniform scale, alpha threshold220, exact16-color palette, fixed per-view head foreground',
 'head_view_status':'Provisional side/three-quarter view, not user-approved'}
save_evidence(D/'recipe.json',recipe);save_evidence(D/'art_checks.json',{'frames':checks,'compression':patch['compression'],'full_anatomical_quality_automatically_proven':False})
np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
print(json.dumps({'frames':checks,'compression':patch['compression']}))
