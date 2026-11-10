from fit_air import *
import shutil
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from scripts.build_riko_idle import patch_frames,AIR_SLASH_SCOPE,SABER_EFFECT_FRAMES
from src.psx_player import compose_indices

source=np.load(D/'key_worlds.npz');worlds={int(n):source[n].copy() for n in source.files}
records={r['frame']:r for r in json.loads((D/'fit_registration.json').read_text('utf8'))}
yy,xx=np.indices((192,192));wx,wy=xx-96,yy-96
def move_layer(n,mask,dx,dy):
 w=worlds[n];hx,hy=records[n]['head_world'];mask=mask.copy()
 mask[96+hy:96+hy+19,96+hx:96+hx+23]&=front==0
 body=np.where(mask,0,w);layer=np.where(mask,w,0);layer=np.roll(np.roll(layer,dy,axis=0),dx,axis=1)
 layer[body!=0]=body[body!=0];worlds[n]=layer
# Fold whole generated fabric inward rather than clipping its moving tip.
# Keep the fixed native head foreground untouched in all layer operations.
for n in (221,225):
 move_layer(n,(wx>=5)&(wy>=-15)&(wy<7),-2,0)
 move_layer(n,(wx<-18)&(wy>=-8)&(wy<=2),3,0)
move_layer(238,(wx>=6)&(wy>=-8)&(wy<8),-2,0)
move_layer(238,(wx<-18)&(wy>=-8)&(wy<=2),3,0)
# Bring the complete trailing leg toward the hip without rescaling it.
move_layer(234,(wx>=1)&(wy>=0),-4,0)
# Two residual generated-head outline pixels outside the protected new head.
worlds[234][96-11:96-9,96-17]=0
# Last landing pose returns to an already approved ground-recovery guard.
old=ROOT/'work/ver_buki_riko/art_pilot/ground_slash_v2'
old_worlds=np.load(old/'final_worlds.npz');old_regs=json.loads((old/'final_registration_probe.json').read_text('utf8'))
worlds[246]=old_worlds['134'].copy();records[246]['head_world']=next(r for r in old_regs if r['frame']==134)['head_world'];records[246]['reused_approved_frame']=134
checks=[]
for n,w in worlds.items():
 hx,hy=records[n]['head_world'];patch=w[96+hy:96+hy+19,96+hx:96+hx+23]
 assert np.array_equal(patch[front!=0],front[front!=0]),f'head{n}'
 bad=np.argwhere((w!=0)&~geometry[n][2]);groups=component(w!=0)
 checks.append({**records[n],'outside':len(bad),'outside_world':[[int(x-96),int(y-96)] for y,x in bad],
                'components':[len(g) for g in groups],'foot_y':int(np.nonzero(w)[0].max()-96)})
review(worlds,D/'all_body_review.png');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print(json.dumps([r for r in checks if r['outside'] or len(r['components'])!=1]))
if any(r['outside'] or len(r['components'])!=1 for r in checks):raise ValueError('Coverage/attachment check failed')
previous=json.loads((old/'recipe.json').read_text('utf8'));recipe={**previous,'scope':AIR_SLASH_SCOPE,'frames':dict(previous['frames']),'preserved_effect_frames':sorted(SABER_EFFECT_FRAMES)}
for r in previous['frames'].values():shutil.copyfile(old/r['file'],D/r['file'])
heads=dict(previous['body_standard']['head_world_positions']);frames={}
for n in roles['shared_references']:
 f=bank['frames'][n];size,b,_=geometry[n]
 if n in worlds:
  w=worlds[n];data=w[96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes();heads[str(n)]=records[n]['head_world']
 else:
  raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;data,size=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[:2]
 name=f'frame_{n:03d}.png';save_image(data,size,words,D/name);frames[n]=(data,size);recipe['frames'][str(n)]={'file':name,'sha256':sha256((D/name).read_bytes())}
_,packing=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['body_standard']={**previous['body_standard'],'head_world_positions':heads}
recipe['air_slash_production']={'body_frames':roles['body_frames'],'effect_frames':roles['effect_frames'],'original_animation_ids':[91,92],
 'generated_sources':[{'file':n,'sha256':sha256((D/n).read_bytes()),'uniform_scale':s} for n,s in [('generated_air_v2.png',.16),('generated_landing_v3.png',.15)]],
 'normalization':'alpha220 largest component; uniform nearest per source; existing23x19 head; world registration; landing foot y23',
 'layer_adjustments':'221/225 cape inward2 and fist inward3;238 same;234 full trailing leg inward4 and two residual head-outline pixels removed;246 reuses approved134 recovery',
 'composition_timing_effects_preserved':True,'runtime_verified':False,'new_art_user_review_pending':True}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),encoding='utf8');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
print(json.dumps({'body':len(worlds),'compression':packing['compression']}))
