from fit_ground import *
import shutil
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames,GROUND_SLASH_SCOPE

source=np.load(D/'key_worlds.npz');keys_world={int(n):source[n].copy() for n in source.files}
registrations={r['frame']:r for r in json.loads((D/'fit_registration.json').read_text('utf8'))}

def polygon(points):
 im=Image.new('L',(192,192));ImageDraw.Draw(im).polygon([(x+96,y+96) for x,y in points],fill=1);return np.array(im).astype(bool)

def composite_translate(world,mask,dx,dy):
 layer=np.where(mask,world,0).astype(np.uint8);body=np.where(mask,0,world).astype(np.uint8)
 layer=np.roll(np.roll(layer,dy,axis=0),dx,axis=1);layer[body!=0]=body[body!=0];return layer

# The generated recovery cape overhangs the original parts by1-2 pixels.
# Move the complete fabric layer inward; retain its tip and the body's size.
for n in (131,133):
 mask=polygon([(13,0),(18,1),(30,0),(30,18),(18,18),(13,9)])
 keys_world[n]=composite_translate(keys_world[n],mask,-2,0)
# Bring the intact glove/forearm toward the elbow without changing the head,
# torso or lower body. The original arm-part rectangle starts at world x=-16.
keys_world[131]=composite_translate(keys_world[131],polygon([(-22,-5),(-9,-5),(-9,1),(-22,1)]),4,0)
# Remove one residual outline pixel from the generated head outside the
# protected native head rectangle (old hair silhouette, not the new anatomy).
keys_world[133][96-13,96-8]=0
for n,w in keys_world.items():
 hx,hy=registrations[n]['head_world'];patch=w[96+hy:96+hy+19,96+hx:96+hx+23];patch[front!=0]=front[front!=0]
 groups=component(w!=0)
 for group in groups[1:]:
  if len(group)>2:raise ValueError(f'{n}: unexplained detached generated component')
  for y,x in group:w[y,x]=0

cape_masks={67:polygon([(-3,-2),(0,-7),(31,-7),(31,12),(15,12),(4,7)]),
            91:polygon([(10,-1),(16,0),(28,0),(28,18),(16,18),(12,9)]),
            111:polygon([(-1,-3),(0,-16),(30,-16),(30,10),(7,10),(0,4)])}
anchors={67:(-2,3),91:(13,4),111:(0,4)}
def cape_variant(base,angle):
 w=keys_world[base];mask=cape_masks[base].copy();hx,hy=registrations[base]['head_world']
 mask[hy+96:hy+96+19,hx+96:hx+96+23]&=front==0
 layer=np.where(mask,w,0).astype(np.uint8);body=np.where(mask,0,w).astype(np.uint8)
 x,y=anchors[base];rot=np.array(Image.fromarray(layer).rotate(angle,resample=Image.Resampling.NEAREST,center=(96+x,96+y),fillcolor=0))
 if base==67 and angle>0:rot=np.roll(rot,-1,axis=1)
 rot[body!=0]=body[body!=0];return rot

lunge_source=np.load(D/'lunge_worlds.npz');lunges={int(n):lunge_source[n].copy() for n in lunge_source.files}
lunge_records={r['frame']:r for r in json.loads((D/'lunge_registration.json').read_text('utf8'))}
for n,w in lunges.items():
 # Fold the complete generated rear skirt/jacket flap toward the hip. The
 # upright-cape frames have no tiles at x>=0,y=-8..7; body scale is unchanged.
 mask=polygon([(-5,-2),(10,-2),(10,7),(-5,7)])
 lunges[n]=composite_translate(w,mask,-6,0)
yy,xx=np.indices((192,192));wx,wy=xx-96,yy-96
common_body=((wx < -6)&(wy>=-20))|(wy>=8)|((wy>=-5)&(wx<0))
for n,w in lunges.items():
 w[common_body]=lunges[1][common_body]
 # Quantize the generated intermediate white into the existing white highlight;
 # retain the darker cloth shadow. Head/effect indices remain protected.
 w[w==12]=15
 hx,hy=lunge_records[n]['head_world'];patch=w[96+hy:96+hy+19,96+hx:96+hx+23];patch[front!=0]=front[front!=0]

worlds={};records=[]
first={67:0,69:10,71:20,73:10,75:0,77:-5,79:0,81:0}
second={91:0,93:0,95:5,97:5,99:0,101:0}
third={111:0,113:1,115:1,117:1,119:1,121:2,123:2,125:3,127:3}
for n in body_frames:
 base=n;angle=0;dx=0
 if n in first:base=67;angle=first[n]
 if n in second:base=91;angle=second[n];dx=1 if n in (93,95) else 0
 if n in third:base=111;angle=0;dx=-1 if n==113 else 0
 if n in (132,134):base=n-1
 w=cape_variant(base,angle) if base in cape_masks else keys_world[base].copy()
 if n in third:w=lunges[third[n]].copy()
 if dx:w=np.roll(w,dx,axis=1)
 hx,hy=(lunge_records[third[n]] if n in third else registrations[base])['head_world'];head=[hx+dx,hy]
 worlds[n]=w
 size,b,safe=geometry[n];bad=np.argwhere((w!=0)&~safe);groups=component(w!=0)
 records.append({'frame':n,'base_pose':base,'cape_rotation_degrees':angle,'body_translation':[dx,0],
                 'head_world':head,'size':size,'outside':len(bad),'outside_world':[[int(x-96),int(y-96)] for y,x in bad],
                 'components':[len(g) for g in groups],'opaque_pixels':int(np.count_nonzero(w)),
                 'foot_y':int(np.nonzero(w)[0].max()-96),'source_scale':.13 if n in third else registrations[base]['source_scale']})
review(worlds,records,D/'all_body_review.png')
(D/'final_registration_probe.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print(json.dumps([r for r in records if r['outside'] or len(r['components'])!=1]))
if any(r['outside'] or len(r['components'])!=1 for r in records):raise ValueError('Artwork coverage/attachment check failed')

previous=json.loads((ROOT/'work/ver_buki_riko/art_pilot/wall_v1/recipe.json').read_text('utf8'))
recipe={**previous,'scope':GROUND_SLASH_SCOPE,'frames':dict(previous['frames']),'preserved_effect_frames':effect_frames}
for r in previous['frames'].values():shutil.copyfile(ROOT/'work/ver_buki_riko/art_pilot/wall_v1'/r['file'],D/r['file'])
heads=dict(previous['body_standard']['head_world_positions']);frames={}
for n in range(61,135):
 f=bank['frames'][n];size,b,_=geometry[n]
 if n in worlds:
  w=worlds[n];data=w[96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes();r=next(r for r in records if r['frame']==n)
  hx,hy=r['head_world'];actual=w[96+hy:96+hy+19,96+hx:96+hx+23]
  if np.any(actual[front!=0]!=front[front!=0]):raise ValueError(f'{n}: head standard changed')
  heads[str(n)]=r['head_world']
 else:
  raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;data,size=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[:2]
 name=f'frame_{n:03}.png';save_image(data,size,words,D/name);frames[n]=(data,size)
 recipe['frames'][str(n)]={'file':name,'sha256':sha256((D/name).read_bytes())}
_,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['body_standard']={**previous['body_standard'],'head_world_positions':heads}
recipe['ground_slash_production']={'body_frames':body_frames,'preserved_effect_frames':effect_frames,'original_animation_ids':[88,89,90],
 'generated_sources':[{'file':name,'sha256':sha256((D/name).read_bytes()),'uniform_scale':scale} for name,scale in [('generated_keyposes_v1.png',.205),('generated_recovery_v2.png',.105),('generated_lunge_v3.png',.13)]],
 'normalization':'alpha220, largest connected component, nearest-neighbor global scale per source sheet, exact palette, approved23x19 head foreground',
 'cape_secondary_motion':'first/second generated fabric rotated about fixed shoulder anchors; third generated four cape variants with fixed head/feet registration',
 'recovery_compositing':'whole cape layer inward2px;131 glove/forearm inward4px;133 old-head residual pixel removed;third rear cloth flap inward6px behind body',
 'original_composition_timing_and_effects_preserved':True,'runtime_verified':False,'art_user_review_pending':True}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8')
(D/'art_checks.json').write_text(json.dumps({'frames':records,'compression':checks['compression'],'preserved_effect_frames':effect_frames,
 'anatomical_quality_automatically_proven':False},indent=2),encoding='utf8')
np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
print(json.dumps({'body_frames':len(body_frames),'effects_preserved':len(effect_frames),'compression':checks['compression']}))
