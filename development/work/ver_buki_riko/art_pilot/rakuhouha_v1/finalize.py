from pathlib import Path
import sys,json,shutil,math
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal,gfx,parts
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import front,component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_frame_edit import read_indexed_png
from src.psx_bank_patch import patch_bank
from src.psx_rakuhouha import BODY,SCOPE
D=Path(__file__).parent;P=D.parent/'ryuenjin_v4';rec=json.loads((P/'recipe.json').read_text());keys=np.load(D/'key_pixels.npz');regs={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())};boxes=json.loads((D/'charge_boxes.json').read_text())
for f in P.glob('*.png'):
 if not (D/f.name).exists():shutil.copyfile(f,D/f.name)
worlds={};checks=[];charging={}
def put(w,a,x,y):
 h,wi=a.shape;dst=w[96+y:96+y+h,96+x:96+x+wi];dst[a!=0]=a[a!=0]
def cape(a,n):
 out=a.copy();phase={182:0,183:-1,184:0,185:1,186:2,187:4}[n]
 for y in range(12):
  for x in range(a.shape[1]):
   if a[y,x]:out[y,x]=0
 for y in range(12):
  for x in range(a.shape[1]):
   if a[y,x]:
    dx=round((12-y)*phase/12);dy=round((12-y)*max(0,phase-1)/12)
    out[y+dy,x+dx]=a[y,x]
 return out
for n in sorted(BODY):
 _,b,safe=original(n);w=np.zeros((192,192),np.uint8)
 if n==188:
  a=np.array(Image.open(P/'bank1_144.png'));ob=original(144)[1];put(w,a,ob[0],ob[1]);hp=rec['body_standard']['head_world_positions']['144']
 else:
  key=177 if n in (177,189) else 179 if n in (178,179,180) else 181 if n==181 else 182;r=regs[key];a=keys[str(key)].copy();x,y=r['position'];hp=r['head_world']
  if key==182:a=cape(a,n)
  put(w,a,x,y)
 body=w.copy();charge=np.zeros_like(w)
 if n in range(177,182):
  oa,ob,_=original(n);x0,y0,x1,y1=boxes[str(n)];fragment=oa[y0-ob[1]:y1-ob[1],x0-ob[0]:x1-ob[0]];converted=np.zeros_like(fragment)
  for src,dst in {1:10,2:2,3:6,8:15,9:12,10:7,11:1}.items():converted[fragment==src]=dst
  put(charge,converted,x0,y0);w[charge!=0]=charge[charge!=0];charging[str(n)]={'box':[x0,y0,x1,y1],'pixels':int(np.count_nonzero(charge)),'geometry_source':'original body-embedded aura; original red glove excluded','palette_mapping':{1:10,2:2,3:6,8:15,9:12,10:7,11:1}}
 # Head identity is authoritative where the body and embedded charge region overlap.
 put(w,front,*hp)
 bad=int(np.count_nonzero((w!=0)&~safe))
 if bad:raise ValueError(('Outside',n,bad))
 groups=component(body!=0)
 if len(groups)!=1:raise ValueError(('Detached body',n,[len(c) for c in groups]))
 if not np.array_equal(w[96+hp[1]:96+hp[1]+19,96+hp[0]:96+hp[0]+23][front!=0],front[front!=0]):raise ValueError('Head')
 picture=w[96+b[1]:96+b[3],96+b[0]:96+b[2]];p=D/f'bank1_{n:03d}.png';save_image(picture.tobytes(),(picture.shape[1],picture.shape[0]),pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};rec['body_standard']['head_world_positions'][str(n)]=hp;rec['body_standard']['head_sizes'][str(n)]=[23,19];worlds[n]=w
 checks.append({'frame':n,'head_world':hp,'body_pixels':int(np.count_nonzero(body))-int(np.count_nonzero(front)),'outside':bad,'body_components':1,'floor_y':int(np.nonzero(body)[0].max())-96})
frames={int(k):read_indexed_png(D/v['file'],pal) for k,v in rec['frames'].items()};_,packing=patch_bank(gfx,parts,1,5,frames,rec['preserved_effect_frames'],clear_unreferenced=True)
rec.update(scope=SCOPE,external_burst_effect={'weapon_id':36,'parts_bank':6,'modified':False},burst_generated_art='generated_keys.png',burst_generated_art_sha256=sha256((D/'generated_keys.png').read_bytes()),burst_floor_generated_art='generated_floor.png',burst_floor_generated_art_sha256=sha256((D/'generated_floor.png').read_bytes()),burst_source_scales={'sheet':.10,'floor':.038},burst_parent_recipe_sha256=sha256((P/'recipe.json').read_bytes()),burst_embedded_charge=charging,art_revision='rakuhouha_ground_strike_native_scale_v1')
(D/'recipe.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
sheet=Image.new('RGBA',(5*240,3*240),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,w) in enumerate(worlds.items()):sheet.alpha_composite(rgba(w).crop((56,32,136,104+32)).resize((240,312),Image.Resampling.NEAREST).crop((0,48,240,288)),(i%5*240,i//5*240+16));dr.text((i%5*240+3,i//5*240+3),str(n)+' STATIC',fill='white')
sheet.save(D/'body_review.png');print(json.dumps({'body':len(worlds),'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression']),'checks':checks}))
