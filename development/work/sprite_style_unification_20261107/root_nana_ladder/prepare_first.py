"""Arrange actual RN18 ladder art and accepted style as immutable image inputs."""
from pathlib import Path
import json,sys,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
source=W/'nana_audit/hurt_repaint/packed_hurt_candidate_v1/PL00_U.ARC'
data=source.read_bytes();assert sha(data)=='978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f';arc=Archive(data)
out=D/'first_inputs01';out.mkdir(exist_ok=False)
target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
for row,(form,mask) in enumerate((('base',0),('fourth',15))):
 for col,ref in enumerate((143,146)):
  im,layers=arc.composite(ref,mask,2);target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  style_ref=0 if col==0 else 47;style.alpha_composite(arc.composite(style_ref,mask,2)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':ref,'rgba_sha256':sha(im.tobytes()),'bbox':im.getbbox(),'fixed_cell_world':[-48,-48,48,48]})
target.save(out/'targets.png');style.save(out/'style.png')
prompt='''Use case: style-transfer. Precisely registered pixel-art sprite sheet for a PS1 Mega Man X4 character replacement.
Image 1 is the EDIT TARGET: four full-body Nana ladder animation sprites in a fixed 2x2 grid. Top row is her accepted base outfit: small black beret, long pink hair, black tailored blouse and short skirt, asymmetrical dark stockings and dark boots. Bottom row is her accepted Fourth Armor outfit: black layered hood/veil over the same long pink hair, black tailored costume with white ornamental hem, bare thighs and dark/red shoes. Image 2 is STYLE ONLY: accepted idle at left and accepted airborne sprite at right in each costume row. Preserve those exact character identities and compact mature proportions; do not make her rounder or chibi.
Refine the FOUR target bodies to the accepted idle's crisp selective thin dark contour, separated pink hair locks with light/middle/dark planes, readable folds in black cloth, white trim and detailed boots. Existing ladder hair is a flat wide pink stripe: redraw its strand structure rather than leaving it flat. Distinguish the Fourth black veil folds from the pink hair underneath and keep its current length. Avoid thick blocky black limbs or muddy merged chest/sleeves. Keep the existing small face and eye placement. No extra accessories.
Preserve each target pose and all contact coordinates exactly: left column is ladder-grab transition143 with an arm extended diagonally up-left and bent knees; right column146 is rear-view climbing with a hand raised straight up, opposite arm bent to the side and one leg bent. Rear view must remain rear view, with no face painted onto the back of the head. Preserve the original full-body origin, head height, hand contacts, knees, foot tips, silhouette size, overlap order and empty spaces between limbs. Do not stretch, shorten, fatten or move the whole figure. Both rows are the same body proportions in different costumes, not different character designs.
Canvas 1536x1536, four768x768 cells representing96x96 native pixels each. Preserve each full cell's framing and exact figure placement. All four figures stay inside their original cells. Keep crisp native pixel clusters suited for about45-pixel-tall game figures, rendered enlarged with nearest-neighbor edges. More material detail without adding noisy speckles.
Output exactly FOUR figures with a true transparent background in the same2x2 layout. No labels, guides, grid lines, additional poses, weapons, ladders, aura, blood, shadows, scenery, bloom or antialias halos. This is a neutral game animation sprite sheet.'''
(out/'prompt.txt').write_text(prompt,'utf8')
manifest={'source_arc':source.relative_to(ROOT).as_posix(),'source_arc_sha256':sha(data),'frames':frames,'native_cell':[96,96],'render_scale':8,
 'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':sha((out/n).read_bytes())} for n in ('targets.png','style.png','prompt.txt')],
 'scope':'나나 기본/포스 사다리 첫143/146 원화 입력. 현자산 변경 없음.','native_packed':False,'runtime_verified':False}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8');print(out)
