from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=W/'root_nana_shot85/packed_shot01/PL00_U.ARC';assert sha(src)=='d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61';a=Archive(src.read_bytes())
out=D/'inputs01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[];rows=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((87,92)):
  im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  ref=a.composite(0 if col==0 else 85,mask)[0];style.alpha_composite(ref.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox(),'palette_start':16 if mask else 0});rows.append((f'{form} firing {n}',[('accepted idle',a.composite(0,mask)[0]),('existing pose',im),('refined raised shot',a.composite(89,mask)[0])]))
for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'existing_{i//2+1}.png',6)
prompt='''Use case: style transfer, registered game sprite refinement. Repaint FOUR fully clothed Nana gameplay sprites in Image1 to match the fine crisp PS1 Mega Man X4 pixel rendering in Image2. Image2 is style only, not pose transfer. Preserve the exact poses and all blank margins of Image1.
Top row: black beret, long layered pink hair, fitted black blouse/skirt, asymmetric dark stockings and black boots. Bottom row: folded black hood, short black rear veil, fitted black/burgundy dress with white hem, pale legs and small burgundy shoes. The same-column pair has identical face/body anatomy and joint locations; clothing alone differs. Preserve the original two distinct settling/ready poses87 and92. Both face left and are settling after firing. Preserve the exact original bent arms and hands, with the small pink/black Sarang pistol lowered beside the thigh when visible, never pointing horizontally or floating. Keep the wrist, forearm, elbow and shoulder connected and unmoved. Keep any visible pistol compact, no arm cannon, flash or bullet. Preserve eyes, hat, waist, knees, boot tips, leg spacing and the original floor row.
Replace coarse flat hair and featureless black cloth masses with the second sheet's three-tone hair locks, selective fine dark contours, tiny face highlights, clean sleeve folds, skirt-edge details and slender crisp legs. Do not enlarge the head or body, stretch legs, move the stance, flatten highlights, or use a uniform thick outline. Keep the hood/veil of the bottom row attached and short. The black hat and black veil remain distinct from the pink hair; no yellow speckles.
Transparent RGBA output with exactly four complete sprites in the original 2x2 cell layout,1536x1536 total,each768x768 cell=96x96 native pixels enlarged8x. Keep the exact target registration and transparent padding; no per-sprite bbox fitting, cropping, recentering or scale change. No labels, borders, grids, background, shadow, extra objects, particles or additional sprites.'''
target.save(out/'target.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8')
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','style.png','prompt.txt')],'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print('new basic/Fourth settling87/92 input prepared')
