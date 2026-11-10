from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((W/'staging_rn_v27.json').read_text('utf8'));src=ROOT/plan['resources']['PL00_U.ARC']['path'];assert sha(src)==plan['resources']['PL00_U.ARC']['after'];a=Archive(src.read_bytes())
out=D/'inputs_a01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((133,135)):
  im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  ref=a.composite(0 if col==0 else 138,mask)[0];style.alpha_composite(ref.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox()})
prompt='''Precisely repaint this 2x2 sheet of four Nana PS1 Mega Man X4 game sprites in place. True transparent background.
Image1 is the POSE EDIT TARGET. LEFT column133 is a low arrival crouch, front knee up, rear knee bent down, front hand holding a tiny pink-and-black pistol pointed down-left. RIGHT column135 is the following upright pose, front forearm raised inward by chest and face, pistol angled up-left, feet in a planted wide stance. Preserve all four poses, head size, face position, wrists, knees, foot endpoints, pixel scale and canvas cell coordinates. The crouch is intentionally lower; do not enlarge it to standing height.
Image2 is the approved STYLE AND CLOTHING REFERENCE. Left column idle, right column detailed raised-hand pose. Match their crisp restrained dark outline, green eye, separated three-tone long pink hair locks, fabric folds and small highlights. Do not use their pose. TOP row clothing is a black beret, tailored black blouse and skirt, asymmetric dark stockings and black boots. BOTTOM row is Fourth costume with a folded black hood and long rear veil, black dress, white decorative skirt trim and burgundy shoes. Reconstruct the bottom row in exactly that reference costume, maintaining identical anatomy and the target crouch/upright pose. The old target bottom row currently lacks those costume pieces; correcting that is intentional.
Refine flat hair wedges and indistinct broad black areas into readable layered hair and fitted fabric, to the same detail and outline weight as the idle reference. Keep the tiny Sarang pistol and recognizable grip; never replace it with a large arm cannon. Do not chibify, grow the head, stretch the arms, thicken the outlines or add new ornaments. Do not add glow, aura, lightning or transfer a weapon effect from the reference.
Keep exact1536x1536 layout, four768x768 cells, each representing96x96 native pixels enlarged8x. Preserve transparent padding and original cell positions. No bounding-box fit, recenter, crop, zoom, text, labels, grids, backgrounds or shadows. Four sprites only.'''
target.save(out/'target.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8')
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','style.png','prompt.txt')],'finding':'133/135 old armor layers5/6/7/8 are transparent; bottom costume in target is missing.','runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('arrival133/135 four inputs prepared')
