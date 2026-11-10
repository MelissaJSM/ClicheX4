from pathlib import Path
import sys,json,shutil,math
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal,gfx,parts,epal
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import front,component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_frame_edit import read_indexed_png
from src.psx_bank_patch import patch_bank
from src.psx_player import graphics_bank,decode_stream,compose_indices,composition_frame
from src.psx_raijingeki import BODY,NEW_BODY,EFFECTS,THRUST,SCOPE
D=Path(__file__).parent;P=D.parent/'rakuhouha_v2';rec=json.loads((P/'recipe.json').read_text());keys=np.load(D/'key_pixels.npz');regs={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())}
for r in rec['frames'].values():shutil.copyfile(P/r['file'],D/r['file'])
for name in ('static_effects.json','effect_palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P/name,D/name)
worlds={};checks=[]
def effect(n):
 f=graphics_bank(gfx,1)['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 data,size,b,_=compose_indices(raw,f['tile_count'],composition_frame(parts,5,n));return np.frombuffer(data,np.uint8).reshape(size[1],size[0]),b
def put(w,a,x,y):
 h,wi=a.shape;dst=w[96+y:96+y+h,96+x:96+x+wi];dst[a!=0]=a[a!=0]
for n in sorted(NEW_BODY):
 _,b,safe=original(n);w=np.zeros((192,192),np.uint8)
 if n in (91,93):
  a=np.array(Image.open(P/'bank1_087.png'));ob=original(87)[1];put(w,a,ob[0],ob[1]);hp=rec['body_standard']['head_world_positions']['87']
 else:
  key=101 if n in (101,103) else 105 if n in (105,107) else 108 if n<128 else 128;r=regs[key];a=keys[str(key)].copy();x,y=r['position']
  if n in THRUST:x=-42 if n<128 else -41
  if n==103:x+=1
  if n==110:x-=1
  # Shift only the outer cape to retain the original flowing loop; shoulder stays fixed.
  phase={108:0,110:-1,112:0,114:1,116:0,119:-1,122:0,125:1}.get(n,0)
  if phase:
   old=a.copy();a[4:24,43:]=0
   for xx in range(43,a.shape[1]):
    dy=phase if xx>=49 else 0
    for yy in range(4,24):
     if old[yy,xx]:a[yy+dy,xx]=old[yy,xx]
  put(w,a,x,y);hp=[x+r['head_local'][0],y+r['head_local'][1]]
  if n in THRUST:
   end=-48 if n==110 else -47
   # Short blade root bridges only the gap to the existing lightning.
   for xx in range(end,-40):
    w[97,96+xx]=12;w[98,96+xx]=7
 bad=int(np.count_nonzero((w!=0)&~safe))
 if bad:raise ValueError(('Outside',n,bad))
 groups=component(w!=0)
 if len(groups)!=1:raise ValueError(('Detached',n,[len(c) for c in groups]))
 picture=w[96+b[1]:96+b[3],96+b[0]:96+b[2]];p=D/f'bank1_{n:03d}.png';save_image(picture.tobytes(),(picture.shape[1],picture.shape[0]),pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};rec['body_standard']['head_world_positions'][str(n)]=hp;rec['body_standard']['head_sizes'][str(n)]=[23,19];worlds[n]=w
 checks.append({'frame':n,'head_world':hp,'body_pixels':int(np.count_nonzero(w))-int(np.count_nonzero(front)),'outside':bad,'body_components':1,'floor_y':int(np.nonzero(w)[0].max())-96})
for n in sorted(EFFECTS):
 a,_=effect(n);p=D/f'bank1_{n:03d}.png';save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())}
preserved=set(rec['preserved_effect_frames'])|EFFECTS
frames={int(k):read_indexed_png(D/v['file'],pal) for k,v in rec['frames'].items()};_,packing=patch_bank(gfx,parts,1,5,frames,preserved,clear_unreferenced=True)
rec.update(scope=SCOPE,preserved_effect_frames=sorted(preserved),thrust_generated_art='generated_keys.png',thrust_generated_art_sha256=sha256((D/'generated_keys.png').read_bytes()),thrust_source_scale=.11,thrust_parent_recipe_sha256=sha256((P/'recipe.json').read_bytes()),external_thrust_effect={'weapon_id':32,'parts_bank':5,'modified':False},art_revision='raijingeki_forward_thrust_native_scale_v1')
(D/'recipe.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
pairs={91:92,93:94,101:102,103:104,105:106,108:109,110:111,112:113,114:115,116:117,119:120,122:123,125:126}
sheet=Image.new('RGBA',(4*420,5*240),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,w) in enumerate(worlds.items()):
 cell=rgba(w);e=pairs.get(n)
 if e:
  a,eb=effect(e);cell.alpha_composite(rgba(a,epal),(96+eb[0],96+eb[1]))
 sheet.alpha_composite(cell.crop((16,62,156,136)).resize((420,222),Image.Resampling.NEAREST),(i%4*420,i//4*240+18));dr.text((i%4*420+3,i//4*240+3),str(n)+' STATIC',fill='white')
sheet.save(D/'body_effect_review.png');print(json.dumps({'new_body':len(worlds),'preserved_effects':len(preserved),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression']),'checks':checks}))

