from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
src=W/'root_nana_arrival/packed_arrival01/PL00_U.ARC';a=Archive(src.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=D/'inputs_206_03';out.mkdir(exist_ok=False)
target=Image.new('RGBA',(1536,1536));frames=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 im=a.composite(206,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(0,row*768))
 style=Image.open(D/'registered_a01'/f'{form}_204_rgba.png');target.alpha_composite(style.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(768,row*768))
 frames.append({'cell':row*2,'form':form,'mask':mask,'ref':206,'bbox':im.getbbox()})
target.save(out/'target.png')
prompt='''Edit ONLY the LEFT column of this 2x2 transparent pixel sprite sheet. The RIGHT column is an already finished Nana game sprite, which must remain unchanged. Top row is the basic costume, bottom row Fourth costume.
Repaint the TWO LEFT sprites to the right column's exact delicate outline, hair strand texture, face size, fabric folds and proportions. Preserve every joint and pixel footprint of the LEFT target pose: tiny pink pistol held vertically beside the face, elbow bent down, hand gripping at cheek height, other hand at waist, planted feet. Preserve the existing left target face/eye position, shoulder, pelvis and bent knee positions. Do NOT lengthen the legs, enlarge the boots or head, lower the body, stand taller, or raise the pistol overhead. The left pose is206. The right pose204 has a different arm position; use its rendering quality and costume, never replace the left arm choreography with the right pose.
The upper-left basic sprite has a black beret, tailored black blouse/skirt, asymmetric dark stockings and boots. Lower-left uses the right-bottom reference's folded black hood, rear veil, dark dress with white trim and burgundy shoes. Keep both left sprites anatomically the SAME size and position. Keep the left original bottom pixel at native cell y70, head top at y27, eye at y35. The artwork lives on a96x96 native grid per cell; the full sheet is1536x1536, four768x768 cells at8x pixel scale. Use the entire fixed cell to register; never use a cropped body bounding box. Original blank margin, foot baseline and all sprite origins are invariant.
Four sprites remain in the sheet, but ONLY TWO LEFT sprites are edited; retain two right sprites. No text, grids, background, effects, extra ornaments, thick outline, chibi inflation or rescaling.'''
(out/'prompt.txt').write_text(prompt,'utf8');(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','prompt.txt')],'native_cell':[96,96],'runtime_verified':False},indent=2)+'\n','utf8');print('isolated206 inputs prepared')
