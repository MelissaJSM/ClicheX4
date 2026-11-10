from pathlib import Path
import sys,json,shutil,struct
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import front,component,geometry,rgba,pal,gfx,parts
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import SHIPPUUGA_SCOPE,SHIPPUUGA_NEW,SHIPPUUGA_EFFECTS,SHIPPUUGA_VIEWS,patch_frames
from scripts.repack_zero import read_inputs
from src.psx_frame_edit import read_indexed_png
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
D=Path(__file__).parent;P=D.parent/'hurt_launch_v1';B=ROOT/'out/ver_buki_riko/riko_motion_20261025T090302549047Z';rec=json.loads((P/'motion_set.json').read_text());keys=np.load(D/'key_pixels.npz');regs={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())};bank=graphics_bank(gfx,0)
for r in rec['frames'].values():shutil.copyfile(P/r['file'],D/r['file'])
palette_info=rec['launch_production']['preview_palette'];shutil.copyfile(P/palette_info['file'],D/palette_info['file'])
worlds={};checks=[];placements={}
def put(w,a,x,y):
 h,wi=a.shape;w[96+y:96+y+h,96+x:96+x+wi]=a
for n in sorted(SHIPPUUGA_NEW):
 size,b,safe=geometry(n)
 if n==155:
  a=np.array(Image.open(B/'frame_046.png'));ys,xs=np.nonzero(a);a=a[ys.min():ys.max()+1,xs.min():xs.max()+1];hp=None
  for yy in range(a.shape[0]-18):
   for xx in range(a.shape[1]-22):
    if np.array_equal(a[yy:yy+19,xx:xx+23][front!=0],front[front!=0]):hp=[xx,yy]
  if hp is None:raise ValueError('Dash head not found')
  target_x=-24-hp[0];head_count=int(np.count_nonzero(front))
 else:
  key=158 if n<160 else 160 if n<164 else 168;r=regs[key];a=keys[str(key)].copy();hp=r['head_local'];target_x=r['position'][0];head_count=309 if n<160 else 319
  if n>=164:target_x={168:-11,170:-12,172:-13}.get(n,-12)
 h,wi=a.shape;options=[]
 for y in range(-32,5):
  for x in range(-40,6):
   bad=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+wi]));options.append((bad*100000+abs(y+h-24)*10+abs(x-target_x),bad,x,y))
 _,bad,x,y=min(options)
 if bad:raise ValueError(('Outside',n,bad,x,y))
 w=np.zeros((192,192),np.uint8);put(w,a,x,y);groups=component(w!=0)
 if len(groups)!=1:raise ValueError(('Detached',n,[len(g) for g in groups]))
 crop=w[96+b[1]:96+b[3],96+b[0]:96+b[2]];p=D/f'frame_{n:03d}.png';save_image(crop.tobytes(),size,pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};placements[str(n)]=[x+hp[0],y+hp[1]];worlds[n]=w;checks.append({'frame':n,'head_world':placements[str(n)],'view':SHIPPUUGA_VIEWS[str(n)],'outside':bad,'components':1,'floor_y':y+h-1,'body_pixels':int(np.count_nonzero(a))-head_count})
for n in SHIPPUUGA_EFFECTS:
 f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;data,size,_,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n));p=D/f'frame_{n:03d}.png';save_image(data,size,pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())}
rec.update(scope=SHIPPUUGA_SCOPE,preserved_effect_frames=sorted(set(rec['preserved_effect_frames'])|SHIPPUUGA_EFFECTS),shippuuga_head_views=SHIPPUUGA_VIEWS,shippuuga_source_scale=.10,shippuuga_source_art={n:sha256((D/n).read_bytes()) for n in ('generated_keys.png','generated_compact.png')},shippuuga_parent_motion_sha256=sha256((P/'motion_set.json').read_bytes()))
rec['body_standard']['head_world_positions'].update(placements)
if 'head_sizes' in rec['body_standard']:rec['body_standard']['head_sizes'].update({n:[23,19] for n in placements})
(D/'motion_set.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
sheet=Image.new('RGBA',(5*288,2*280),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,w) in enumerate(worlds.items()):
 sheet.alpha_composite(rgba(w).crop((48,48,144,132)).resize((288,252),Image.Resampling.NEAREST),(i%5*288,i//5*280+22));dr.text((i%5*288+4,i//5*280+4),str(n)+' STATIC',fill='white')
sheet.save(D/'body_review.png');print(json.dumps(checks))
