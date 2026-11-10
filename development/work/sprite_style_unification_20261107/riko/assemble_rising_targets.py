"""Preserve proven original cape/grip variants of the five detailed keys."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).resolve().parent/'rising_clothes15';OUT=D/'targets01';OUT.mkdir(exist_ok=True);assert not any(OUT.iterdir())
P=D.parent/'prepared_movement_clothes_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='df73f6a50dc13c9b5c00b8cc60ab474e7b725011ea896f94712013f7fe411e7a'
keys={};register=[]
for page in(2,3,4):
 p=D/f'page{page}/registered01/registration.json';reg=json.loads(p.read_text('utf8'));assert reg['source_sha256']==sha(arc);register.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())})
 for r in reg['frames']:
  q=ROOT/r['target'];assert sha(q.read_bytes())==r['target_sha256'];keys[r['ref']]=np.array(Image.open(q))
assert set(keys)=={133,138,146,156,158}
old={n:render(arc,1,5,n)[0]for n in list(range(133,145))+[146,156,158]};rows=[]
contacts={133:[(148,149,157,166)],138:[(145,162,154,172)],146:[(130,164,143,176)],156:[(161,120,169,134)],158:[(165,128,175,143)]}
for n,a in keys.items():
 for x0,y0,x1,y1 in contacts[n]:a[y0:y1,x0:x1]=old[n][y0:y1,x0:x1]
 rows.append({'ref':n,'original_contact_rects':contacts[n],'old_body_copied':False})
targets={n:keys[n].copy()for n in[146,156,158]}
for n in range(133,138):
 mask=np.zeros((384,384),bool);mask[135:148,177:184]=True
 assert np.array_equal(old[n][~mask],old[133][~mask]),n
 q=keys[133].copy();q[mask]=old[n][mask];targets[n]=q
 rows.append({'ref':n,'master':133,'original_body_exact_outside_cape':True,'cape_rect':[177,135,184,148]})
for n in range(138,145):
 dx=0 if n==138 else -1 if n==144 else 1
 base=np.roll(old[138],dx,axis=1);q=np.roll(keys[138],dx,axis=1)
 mask=np.zeros((384,384),bool);mask[158:175,173+dx:184+dx]=True
 if n==144:mask[159:172,144:156]=True
 assert np.array_equal(old[n][~mask],base[~mask]),n
 q[mask]=old[n][mask];targets[n]=q
 rows.append({'ref':n,'master':138,'translation':[dx,0],'original_body_exact_outside_cape_hand':True,'cape_rect':[173+dx,158,184+dx,175],'original_hand_variant':n==144})
for n,a in targets.items():Image.fromarray(a).save(OUT/f'b1_{n:03}_indices.png')
for label,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(arc,9),row*32)
 for page,refs in enumerate([[133,135,137,138],[139,140,142,144],[146,156,158]]):
  sheet=Image.new('RGB',(1152,len(refs)*400),'#64717b');dr=ImageDraw.Draw(sheet)
  for i,n in enumerate(refs):
   for j,(name,a)in enumerate([('idle',render(arc,0,0,147)[0]),('old',old[n]),('candidate',targets[n])]):
    pic=rgba(a,pal).crop((112,104,208,200)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(j*384,i*400+16),pic);dr.text((j*384+4,i*400+3),f'{n} {name}',fill='white')
  sheet.save(OUT/f'{label}_comparison_{page:02}.png')
(OUT/'registration.json').write_text(json.dumps({'source_sha256':sha(arc),'source_registrations':register,'derivations':rows,'frames':[{'bank':1,'ref':n,'target':str((OUT/f'b1_{n:03}_indices.png').relative_to(ROOT)),'target_sha256':sha((OUT/f'b1_{n:03}_indices.png').read_bytes())}for n in sorted(targets)],'runtime_verified':False},indent=2),'utf8')
print({'targets':sorted(targets)})
