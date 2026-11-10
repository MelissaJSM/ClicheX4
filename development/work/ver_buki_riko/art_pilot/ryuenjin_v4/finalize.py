from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal,gfx,parts
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import front,component
from work.ver_buki_riko.art_pilot.sword_v1.inspect_sword import epal
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_frame_edit import read_indexed_png
from src.psx_bank_patch import patch_bank
from src.psx_ryuenjin import NEW_BODY,RISE_LOOP
D=Path(__file__).parent;P=D.parent/'ryuenjin_v2';rec=json.loads((P/'recipe.json').read_text());rear=np.array(Image.open(D.parent/'ladder_v1/rear_head_indexed.png'))
a=np.array(Image.open(D/'sampled_148.png'));b=np.array(Image.open(D/'sampled_156.png'))
mask=Image.new('1',(a.shape[1],a.shape[0]));ImageDraw.Draw(mask).polygon([(9,0),(28,0),(28,23),(23,27),(21,23),(22,19),(22,15),(19,12),(16,10),(12,8)],fill=1)
arm=a.copy();arm[~np.array(mask,dtype=bool)]=0;arm[np.isin(arm,[4,8,14])]=0
other=b.copy();other[:,:20]=0;other[25:]=0;other[np.isin(other,[4,8,14])]=0
glove=a[0:8,9:19].copy()
worlds={};checks=[]
def paste(world,patch,x,y):
 h,w=patch.shape;dst=world[96+y:96+y+h,96+x:96+x+w];dst[patch!=0]=patch[patch!=0]
for name in P.glob('*.png'):shutil.copyfile(name,D/name.name) if not (D/name.name).exists() else None
for n in sorted(NEW_BODY):
 old=np.array(Image.open(P/f'bank1_{n:03d}.png'));_,bounds,safe=original(n);w=np.zeros((192,192),np.uint8);w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]]=old;before=w.copy()
 yy,xx=np.indices(w.shape);xx-=96;yy-=96
 if n in RISE_LOOP:
  w[((xx>=2)&(yy<-19))|(yy<-29)]=0;paste(w,arm,-24,-40)
 elif n==156:
  w[(yy<-18)&(xx>=0)]=0;paste(w,other,-16,-38)
 elif n==158:
  w[(yy<-10)&(xx>=7)]=0;paste(w,other,-12,-31)
 elif n==144:paste(w,np.rot90(glove,2),-14,0)
 elif n==146:paste(w,np.rot90(glove,1),-28,6)
 hx,hy=rec['body_standard']['head_world_positions'][str(n)];head=rear if n in RISE_LOOP else front;paste(w,head,hx,hy)
 groups=component(w!=0)
 if any(len(c)>2 for c in groups[1:]):raise ValueError(('Detached',n,[len(c) for c in groups]))
 for c in groups[1:]:
  for y,x in c:w[y,x]=0
 bad=int(np.count_nonzero((w!=0)&~safe))
 if bad:raise ValueError(('Outside',n,bad,list(zip(xx[(w!=0)&~safe].tolist(),yy[(w!=0)&~safe].tolist()))))
 p=D/f'bank1_{n:03d}.png';out=w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]];save_image(out.tobytes(),(out.shape[1],out.shape[0]),pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};worlds[n]=w
 checks.append({'frame':n,'changed_pixels':int(np.count_nonzero(w!=before)),'body_pixels':int(np.count_nonzero(w))-int(np.count_nonzero(head)),'head_unchanged':bool(np.array_equal(w[96+hy:96+hy+19,96+hx:96+hx+23][head!=0],head[head!=0])),'lower_body_unchanged':bool(np.array_equal(w[96:],before[96:])) if n>=148 else None,'outside':bad,'components':len(component(w!=0))})
frames={int(k):read_indexed_png(D/v['file'],pal) for k,v in rec['frames'].items()};_,packing=patch_bank(gfx,parts,1,5,frames,rec['preserved_effect_frames'],clear_unreferenced=True)
rec.update(rise_parent_recipe_sha256=sha256((P/'recipe.json').read_bytes()),rise_arm_generated_art='generated_arms.png',rise_arm_generated_art_sha256=sha256((D/'generated_arms.png').read_bytes()),rise_arm_source_scale=.077,art_revision='rear_turn_preserved_hand_hilt_registered_to_original_fire_v4')
(D/'recipe.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
sheet=Image.new('RGBA',(8*192,3*240),(32,36,48));dr=ImageDraw.Draw(sheet)
for i,(n,w) in enumerate(worlds.items()):
 for j in range(3):
  cell=rgba(w);e,eb,_=original(n+1)
  if j>0:cell.alpha_composite(rgba(e,epal),(96+eb[0],96+eb[1]))
  if j==2:cell=cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  sheet.alpha_composite(cell.crop((48,24,144,136)).resize((192,224),Image.Resampling.NEAREST),(i*192,j*240+16));dr.text((i*192+2,j*240+2),str(n)+' '+('BODY','STATIC +FX','MIRROR +FX')[j],fill='white')
sheet.save(D/'alignment_after.png');print(json.dumps({'checks':checks,'min_margin':min(r['untouched_tail_bytes'] for r in packing['compression'])}))



