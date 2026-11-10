from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
src=W/'root_nana_arrival/packed_arrival01/PL00_U.ARC';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)=='9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91';a=Archive(src.read_bytes())
out=D/'inputs_a01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((204,205)):
  im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  ref=a.composite(0 if col==0 else 89,mask)[0];style.alpha_composite(ref.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox()})
prompt='''Edit the first image into a precise production sprite sheet for a PS1 Mega Man X4 character replacement. True transparent background. Four Nana sprites only in the same2x2 layout.
IMAGE1 IS THE POSE EDIT TARGET: left column204 is a planted victory transition, the front hand and tiny pistol bent inward across the chest, rear hand on waist. Right column205 raises the front bent forearm and hand beside the forehead, body slightly angled, rear hand on waist. Do not change the original choreography, head tilt, hand endpoints, elbow direction, pelvis, knee bends or wide planted foot positions. Preserve the tiny pink-and-black Sarang pistol where present; never add an arm cannon or a large weapon.
IMAGE2 IS STYLE AND COSTUME ONLY: its left column is the approved idle, right column the approved detailed raised-hand pose. Match the clean delicate dark contours, three-tone separated pink hair locks, small green eyes, facial shape, fitted fabric folds and small highlights. Do not copy the reference poses.
TOP ROW: black beret, fitted black blouse and short black skirt, asymmetric dark stockings, black boots. BOTTOM ROW: folded dark hood with a rear veil, dark dress with white decorative hem trim and burgundy shoes, exactly matching the bottom idle clothing. Restore the bottom row costume detail which was simplified in the old target, preserving the same anatomy as the top row.
Refine the existing blurry flat hair wedges, thick black sleeve blocks and indistinct skirt into crisp connected pixel clusters at the idle's level of detail. Maintain the original adult character proportions and same small head. No larger head, no chibi proportions, no thicker outlines, no rounded inflated torso, no new ornaments. Preserve sprite height and width rather than scaling to the pose's bounding box.
Keep the1536x1536 canvas, four768x768 equal cells, each depicting96x96 native pixels at8x nearest-neighbor pixel scale. Keep all cell padding and sprite positions. No recentering, cropping, rescaling, lighting effects, glow, text, labels, grids, backdrops or shadows.'''
target.save(out/'target.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8')
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','style.png','prompt.txt')],'runtime_verified':False},indent=2)+'\n','utf8');print('victory204/205 input prepared')
