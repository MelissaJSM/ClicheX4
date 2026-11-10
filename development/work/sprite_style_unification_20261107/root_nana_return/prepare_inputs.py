from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
src=W/'root_nana_victory/packed_victory02/PL00_U.ARC';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)=='90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239'
a=Archive(src.read_bytes());out=D/'inputs01';out.mkdir(exist_ok=False)
im=Image.new('RGBA',(1536,1536));frames=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((156,204)):
  pic=a.composite(n,mask)[0];im.alpha_composite(pic.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  if col==0:frames.append({'cell':row*2,'form':form,'mask':mask,'ref':156,'bbox':pic.getbbox()})
im.save(out/'target.png')
prompt='''Edit only the TWO LEFT sprites of this 2x2 transparent pixel-art sheet. Preserve the TWO RIGHT sprites unchanged as finished style references. Top row basic Nana costume, bottom row Fourth costume. Each cell is a fixed96x96 game grid shown at8x, total1536x1536. Keep exact framing, blank margins, center origin and the old LEFT sprite joint positions.
The left pose is a full-body floating teleport-return pose, facing left, feet and knees close together, both forearms bent inward in front of the chest. Repaint its body to exactly the right sprite's delicate pixel outline, detailed pink hair strands, small face, fabric folds and slender normal game proportions. The top-left wears the right top reference's black beret, fitted black blouse and skirt, asymmetric dark stockings and boots. The bottom-left wears the right bottom reference's folded black hood, compact rear veil, black and burgundy dress with white trim, small burgundy shoes. Do not add or change weapons, effects or decorations. Keep left pose's bent knees and airborne feet positions; do not borrow the standing legs from the right. Head size, arm thickness, waist, boot size must match the right reference without inflating or smoothing the pixel clusters. Do not reposition the entire figure, stretch the legs, enlarge the head, or thicken every outer edge. Keep hair wind direction and the forearms in front of the torso. Add the same precise hair highlights and cloth shading in native pixel clusters.
Four cells total, only two left poses edited. Transparent background. No text, grid, panels, ground shadow, beam, glow, antialiased illustration or extra frames.'''
(out/'prompt.txt').write_text(prompt,'utf8');(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','prompt.txt')],'runtime_verified':False},indent=2)+'\n','utf8')
print('two return bodies, fixed cells prepared')
