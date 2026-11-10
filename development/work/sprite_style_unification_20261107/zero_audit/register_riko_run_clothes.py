"""Register new clothing with the accepted head and native neck contact unchanged."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
OUT=D/'riko_cloth_inputs/run_registered_v3';OUT.mkdir(exist_ok=True)
source=D/'riko_restore/prepared_cloth_v1/PL01_U.ARC';arc=source.read_bytes();assert hashlib.sha256(arc).hexdigest()=='6ebb0239f27253bdd37b16c54b66a5b2044ba8191f41b8cc9f29cfbe15a440dc'
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35];green=np.isin(front,[4,8,14])
inv=json.loads((D/'shared_masters/inventory.json').read_text('utf8'));heads={r['id']:r for r in inv['riko']['head_masters'][0]['matches']};rows=[];targets={}
sources={}
for page in range(1,4):
 folder=ROOT/f'work/sprite_style_unification_20261107/riko/run_cloth{page:02d}'
 for p in (folder/'native').glob('*_indices.png'):sources[int(p.stem.split('_')[1])]=p
for n,p in sorted(sources.items()):
 old=render(arc,0,0,n)[0];authored=np.array(Image.open(p));body_dx=4 if n in(18,20)else 0
 if body_dx:authored=np.roll(authored,body_dx,axis=1)
 hx,hy=heads[f'b0_{n:03d}']['origin_world'];mask=np.zeros_like(old,bool);mask[160+hy:179+hy,160+hx:183+hx]=front>0;assert int(mask.sum())==309 and np.array_equal(old[mask],front[front>0])
 options=[]
 for dy in range(-6,7):
  for dx in range(-5,6):
   patch=authored[160+hy+dy:179+hy+dy,160+hx+dx:183+hx+dx];error=int(np.count_nonzero(patch[green]!=front[green]));extra=int(np.count_nonzero(np.isin(patch,[4,8,14])&~green));options.append((error+extra,abs(dx)+abs(dy),dx,dy,error,extra))
 score,_,dx,dy,error,extra=min(options);generated_head=np.roll(np.roll(mask,dy,axis=0),dx,axis=1);box=np.zeros_like(mask);box[160+hy+dy:179+hy+dy,160+hx+dx:183+hx+dx]=True;generated_head|=box&np.isin(authored,[4,8,14]);out=authored.copy();out[generated_head]=0;out[mask]=old[mask]
 seam=np.zeros_like(mask);seam[160+hy+17:160+hy+19+max(0,dy)+2,160+hx-2:160+hx+25]=True;restore=seam&(out==0)&(old>0)&~mask;out[restore]=old[restore]
 # Keep the accepted head's negative space too. This removes residual generated
 # hair edges outside its opaque mask without overwriting existing body paint.
 head_space=np.zeros_like(mask);head_space[160+hy-2:160+hy+19,160+hx-2:160+hx+25]=True
 negative=head_space&(old==0)&(out>0);out[negative]=0
 assert np.array_equal(out[mask],old[mask]);targets[n]=out;Image.fromarray(out).save(OUT/f'b0_{n:03d}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(OUT/f'b0_{n:03d}_protected_head.png')
 rows.append({'ref':n,'source_native':str(p.relative_to(ROOT)),'source_native_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_generated_sha256':hashlib.sha256((p.parent.parent/'generated.png').read_bytes()).hexdigest(),'body_registration_translation':[body_dx,0],'generated_head_offset_after_body_registration':[dx,dy],'green_match_error':error,'extra_green':extra,'head_preserved_pixels':309,'neck_existing_pixels_restored':int(restore.sum()),'head_negative_space_restored':int(negative.sum()),'head_exact':True,'target_sha256':hashlib.sha256((OUT/f'b0_{n:03d}_indices.png').read_bytes()).hexdigest(),'before_bounds':rgba(old,struct.unpack_from('<16H',entry(arc,9))).getbbox(),'after_bounds':rgba(out,struct.unpack_from('<16H',entry(arc,9))).getbbox()})
for label,row in(('normal',0),('black',13)):
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);ns=sorted(targets)
 for start in range(0,len(ns),4):
  subset=ns[start:start+4];sheet=Image.new('RGB',(1200,428*len(subset)),'#64717b');draw=ImageDraw.Draw(sheet)
  for iy,n in enumerate(subset):
   for ix,(title,a)in enumerate([('before',render(arc,0,0,n)[0]),('authored',np.array(Image.open(sources[n]))),('head and neck registered',targets[n])]):
    pic=rgba(a,pal).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+5,iy*428+5),f'{n} {title}',fill='white')
  sheet.save(OUT/f'{label}_comparison_{start//4:02d}.png')
(OUT/'registration.json').write_text(json.dumps({'source_arc':str(source.relative_to(ROOT)),'source_arc_sha256':hashlib.sha256(arc).hexdigest(),'frames':rows,'packed':False,'game_changed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
