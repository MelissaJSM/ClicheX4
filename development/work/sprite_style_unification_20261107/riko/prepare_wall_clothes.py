"""벽동작의 네 실제 자세와 승인 대기 의상 세부표현을 편집 입력으로 준비한다."""
from pathlib import Path
import json,sys,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_vehicle_clothes_v2/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest();arc=P.read_bytes()
assert sha(arc)=='aedbb93bf5072fbb5ba98ddd4c149b745849ac87173e965a1a2a8d7717ef1512'
D=W/'riko/wall_clothes10';D.mkdir(exist_ok=False)
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208);sheet=Image.new('RGBA',(1536,1536));rows=[]
for i,n in enumerate([37,38,39,41]):
    a=render(arc,0,0,n)[0];pic=rgba(a,pal);pic.save(D/f'b0_{n:03}_source.png')
    sheet.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*(i%2),768*(i//2)))
    rows.append(dict(bank=0,ref=n,cell=i,source_sha256=sha(a.tobytes())))
sheet.save(D/'targets.png');style=Image.new('RGBA',(1536,1536))
for i,n in enumerate([147,24,33,213]):
    pic=rgba(render(arc,0,0,n)[0],pal);style.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*(i%2),768*(i//2)))
style.save(D/'accepted_style.png')
(D/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,96],grid=[2,2],crop=crop,frames=rows),indent=2)+'\n','utf8')
prompt='''Edit FIRST image: a 2 by 2 sprite grid of FOUR Riko wall climbing/jumping poses from Mega Man X4. Transparent background. Each cell is 96x96 native pixels shown at 8x. Keep EXACT pose, world placement, head angle, limb lengths, torso width, lifted glove tips, knee bend, ankle and boot sole locations. Do not move or scale figures in their cells. SECOND image is accepted detail/style only: idle and detailed airborne outfits. Match that same native pixel craft in the FIRST four poses: fine light-gray folded sleeves and cuffs, fitted white jacket collar and waist seams, small layered skirt hem, carefully shaped knee-high white boots with gray side planes, distinct cuff, ankle and heel. These wall poses currently have big empty white boot/sleeve masses: redraw their interior forms with the accepted idle quality, without thickening outlines or shrinking limbs. Preserve original green bob hair, purple eye, precise face and head shape, cyan-lined white cape flow and attachment. Keep the cape behind the figure, thin selective dark navy edge, no black holes at joints, no heavier/chibi body. No wall, props, weapons, text, borders, new costume, smearing, illustration antialias, shadows outside sprite. FOUR distinct poses in their original cells, not new poses. This is a native-resolution sprite detail refinement, not a pixel filter.'''
(D/'prompt.txt').write_text(prompt+'\n','utf8');print(str(D))
