"""이동 루프에서 남은 의상과 부츠의 자세별 원화를 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_special_clothes_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='03fa9ef5b662a71963f1b4e2be5a00fb7f18202e834e33f595a2b6b672c1d6a3'
D=W/'riko/movement_clothes14';D.mkdir(exist_ok=False);pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
for page,refs in enumerate([[3,4],[7,9,10,11],[12,13,15,16],[17,18,19,20]],1):
    folder=D/f'page{page}';folder.mkdir();gx=2;gy=(len(refs)+1)//2;sheet=Image.new('RGBA',(1536,gy*768));rows=[]
    for i,n in enumerate(refs):
        pic=rgba(render(arc,0,0,n)[0],pal);pic.save(folder/f'b0_{n:03}_source.png');sheet.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*(i%gx),768*(i//gx)));rows.append(dict(bank=0,ref=n,cell=i))
    sheet.save(folder/'targets.png');style=Image.new('RGBA',(2304,768))
    for i,n in enumerate([147,8,14]):
        pic=rgba(render(arc,0,0,n)[0],pal);style.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(i*768,0))
    style.save(folder/'accepted_style.png');layout='TWO poses in ONE row'if len(refs)==2 else 'FOUR poses in TWO rows and TWO columns'
    prompt=f'''Refine FIRST reference: exactly {layout} of existing Riko Mega Man X4 running/transition sprites. Transparent background. Native96x96 cells shown8x. Preserve each distinct precise torso lean, shoulder and elbow rotation, stride, forward/backward knee bend, foot/sole positions and head position. No standing replacements, no repeating one pose, no body stretching, no changed leg proportions. SECOND reference shows accepted idle and two previously refined run frames for exact quality and scale. Match fine white fitted jacket collar/cuffs/seams, short white pleated skirt with clear gray planes, detailed white boots with gray ankles/heels and selective thin navy edges. Add coherent folds and segmented boot planes to the overly plain fabric surfaces while preserving limb silhouettes. Preserve existing detailed green bob, violet eye, face direction and hair silhouette. Keep the cyan-lined white cape firmly attached and its per-frame direction/motion as in first reference. Do not invent a long weapon or new decoration. Consistent native pixel craftsmanship, no blur, antialias, soft illustration, thickened outline, motion streak, text or background.'''
    (folder/'prompt.txt').write_text(prompt+'\n','utf8');(folder/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,96],grid=[gx,gy],crop=crop,frames=rows),indent=2)+'\n','utf8')
print(D)
