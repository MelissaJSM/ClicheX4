from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=W/'root_nana_special/packed_special02/PL00_U.ARC';assert sha(src)=='f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648';a=Archive(src.read_bytes())
out=D/'inputs01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((89,97)):
  im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));ref=a.composite(0 if col==0 else 98,mask)[0];style.alpha_composite(ref.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox(),'palette_start':16 if mask else 0})
prompt='''Use case: style-transfer. Refine four fully clothed Nana PS1 Mega Man X4 sprites in place, keeping their original poses and game-pixel size.
Image1 is the EDIT TARGET fixed 2x2 sheet. Top row: Nana's black beret, long pink hair, fitted black blouse and skirt, asymmetric black stockings, black boots. Bottom row: Nana's Fourth outfit, black folded hood and rear veil, long pink hair, fitted black dress with white ornamental hem, pale legs and burgundy shoes. Image2 is STYLE ONLY: accepted idle left, refined special firing right, same costume rows. Preserve costume identity; no pose transfer.
LEFT column frame89: standing wide stance, left-visible arm raised diagonally above her head, holding her small pink/black Sarang pistol pointed diagonally upward-left, other arm down by her side. RIGHT column frame97: preserve the standing windup with both hands close in front of the upper chest and face, the pistol held in the hand near the face, forearms bent across the chest. Keep the exact original muzzle, hand grip, wrists, elbow, shoulders, eye, hat, waist, knees, toes and foot baseline. Do not move or reorient either pose or the pistol, and do not enlarge the weapon. The two costumes must have identical underlying body proportion and hand/leg positions.
Repaint the flat pink hair and coarse sleeves to match the accepted idle's precise selective dark contour, readable layered pink hair locks with three-tone shading, black cloth folds, sleeve edges, skirt trim and crisp leg/boot outlines. Maintain native human proportions, small head, green eye and same silhouette. Do not add thick black borders, blurred gradients, chibi proportions, broad blank color blocks, ornaments or particle effects. Keep the dark veil attached with its original length; keep the raised hand clear of the hair.
Output transparent background, four complete sprites only in the unchanged 1536x1536 2x2 grid. Each768x768 cell represents96x96 native pixels enlarged8x. Retain all transparent padding and exact registration in each cell. No per-sprite bounding-box fit, recentering, crop, scaling, text, labels, grid, shadows or scenery.'''
target.save(out/'target.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8')
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','style.png','prompt.txt')],'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('prepared 4 registered costume cells')
