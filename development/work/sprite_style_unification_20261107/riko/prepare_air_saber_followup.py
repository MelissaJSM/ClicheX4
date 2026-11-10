"""공중 하강 베기92의 나머지8자세를 같은 의상 기준으로 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_followup_cloth_v1/PL01_U.ARC'
arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='105a7ba315a8dc0ef09d229770c4238fd8364adba43b483a5364c83f0ba79141'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,192)
style=Image.new('RGBA',(2304,640))
for i,q in enumerate([render(arc,0,0,147)[0],np.array(Image.open(W/'riko/followup_cloth05/registered03/b0_230_indices.png')),render(arc,0,0,213)[0]]):
    style.paste(rgba(q,pal).crop(crop).resize((768,640),Image.Resampling.NEAREST),(i*768,0))
for page,refs in enumerate([[232,234,236],[238,240,242],[244,246]],1):
    d=W/f'riko/air_saber_followup07/page{page}';d.mkdir(parents=True,exist_ok=False)
    sheet=Image.new('RGBA',(768*len(refs),640));rows=[]
    for i,n in enumerate(refs):
        a=render(arc,0,0,n)[0];pic=rgba(a,pal);pic.save(d/f'b0_{n:03}_source.png')
        sheet.paste(pic.crop(crop).resize((768,640),Image.Resampling.NEAREST),(i*768,0));rows.append(dict(bank=0,ref=n,cell=i,source_sha256=sha(a.tobytes())))
    sheet.save(d/'targets.png');style.save(d/'accepted_style.png')
    (d/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,80],crop=crop,frames=rows),indent=2)+'\n','utf8')
    prompt=f'''Edit ONLY the FIRST supplied sprite sheet, {len(refs)} existing airborne downward saber poses of Riko in PlayStation Mega Man X4. Keep exactly {len(refs)} columns, each768x640 cell representing96x80 native pixels at8x, transparent background. SECOND reference provides accepted idle(left), matching newly refined first pose of THIS attack sequence(middle), and airborne outfit(right). Follow the FIRST sheet's DIFFERENT torso turns, shoulders, elbows, hands, hand-held tiny saber hilt connection, facial/green hair position, knees, leg spread and boot coordinates. Redraw the coarse outfit as the SECOND middle sprite: detailed white jacket/collar/cuffs, white waist and short skirt with light-gray small pleat seams, cyan inside attached cape, white boots with restrained gray edge shaping. The torso and pelvis must not be a different turquoise leotard. Preserve the FIRST full-body size, all native joint and hand coordinates and airborne action; no scaling, no shrinking, no standing-idle substitution. Maintain accepted detailed green hairstyle and eye, selective thin outline, crisp native pixel clusters. Preserve the natural arm and torso rotation instead of copying one pose on all frames. No new sword blade, no extra effects, no text/grid, no blur or antialias. Keep all distinct cape silhouettes and shoulder attachments, boots and head same scale as reference.'''
    (d/'prompt.txt').write_text(prompt+'\n','utf8')
print('Prepared three pages: 232/234/236, 238/240/242, 244/246')
