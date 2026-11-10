from fit_sword import *
from scripts.build_riko_idle import patch_frames,SABER_EFFECT_FRAMES
from src.psx_frame_edit import read_indexed_png
from src.psx_compress import replace_stream
from src.psx_frame_edit import edit_frame_set
master=np.array(Image.open(D/'sword_native.png'));pivot=json.loads((D/'sword_master.json').read_text('utf8'))['grip_pivot']
regs=json.loads((D/'registration.json').read_text('utf8'));worlds={};effects={};checks=[]
body_colors=np.array(rgba(np.arange(16,dtype=np.uint8).reshape(1,16)))[0,:,:3].astype(int)
effect_colors=np.array(rgba(np.arange(16,dtype=np.uint8).reshape(1,16),epal))[0,:,:3].astype(int)
mapping=np.argmin(((body_colors[:,None]-effect_colors[None,1:])**2).sum(2),1)+1;mapping[0]=0
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
for r in regs:
 n=r['frame'];a,b,safe=original(n);world=np.zeros((192,192),np.uint8);body=np.array(Image.open(old/recipe['frames'][str(n)]['file']));world[96+b[1]:96+b[3],96+b[0]:96+b[2]]=body
 allowed=np.zeros_like(world,bool);allowed[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe
 hx,hy=r['hand'];layer=np.zeros_like(world);layer[96+hy-48:96+hy+48,96+hx-48:96+hx+48]=orient(master,pivot,r['angle'])
 # Blade/guard can pass in front of clothes. The native identity head and the
 # closed glove remain foreground, so the hand wraps around the grip.
 mask=(layer!=0)&allowed;px,py=recipe['body_standard']['head_world_positions'][str(n)]
 mask[96+py:96+py+19,96+px:96+px+23]&=front==0
 glove=np.zeros_like(mask);glove[96+hy-1:96+hy+2,96+hx-1:96+hx+2]=True
 mask&=~(glove&(world!=0));result=world.copy();result[mask]=layer[mask]
 if n in (117,123,125,127):
  mask&=world==0;result=world.copy();result[mask]=layer[mask]
 remaining=np.where(~allowed,layer,0);e=r['effect'];added=0
 if np.any(remaining):
  assert e is not None
  ea,eb,esafe=original(e);ew=np.zeros_like(world);ew[96+eb[1]:96+eb[3],96+eb[0]:96+eb[2]]=ea
  ecov=np.zeros_like(mask);ecov[96+eb[1]:96+eb[3],96+eb[0]:96+eb[2]]=esafe
  assert not np.any((remaining!=0)&~ecov),f'outside effect {e}'
  add=(remaining!=0)&(ew==0);ew[add]=mapping[remaining[add]];added=int(add.sum())
  if e in effects:assert np.array_equal(effects[e],ew),'Shared effect conflict'
  effects[e]=ew
 attached=bool(world[96+hy,96+hx]!=0 and layer[96+hy,96+hx]!=0)
 assert attached,f'Grip detached {n}'
 worlds[n]=result;checks.append({**r,'added_effect_pixels':added,'weapon_pixels_in_body':int(mask.sum()),'grip_overlaps_original_glove':attached})
# 101 continues while weapon moves from 102 to 103, with identical hand pose.
if 102 in effects:
 a,b,safe=original(102);a2,b2,safe2=original(103);ow=np.zeros((192,192),np.uint8);ow[96+b[1]:96+b[3],96+b[0]:96+b[2]]=a
 extra=np.where(ow==0,effects[102],0);ew=np.zeros_like(ow);ew[96+b2[1]:96+b2[3],96+b2[0]:96+b2[2]]=a2;cv=np.zeros_like(ow,bool);cv[96+b2[1]:96+b2[3],96+b2[0]:96+b2[2]]=safe2
 assert not np.any((extra!=0)&~cv),'103 blade needs coverage';mask=(extra!=0)&(ew==0);ew[mask]=extra[mask];effects[103]=ew
new={**recipe,'frames':dict(recipe['frames']),'sword_effect_edits':{}}
for r in recipe['frames'].values():shutil.copyfile(old/r['file'],D/r['file'])
for n,world in {**worlds,**effects}.items():
 a,b,safe=original(n);data=world[96+b[1]:96+b[3],96+b[0]:96+b[2]].tobytes();name=f'frame_{n:03d}.png';save_image(data,(b[2]-b[0],b[3]-b[1]),pal,D/name)
 new['frames'][str(n)]={'file':name,'sha256':sha256((D/name).read_bytes())}
 if n in effects and data!=a.tobytes():new['sword_effect_edits'][str(n)]={'original_indices_sha256':sha256(a.tobytes()),'replacement_indices_sha256':sha256(data),'added_pixels':sum(x!=y for x,y in zip(a.tobytes(),data))}
new['preserved_effect_frames']=sorted(SABER_EFFECT_FRAMES-set(map(int,new['sword_effect_edits'])))
new['sword_production']={'source':'generated_sword.png','source_sha256':sha256((D/'generated_sword.png').read_bytes()),'master':'sword_native.png','master_sha256':sha256((D/'sword_native.png').read_bytes()),'registration':'registration.json','native_size':list(Image.open(D/'sword_native.png').size),'palette_rows_changed':[],'original_trail_opaque_pixels_preserved':True,'body_pose_geometry_unchanged':True,'art_review_pending':True}
(D/'recipe.json').write_text(json.dumps(new,indent=2),'utf8');(D/'attachment_checks.json').write_text(json.dumps(checks,indent=2),'utf8')
frames={int(n):read_indexed_png(D/r['file'],pal) for n,r in new['frames'].items()}
_,packing=patch_frames(arc,gmeta,gfx,parts,frames,struct.pack('<16H',*pal),new['sword_effect_edits'])
(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8')
review(worlds,D/'body_weapon_review.png');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
print(json.dumps({'bodies':len(worlds),'effects':len(new['sword_effect_edits']),'minimum_spare':min(p['original_bytes']-p['encoded_bytes'] for p in packing['compression'])}))
