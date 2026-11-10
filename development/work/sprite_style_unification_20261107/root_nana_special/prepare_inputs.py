from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=W/'root_nana_lowhp/packed_lowhp01/PL00_U.ARC';assert sha(source)=='ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16';a=Archive(source.read_bytes())
out=D/'inputs01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));rows=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((95,98)):
  im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  st=0 if col==0 else 106;style.alpha_composite(a.composite(st,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  rows.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox(),'palette_start':16 if mask else 0})
relations=[]
for n,other in((95,96),(98,99)):
 for pb in(0,5,6,7,8):
  assert np.array_equal(np.roll(a.layer(n,pb)[0],1,1),a.layer(other,pb)[0]);relations.append({'ref':other,'source':n,'part_bank':pb,'translation':[1,0],'all_index_pixels_exact':True})
target.save(out/'target.png');style.save(out/'style.png')
prompt='''Use case: style-transfer. Edit four registered, fully clothed PS1 Mega Man X4 game sprites of Nana, preserving the exact poses and coordinates.
Image 1 is the EDIT TARGET: a fixed 2x2 sheet. Top row is the accepted black beret outfit: long pink hair, fitted black blouse and black skirt, asymmetric dark stockings and boots. Bottom row is the accepted Fourth costume: black folded hood and rear veil over pink hair, black dress with white ornamental hem, pale legs and small burgundy shoes. Image 2 is STYLE ONLY, same costume rows: accepted idle left and a newly refined reaction right. Do not copy those poses.
LEFT column (frame95): preserve this suspended pose with slightly bent knees, both foot positions, shoulders, the small pink/black pistol held down and forward in her left-visible hand, and the other hand behind her. RIGHT column (frame98): preserve the wide grounded stance, forward extended firing arm and small pistol pointing horizontally left, other arm extended backward, chest orientation and hair sweep. The pistol is Sarang. Keep the original hand-to-gun contact, muzzle coordinate, weapon size, elbow/wrist and shoulder locations; do not omit the gun or add another weapon. Keep green eye, head and body proportions, belly/waist/hip, knee and ankle at exactly the current points. Upper and lower body must have the same original pose and scale in each costume.
Replace the flattened, coarse rendering with the accepted idle's crisp selective dark contour, clear pink hair locks with three-tone highlights, readable black-cloth folds and sleeve cuffs, skirt trim, stocking seams and precise shoe silhouette. Retain the small native game scale and human proportions; do not make a plump chibi, enlarge the head, thicken all outlines, smooth/blur the dots, or add speckles. The veil must remain connected and have the accepted length. Do not introduce idle pose, extra expression, sweat, effects, muzzle flashes, lettering, borders, scenery or decorative pixels.
Output true transparent background, four complete sprites only, 1536x1536 sheet: each of four768x768 cells represents96x96 game pixels enlarged8x. Preserve the entire transparent framing, exact sprite placement and common scale. No per-sprite recentering, bounding-box fit or cropping. Pixel clusters should read at the original roughly45–50px standing figure height, with no soft brush gradients, bloom or antialias halos.'''
(out/'prompt.txt').write_text(prompt,'utf8');(out/'manifest.json').write_text(json.dumps({'parent_arc':source.relative_to(ROOT).as_posix(),'parent_sha256':sha(source),'frames':rows,'aliases':relations,'native_cell':[96,96],'render_scale':8,'source_files':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':sha(out/n)}for n in('target.png','style.png','prompt.txt')],'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('prepared 4 cells, confirmed all 10 shifted layers')
