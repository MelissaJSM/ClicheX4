"""Compose the ladder group using unchanged parts, fixed palette and saved artwork."""
from fit_ladder import *
import shutil
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames,LADDER_SCOPE,LADDER_BODY_FRAMES,KNOWN_SABER_EFFECT_FRAMES as SABER_EFFECT_FRAMES,LADDER_EFFECT_FRAMES
from src.psx_frame_edit import edit_frame_indices,read_indexed_png
D=Path(__file__).parent
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
def run():
 src=np.load(D/'key_worlds.npz');worlds={int(n):src[n].copy() for n in src.files}
 regs={r['frame']:r for r in json.loads((D/'fit_registration.json').read_text())};heads={n:r['head_world'] for n,r in regs.items()};views={n:r['head_view'] for n,r in regs.items()}
 # 191 raises the body onto the ledge and turns toward the side-on exit.
 worlds[191]=np.roll(worlds[192],-10,axis=0);heads[191]=[heads[192][0],heads[192][1]-10];views[191]='approved_front'
 for n,source in ((196,195),(201,199),(204,202),(206,202),(208,202),(210,202),(212,197)):
  worlds[n]=worlds[source].copy();heads[n]=list(heads[source]);views[n]=views[source]
 # Body keys in the shared climbing streams live solely in the base grid.
 # The original ponytail overlays are empty; no old Zero fragments survive.
 for key in (174,178,182,186):
  f=bank['frames'][key];c=composition_frame(parts,0,key);base={**c,'parts':c['parts'][:BASE_COUNTS[key]]}
  raw=bytes(f['tile_count']*128);_,size,b,_=compose_indices(raw,f['tile_count'],base)
  data=worlds[key][96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes()
  raw=edit_frame_indices(raw,f['tile_count'],base,data,size)
  for n in range(key,key+4):
   a,size,b,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n));w=np.zeros((192,192),np.uint8);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=np.frombuffer(a,np.uint8).reshape(size[1],size[0]);worlds[n]=w
   mirrored=composition_frame(parts,0,n)['parts'][0]['flip_x']!=base['parts'][0]['flip_x']
   heads[n]=[-heads[key][0]-23,heads[key][1]] if mirrored else list(heads[key]);views[n]='ladder_rear_mirrored' if mirrored else 'ladder_rear'
 # Tiny grip attachment follows the existing trail; no effect pixels change.
 grip=np.array(Image.open(D.parent/'sword_grip_v3/grip_native.png'))
 sys.path.insert(0,str(D.parent/'sword_grip_v3'))
 from assemble_grip import orient
 pairs={197:198,199:200,202:203,204:205,206:207,208:209,210:211}
 hands={195:(-12,-9),196:(-12,-9),197:(-15,-21),199:(-18,8),201:(-18,8),202:(-19,8),204:(-19,8),206:(-19,8),208:(-19,8),210:(-19,8),212:(-15,-21)}
 gripregs=[]
 for n,(hx,hy) in hands.items():
  target=None;angle=-115
  if n in pairs:
   en=pairs[n];ef=bank['frames'][en];raw=decode_stream(gfx,ef['offset'],ef['limit'],ef['tile_count']*128).data;a,s,b,_=compose_indices(raw,ef['tile_count'],composition_frame(parts,0,en));a=np.frombuffer(a,np.uint8).reshape(s[1],s[0]);yy,xx=np.nonzero(a);xx=xx+b[0];yy=yy+b[1];j=int(np.argmin((xx-hx)**2+(yy-hy)**2));target=[int(xx[j]),int(yy[j])];angle=math.degrees(math.atan2(target[1]-hy,target[0]-hx))
  w=worlds[n];safe=geometry(n)[2];layer=np.zeros_like(w);layer[96+hy-32:96+hy+32,96+hx-32:96+hx+32]=orient(grip,[2,6],angle)
  px,py=heads[n];protected=np.zeros_like(safe);protected[96+py:96+py+19,96+px:96+px+23]=front!=0
  glove=np.zeros_like(safe);glove[96+hy-2:96+hy+3,96+hx-2:96+hx+3]=True
  mask=(layer!=0)&safe&~protected&((w==0)|glove);w[mask]=layer[mask]
  if target:
   distance=math.hypot(target[0]-hx,target[1]-hy)
   if distance<=24:
    for d in np.arange(0,distance+.1,.2):
     x=round(hx+(target[0]-hx)*d/max(distance,.1));y=round(hy+(target[1]-hy)*d/max(distance,.1))
     if safe[96+y,96+x] and not protected[96+y,96+x] and not w[96+y,96+x]:w[96+y,96+x]=1 if d<5 else 10
  gripregs.append({'frame':n,'hand':[hx,hy],'effect':pairs.get(n),'trail_nearest':target,'angle':angle})
 # 201 reuses the left-hand/body column of 199 in the actual tile stream.
 worlds[201][:, :96-8]=worlds[199][:, :96-8]
 for n in (204,206,208,210):
  worlds[n][:,:96-8]=worlds[202][:,:96-8]
 # Two generated cape contours alternate only in the independent trailing area.
 for n in (201,204,208,210):
  worlds[n][96-6:96+24,96+9:]=worlds[199][96-6:96+24,96+9:]
 # These follow-through poses share the left column. One small common emitter
 # joins every original trail edge without changing the shared hand each tick.
 follow=(202,204,206,208,210);bridge=worlds[202].copy();safe=geometry(202)[2]
 for r in gripregs:
  if r['frame'] not in follow:continue
  hx,hy=r['hand'];tx,ty=r['trail_nearest'];distance=math.hypot(tx-hx,ty-hy)
  for d in np.arange(0,distance+.1,.2):
   x=round(hx+(tx-hx)*d/distance);y=round(hy+(ty-hy)*d/distance)
   if safe[96+y,96+x] and not bridge[96+y,96+x]:bridge[96+y,96+x]=10
 for n in follow:worlds[n][:,:96-8]=bridge[:,:96-8]
 old=D.parent/'sword_grip_v3';recipe=json.loads((old/'recipe.json').read_text('utf8'));new={**recipe,'scope':LADDER_SCOPE,'frames':dict(recipe['frames']),'preserved_effect_frames':sorted(SABER_EFFECT_FRAMES),'sword_effect_edits':{}}
 for r in recipe['frames'].values():shutil.copyfile(old/r['file'],D/r['file'])
 frames={};checks=[]
 for n in range(174,213):
  size,b,safe=geometry(n)
  if n in worlds:
   w=worlds[n];safe=geometry(n,True)[2] if n in BASE_COUNTS else safe;bad=int(np.count_nonzero((w!=0)&~safe));groups=component(w!=0)
   checks.append({'frame':n,'head_world':heads[n],'head_view':views[n],'outside':bad,'components':[len(g) for g in groups]})
   data=w[96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes()
  else:
   f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;data,size=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[:2]
  name=f'frame_{n:03d}.png';save_image(data,size,pal,D/name);new['frames'][str(n)]={'file':name,'sha256':sha256((D/name).read_bytes())};frames[n]=(data,size)
 review(dict(sorted(worlds.items())),D/'all_body_review.png');write(D/'art_checks.json',checks);write(D/'grip_registration.json',gripregs)
 if any(r['outside'] or len(r['components'])!=1 for r in checks):raise ValueError('Coverage or disconnected component')
 config={'base_standard_sha256':sha256((ROOT/'config/riko_body_standard.json').read_bytes()),'views':{},'assignments':{str(n):views[n] for n in range(174,191)},'new_art_user_review_pending':True}
 for name,p in [('ladder_rear',D/'rear_head_indexed.png'),('ladder_rear_mirrored',D/'rear_head_mirrored_indexed.png')]:
  data,size=read_indexed_png(p,pal);config['views'][name]={'reference_png':p.relative_to(ROOT).as_posix(),'reference_png_sha256':sha256(p.read_bytes()),'reference_indices_sha256':sha256(data),'size':list(size)}
 write(ROOT/'config/riko_ladder_head_views.json',config)
 new['body_standard']={**recipe['body_standard'],'ladder_view_config_sha256':sha256((ROOT/'config/riko_ladder_head_views.json').read_bytes()),'head_world_positions':{**recipe['body_standard']['head_world_positions'],**{str(n):h for n,h in heads.items()}}}
 new['ladder_production']={'body_frames':sorted(LADDER_BODY_FRAMES),'effects':sorted(LADDER_EFFECT_FRAMES),'generated_source_sha256':sha256((D/'generated_ladder.png').read_bytes()),'uniform_scale':.19,'original_animation_ids':[27,28,29,30,31,93,117],'base_layer_frames':sorted(BASE_COUNTS),'runtime_verified':False,'art_review_pending':True}
 write(D/'recipe.json',new);np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
 _,packing=patch_frames(arc,gmeta,gfx,parts,frames,struct.pack('<16H',*pal));write(D/'packing_checks.json',packing);print(json.dumps({'body':len(worlds),'compression':packing['compression']}))

if __name__=='__main__':run()
