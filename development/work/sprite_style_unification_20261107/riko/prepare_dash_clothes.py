"""대시 진입/정지까지 실제9 자세를 세 페이지로 준비한다."""
from pathlib import Path
import json,sys,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_wall_clothes_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='8f81bd702370d9ae4d47a50cd6c628a9513067caeacf8de5ccff809097f06c48'
D=W/'riko/dash_clothes11';D.mkdir(exist_ok=False);pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
for page,refs in enumerate([[44,45,46],[47,48,49],[50,51,52]],1):
    folder=D/f'page{page}';folder.mkdir();sheet=Image.new('RGBA',(2304,768));rows=[]
    for i,n in enumerate(refs):
        a=render(arc,0,0,n)[0];pic=rgba(a,pal);pic.save(folder/f'b0_{n:03}_source.png');sheet.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*i,0));rows.append(dict(bank=0,ref=n,cell=i))
    sheet.save(folder/'targets.png');style=Image.new('RGBA',(2304,768))
    for i,n in enumerate([147,33,39]):
        pic=rgba(render(arc,0,0,n)[0],pal);style.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*i,0))
    style.save(folder/'accepted_style.png')
    (folder/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,96],grid=[3,1],crop=crop,frames=rows),indent=2)+'\n','utf8')
    prompt='''Refine FIRST reference: exactly THREE existing Riko Mega Man X4 ground dash/transition sprites in one row. Transparent background. Native96x96 cells shown8x. Preserve each precise dynamic torso lean, elbow and knee bend, hand reach, foot/sole locations and head position; preserve the low horizontal dash pose, never elongate torso like a dachshund or enlarge into standing. SECOND reference is accepted idle and detailed landing/wall outfits, for quality only. Match their fine fitted white jacket collar/cuffs/seams, short pleated white skirt with clear gray planes, detailed white knee boots/gray heels and ankle bends, thin selective dark navy edge. Refine the plain white limbs into distinct fabric and boot planes without changing limb thickness/length or body scale. Original green bob hairstyle/eye/head silhouette stays at the same angle and size. Keep cyan-lined white cape attached to shoulder and its exact flow/silhouette for each first-reference pose; do not sever cloak from neck. Keep hands at same original coordinates, no long weapon. Do not change pose or repeat one pose in all cells. No text, wall, dust, new effects, scenery, outlines thickening, blur, antialias or smoother illustration. Native pixel craftsmanship consistent with accepted idle.'''
    (folder/'prompt.txt').write_text(prompt+'\n','utf8')
print(str(D))
