from pathlib import Path
import sys,json,hashlib
from PIL import Image
W=Path(__file__).resolve().parent.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
D=Path(__file__).resolve().parent;p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(p.read_bytes())=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes())
target=Image.new('RGBA',(1536,1536));crop=(112,112,208,208)
for row,n in enumerate((225,227)):
 for col,mask in enumerate((8,15)):
  im=a.composite(n,mask)[0];assert im.getbbox()==im.getchannel('A').getbbox()
  target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*col,768*row))
out=D/'art02_inputs.png';assert not out.exists();target.save(out)
prompt='''Use case: identity-preserve.
Asset type: transparent console pixel-art sprite sheet refinement.
Image1 is the EDIT TARGET: exactly2 columns and2 rows, each cell a96x96 logical pixel square enlarged8x, cell origin(48,48). Keep the exact layout, sprite position, head size, eyes, wrist/hand anchors, shoulders/waist/knees and boot soles. Preserve poses in Image1. Do not auto-crop, recenter, stretch, enlarge heads, or add extra limbs. Image2 is the accepted detail reference: top idle and bottom airborne; it is not the target pose.
Both columns show the same lavender-haired fox-eared heroine floating with her torso nearly frontal, gaze turned LEFT. The two dark flight boots are folded close together below her, not a planted standing pose. Both columns keep the same boot design and exact foot/ankle coordinates for the original jet contact later. No flames, projectiles, gun, buster, labels, grid or cast shadow.
TOP ROW225: elbows bent to each side and both hands raised near the lower cheeks/shoulders. Keep these two hands, neither goes above the ears. BOTTOM ROW227: elbows/forearms lower, hands closer to her waist/sides; preserve these distinct lower hand coordinates. Keep the original knee/boot arrangement in each row.
LEFT: red ribbon beside the lavender ears, gold eye, white/light-lavender sleeves with controlled purple folds, red/white short shrine outfit, lavender braid and dark flight boots. RIGHT: same head/anatomy but small dark/gold head accessory, black/dark-purple sleeves and bodice, gold trim/buttons, restrained pale collar and accepted rear draped cloth. No red head ribbon or broad white sleeve on the right.
Refine the target's flat hair and clothes to the accepted idle's crisp separated lavender strands, ear interiors, one clear gold iris, cloth fold planes, cuff, waist and hem details. Consistent thin dark contour and2-3tone native clusters. Preserve short rounded proportions, don't make her tall or bulky. No blur, fuzzy antialiasing, hatching, glow or thick black halo. Keep the same transparent empty space and four complete sprites. True alpha-transparent background.'''
(D/'art02_prompt.txt').write_text(prompt,'utf8');(D/'art02_input_audit.json').write_text(json.dumps({'parent_sha256':sha(p.read_bytes()),'pose_order':[[225,8],[225,15],[227,8],[227,15]],'fixed_native_cell':96,'crop':list(crop),'output_sha256':sha(out.read_bytes()),'prompt_sha256':sha((D/'art02_prompt.txt').read_bytes()),'style_sha256':sha((D/'style_inputs_actual.png').read_bytes())},indent=2)+'\n','utf8');print(out)
