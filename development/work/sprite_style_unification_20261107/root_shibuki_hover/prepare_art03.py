from pathlib import Path
import sys,json,hashlib
from PIL import Image
W=Path(__file__).resolve().parent.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
D=Path(__file__).resolve().parent;p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(p.read_bytes())=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes())
target=Image.new('RGBA',(1536,768));style=Image.new('RGBA',target.size);crop=(112,112,208,208)
for col,mask in enumerate((8,15)):
    target.alpha_composite(a.composite(229,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*col,0))
    style.alpha_composite(a.composite(0,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*col,0))
for f in('art03_inputs.png','art03_style.png','art03_prompt.txt','art03_input_audit.json'):assert not(D/f).exists()
target.save(D/'art03_inputs.png');style.save(D/'art03_style.png')
prompt='''Use case: identity-preserve.
Asset type: transparent console pixel-art sprite refinement.
Image1 is the EDIT TARGET with exactly TWO sprite cells in one horizontal row. Each square cell is96x96 logical pixels enlarged8x, origin(48,48). Maintain the aspect ratio2:1 and the exact two96-pixel-square logical cells, positions, character size, head size, eye/hand/waist/ankle anchors. Keep all surrounding empty space. Do not enlarge the figures to fill the sheet. Image2 is the accepted idle DETAIL STYLE reference, not the target pose.
Both cells show the same lavender-haired fox-eared heroine in a front-three-quarter hover with gaze LEFT. BOTH arms are raised above/beside the head, each fist at its original Image1 coordinate. Do not drop an arm to the waist or add extra arms. Keep the exact tucked asymmetric knees and both distinct dark boots: the forward boot points downward in the original position; the rear bent boot's sole is at the original jet contact. No straight standing legs, flying flames, weapons, projectiles, shadows, grids or text.
LEFT has a red ribbon by the ears, white/light-lavender sleeves, red/white short shrine outfit, lavender braid, gold iris, and dark flight boots. RIGHT has the same face, hair and two dark boots but black/dark-purple sleeves and bodice, gold fasteners, small dark/gold head ornament, restrained pale collar and accepted rear draped cloth. Do not copy a red ribbon or large white sleeve onto the right.
Replace broad flat target hair with the accepted idle's clearly separated lavender strands and shaded ear interiors. Match the idle's crisp thin contour, coherent two-to-three-tone clusters, sleeve folds, waist/hem and boot detail density. Keep rounded short-limbed proportions and every native pose anchor. No thick black halo, random speckles, blur, glossy rendering or antialiasing. True alpha transparency. Exactly two complete sprites on the unchanged2:1 canvas.'''
(D/'art03_prompt.txt').write_text(prompt,'utf8');(D/'art03_input_audit.json').write_text(json.dumps({'parent_sha256':sha(p.read_bytes()),'pose_order':[[229,8],[229,15]],'fixed_native_cell':96,'crop':list(crop),'grid':[2,1],'files':{n:sha((D/n).read_bytes())for n in('art03_inputs.png','art03_style.png','art03_prompt.txt')}},indent=2)+'\n','utf8');print(D/'art03_inputs.png')
