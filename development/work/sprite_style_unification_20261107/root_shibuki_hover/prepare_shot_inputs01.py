from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(D),str(ROOT)]
from prepare_body_layers01 import Archive,comp
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(P)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(P.read_bytes())
master_mask_path=W/'shibuki_audit/air_barrel_guard02/master_034_mask.png';mask=np.array(Image.open(master_mask_path))>0
master=np.where(mask,a.layer(34,0)[0],0).astype(np.uint8);assert int((master>0).sum())==60 and int(mask.sum())==71
out=D/'shot_inputs01';out.mkdir(exist_ok=False);Image.fromarray(master).save(out/'master_indices.png');Image.fromarray((mask*255).astype(np.uint8)).save(out/'master_mask.png')
muzzles={222:(-27,-9),224:(-29,-8),226:(-20,-10),228:(-17,-10),230:(-24,-11)};records=[]
for shot,(mx,my)in muzzles.items():
 layers={pb:np.array(Image.open(D/f'body_layers_probe03/layer{pb}_{shot-1:03}.png'))for pb in(0,5,6,7,8)}
 dx,dy=mx+24,my+10;gun=np.roll(master,(dy,dx),(0,1));guard=np.roll(mask,(dy,dx),(0,1));Image.fromarray(gun).save(out/f'{shot}_gun_indices.png');Image.fromarray((guard*255).astype(np.uint8)).save(out/f'{shot}_gun_guard.png')
 for form,m in(('base_legs',8),('fourth',15)):
  body=comp(a,layers,m);z=np.array(body);z[guard]=np.array(a.rgba(gun))[guard];Image.fromarray(z).save(out/f'{form}_{shot}_target.png');a.composite(shot,m)[0].save(out/f'{form}_{shot}_old.png')
 records.append({'ref':shot,'muzzle':[mx,my],'translation':[dx,dy],'opaque':60,'transparent_guard':11})
for page,refs in enumerate(((222,224),(226,228),(230,)),1):
 sub=out/f'page{page:02}';sub.mkdir();rows=len(refs);target=Image.new('RGBA',(1536,768*rows));old=target.copy();style=target.copy();crop=(112,112,208,208)
 for y,shot in enumerate(refs):
  for x,(form,m)in enumerate((('base_legs',8),('fourth',15))):
   for dst,im in((target,Image.open(out/f'{form}_{shot}_target.png')),(old,Image.open(out/f'{form}_{shot}_old.png')),(style,a.composite(34,m)[0])):dst.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*x,768*y))
 target.save(sub/'edit_target.png');old.save(sub/'original_shot_pose.png');style.save(sub/'accepted_shot_material.png')
 prompt=f'''Edit the FIRST image, a {'2 by 2' if rows==2 else 'single row of two'} game sprite sheet. Each cell is exactly96x96 native pixels enlarged8x, origin48,48. Left column is the red/white basic costume with shared hover boots; right column is the dark violet/gold Fourth costume with the same boots. Rows correspond to hovering shooting poses {','.join(map(str,refs))}. Keep the canvas layout, margins, character scale and position completely unchanged.
The first image contains the newly detailed body and a purple forearm cannon at the required original muzzle position. Replace ONLY the FRONT/VIEWER-LEFT arm so that it connects the shoulder to the rear/right end of that fixed cannon. Keep the cannon where it is, same size and direction. It is an arm cannon, not a separate pistol. The SECOND image shows the original firing pose and which arm is replaced. Keep the opposite arm exactly in the new pose; where the old front arm is raised, REMOVE it when adding the shooting arm. Exactly two arms, never a third fist. Restore any tiny uncovered hair behind the removed arm in the same fine pixel style.
The THIRD image is the accepted shooting sleeve and cannon material reference. LEFT column has light white/blue sleeves with red cuff accents. RIGHT column has dark navy/violet sleeves with small gold cuff accents: do not copy a white sleeve to the right. Preserve the separate small white collar on the right. Make a natural elbow bend to reach the fixed muzzle without making an excessively long arm. Join shoulder, sleeve, wrist and cannon with an unbroken thin contour.
Preserve every other part of image1: detailed lavender hair and ears, gold eyes, face, braid, torso, trim, waist, folded legs and shoes. Keep the legs pixel-identical in shape and placement, do not change the foot height or body size. Do not simplify the detail to large flat blobs or thicken outlines. No projectile, muzzle flash, flames, jets, effects, labels, grid or background. Output the same full transparent sheet with just the correct front shooting arms connected to the fixed cannons.'''
 (sub/'prompt.txt').write_text(prompt,'utf8');(sub/'input.json').write_text(json.dumps({'refs':refs,'rows':rows,'columns':2,'native_cell':96,'origin':[48,48],'parent_sha256':sha(P),'body_source':'body_layers_probe03','files':{p.name:sha(p)for p in sub.iterdir()if p.is_file()}},ensure_ascii=False,indent=2)+'\n','utf8')
(out/'manifest.json').write_text(json.dumps({'parent_sha256':sha(P),'master_mask_path':master_mask_path.relative_to(ROOT).as_posix(),'master_mask_sha256':sha(master_mask_path),'frames':records,'native_packed':False},indent=2)+'\n','utf8');print('3 pages / 10 outfit cells, exact 60+11 cannon from current34')
