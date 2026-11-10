"""Prepare exact rising-move poses; the existing rotating rear views remain locked."""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_movement_clothes_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='df73f6a50dc13c9b5c00b8cc60ab474e7b725011ea896f94712013f7fe411e7a'
D=W/'riko/rising_clothes15';D.mkdir(exist_ok=False);pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,104,208,200)
for page,refs in enumerate([[133,138,146,158],[156,148,150,152]],1):
    folder=D/f'page{page}';folder.mkdir();sheet=Image.new('RGBA',(1536,1536));rows=[]
    for i,n in enumerate(refs):
        pic=rgba(render(arc,1,5,n)[0],pal);pic.save(folder/f'b1_{n:03}_source.png');sheet.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(768*(i%2),768*(i//2)));rows.append(dict(bank=1,ref=n,cell=i))
    sheet.save(folder/'targets.png');style=Image.new('RGBA',(2304,768))
    for i,(b,n)in enumerate([(0,147),(1,50),(1,148)]):
        pic=rgba(render(arc,b,b*5,n)[0],pal);style.paste(pic.crop(crop).resize((768,768),Image.Resampling.NEAREST),(i*768,0))
    style.save(folder/'accepted_style.png')
    prompt='''Refine the FIRST reference game sprite sheet, exactly FOUR cells in a two-by-two grid, native96x96 cells shown8x. Keep original exact body size, head and hand positions, bent knees, soles, and each distinct view/torso rotation. This is Riko in Mega Man X4: detailed green bob, violet eye, fitted white military jacket and short pleated white skirt with gray fold planes and thin selective navy edges, cyan-lined attached white cape, finely segmented white knee boots. SECOND reference shows the accepted idle, newly refined raised-arm pose, and the existing rear-facing rising slash. Match their native pixel detail in collar, cuffs, seams, skirt folds and boot joints without widening/thickening the limbs or outlines. Preserve the first reference weapon grip positions and short black/cyan handles exactly; NO long sword, no flame or special effects. Do not substitute poses or turn rear views into frontal uppercuts. Retain leg length, compact torso, current silhouette and body scale. Transparent background, no floor, no labels, no blur, no soft illustration or motion streaks. Enrich only the overly plain clothing and boots while preserving the existing fine hair/face.'''
    if page==2:prompt+=' Only the TOP LEFT pose is to be refined; the other THREE rear views are locked references and must remain unchanged.'
    (folder/'prompt.txt').write_text(prompt+'\n','utf8');(folder/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,96],grid=[2,2],crop=crop,frames=rows,apply_only_refs=refs if page==1 else[156]),indent=2)+'\n','utf8')
print(D)
