"""전수검토에서 남은 점프·착지8형태를 대기/수정착지와 함께 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_air_saber_v1/PL01_U.ARC'
arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='7b79453e89d3a9600ee117630a510844a5738c31bf3e3e3d5b6ebac35b739328'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,192)
style=Image.new('RGBA',(2304,640))
for i,n in enumerate([147,34,213]):style.paste(rgba(render(arc,0,0,n)[0],pal).crop(crop).resize((768,640),Image.Resampling.NEAREST),(i*768,0))
for page,refs in enumerate([[21,22,24],[25,27,33],[35,36]],1):
    d=W/f'riko/jump_clothes08/page{page}';d.mkdir(parents=True,exist_ok=False);sheet=Image.new('RGBA',(768*len(refs),640));rows=[]
    for i,n in enumerate(refs):
        a=render(arc,0,0,n)[0];pic=rgba(a,pal);pic.save(d/f'b0_{n:03}_source.png');sheet.paste(pic.crop(crop).resize((768,640),Image.Resampling.NEAREST),(768*i,0));rows.append(dict(bank=0,ref=n,cell=i,source_sha256=sha(a.tobytes())))
    sheet.save(d/'targets.png');style.save(d/'accepted_style.png')
    (d/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,80],crop=crop,frames=rows),indent=2)+'\n','utf8')
    prompt=f'''Edit ONLY the FIRST supplied sprite sheet: {len(refs)} existing jump/landing poses of Riko, PlayStation Mega Man X4. Exactly {len(refs)} columns, each768x640 representing96x80 native pixels at8x. Transparent background. SECOND sheet shows the accepted idle, newly refined landing, and detailed airborne outfit. Keep the FIRST sheet's exact posture, body origin, green head/facial angle and size, shoulder/elbow/hand positions, bent knees, boot sole coordinates, distinct cape silhouette and flowing direction. These are separate moments of a jump and landing, not standing poses. Refine the existing coarse clothes and boots to the SECOND reference's delicate native pixel craft: crisp thin selective outline, white collar and fitted white jacket, short white waist/skirt pleats, light gray small cloth folds, matching white boot gray side planes/cuffs/heel. Keep cyan cape lining attached at shoulders, green detailed hair and ornament, purple eyes. Keep original first-reference body mass and limb lengths, clear joints and naturally bent knees. Avoid thick black edges, featureless white boot blocks, muddy texture, tiny skinny body, enlarged head, different face, blur. Do not replace pose with idle; do not scale or move body/feet within each cell. No weapons or effects added, no text/grid or background. Preserve readable whole-body silhouette and every cape boundary.'''
    (d/'prompt.txt').write_text(prompt+'\n','utf8')
print('prepared jump pages')
