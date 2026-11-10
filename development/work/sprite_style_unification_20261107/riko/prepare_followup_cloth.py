"""전수 시트에서 선별한 큰 단색 의상면3자세의 실제 원점 입력을 만든다."""
from pathlib import Path
import sys,json,hashlib,struct,argparse
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
parser=argparse.ArgumentParser();parser.add_argument('--saber-continuation',action='store_true');args=parser.parse_args()
W=ROOT/'work/sprite_style_unification_20261107';D=W/('riko/saber_continuation06' if args.saber_continuation else 'riko/followup_cloth05');D.mkdir(exist_ok=True)
assert not (D/'generated.png').exists(), 'Input already used for generation'
P=W/'riko/prepared_air_special_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='4e751c0e13d6f68bbb02f285493fee75c263c7cc995a96615332935c358e7615'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112 if args.saber_continuation else 128,208,192);cellheight=(crop[3]-crop[1])*8
sheet=Image.new('RGBA',(2304,cellheight));rows=[]
targets=[(0,113),(0,121),(0,125)]if args.saber_continuation else [(0,34),(0,111),(0,230)]
for i,(b,n)in enumerate(targets):
    a=render(arc,b,b*5,n)[0];im=rgba(a,pal);im.save(D/f'b{b}_{n:03}_source.png')
    sheet.paste(im.crop(crop).resize((768,cellheight),Image.Resampling.NEAREST),(i*768,0))
    rows.append(dict(bank=b,ref=n,cell=i,source_indices_sha256=sha(a.tobytes())))
sheet.save(D/'targets.png')
style=Image.new('RGBA',(2304,cellheight))
for i,(b,n)in enumerate([(0,147),(0,8),(0,213)]):
    a=render(arc,b,b*5,n)[0]
    if args.saber_continuation and i==1:
        import numpy as np
        a=np.array(Image.open(W/'riko/followup_cloth05/registered02/b0_111_indices.png'))
    style.paste(rgba(a,pal).crop(crop).resize((768,cellheight),Image.Resampling.NEAREST),(i*768,0))
style.save(D/'accepted_style.png')
(D/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),crop=crop,native_cell=[96,crop[3]-crop[1]],frames=rows),indent=2)+'\n','utf8')
prompt='''Edit ONLY the FIRST supplied image: three existing Riko player poses for PlayStation Mega Man X4. Output the exact same 3-column sheet, 2304x512 transparent canvas, each cell 768x512 representing 96x64 native pixels enlarged8x. SECOND image is accepted idle/run/new airborne STYLE reference. Keep FIRST image poses, head origins, face and green hair design, all hands/hilt contact coordinates, grounded feet coordinates, total head/body size, and original low attack stances EXACT. Redraw ONLY coarse garment and boot planes into the accepted detailed white outfit: small light-gray collar folds, cuff seams, waist details, segmented white skirt hem, cyan-lined cape, and elegant white boots with restrained gray shaping. The two attack poses must wear the SAME white outfit as idle; their turquoise torso/hip area must not turn into a new leotard. Refine the broad flat-white boot shapes without changing leg reach, knees, foot contact or making limbs thin. LEFT is the landing-to-idle bent stance. CENTER is the low third-saber attack with chest forward and legs spread, cape stretched backward. RIGHT is a wide ready-to-swing stance with the front hand extended left and the other hand tucked across the chest. Maintain stance and saber connection coordinates, no added sword blades. Keep cape physically attached. Native crisp pixel clusters, selective thin dark outlines, no black heavy contour, no blur, no shine or antialiasing. No enlarged chibi head, no shrunken waist, no thickened limbs, no facial redesign. Transparent background, no text or grid. Three complete fixed-origin poses; preserve their movement intention.'''
if args.saber_continuation:
    prompt='''Edit ONLY the FIRST image, a3-column sheet of Riko third-saber attack follow-through frames from PlayStation Mega Man X4. Same2304x512 transparent canvas, three768x512cells representing native96x64 pixels enlarged8x. SECOND image is the accepted detailed idle and newly refined matching first attack frame (middle), plus detailed airborne outfit. Preserve all FIRST image distinct cape angles (left vertical, middle swept right, right lower), head and face positions, and the exact low lunge/leg/feet/hand/hilt coordinates. Each frame has the identical body and outfit as the SECOND middle pose, with its own cape flutter phase. Redraw ONLY torso/collar/cuffs/white pleated skirt/boot shading to that accepted fine style, fine selective thin dark lines, narrow gray fabric folds, waist teal detail, white front skirt and layered sleeves. Keep original head/green hair and overall proportions, no head enlargement or narrow waist. The waist must stay a white outfit rather than exposed turquoise leotard. Do not lift the body or straighten knees. Retain thin saber connection/hilt at the forward fist, no sword blades. Crisp native pixel clusters, consistent scale and body weight. No blur, antialias, grids, text, shadows or extra effects. All3 complete poses remain at their original frame positions.'''
if args.saber_continuation:prompt=prompt.replace('2304x512','2304x640').replace('768x512','768x640').replace('96x64','96x80')
(D/'prompt.txt').write_text(prompt+'\n','utf8')
print(str(D))
