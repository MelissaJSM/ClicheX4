"""Prepare detail-only editing of the eight rotating bodies, without saber effects."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
P=Path(__file__).resolve().parent/'prepared_ceremony_clothes_v2/PL01_U.ARC';arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='0de65ee0ee43f9c2713af4ce372023325cc2389bd42664f460ff93d2efd2a7d0'
D=P.parent.parent/'spin_clothes17';D.mkdir(exist_ok=False);pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
# Preserve actual fine head texels, including the original 45 degree sample rule.
base=np.zeros((384,384),np.uint8);src=render(arc,1,5,161)[0];base[141:160,146:169]=src[141:160,146:169]
heads={}
for j,n in enumerate(range(161,176,2)):
    mask=np.array(Image.fromarray(base).rotate(j*45,Image.Resampling.NEAREST,center=(160.5,160)))
    old=render(arc,1,5,n)[0];match=bool(np.array_equal(old[mask>0],mask[mask>0]));heads[n]=dict(matches=match,pixels=int(np.count_nonzero(mask)))
    assert match,f'Original rotated head mismatch {n}'
    Image.fromarray(mask).save(D/f'head_{n:03}.png')
for page,refs in enumerate([list(range(161,168,2)),list(range(169,176,2))],1):
    p=D/f'page{page}';p.mkdir();sheet=Image.new('RGBA',(1536,2304));keys=[(1,n)for n in refs]+[(0,147),(0,21)];rows=[]
    for i,(b,n)in enumerate(keys):
        im=rgba(render(arc,b,b*5,n)[0],pal);im.save(p/f'b{b}_{n:03}_source.png');sheet.paste(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768));rows.append(dict(bank=b,ref=n,cell=i))
    sheet.save(p/'targets.png')
    prompt='''Edit the TOP FOUR sprites ONLY in this transparent 2-column, 3-row game sprite sheet. The BOTTOM TWO are locked finished idle and jumping references. This is a very small pixel-art DETAIL REPAIR of Riko in Mega Man X4: green bob hair, white fitted jacket, short white skirt, attached teal-lined white cape, white knee boots. The top four are consecutive sword-spin poses rotating at 45 degrees. Preserve every pose's original exact rotation, location, head, hands, feet, knees, cape silhouette and size. Do NOT turn any pose upright or enlarge it. Their fine green hair and faces are already final: keep them. Refine ONLY the too-flat white boot panels, ankle and knee seams, small cuff and skirt folds with compact gray/navy pixel clusters matching the bottom references. Keep thin selective outlines with no heavy black border. No new weapon, effects, glow, ornaments or separate objects. Do not change leg lengths or the rotation center. Each cell is 96x96 native pixels shown8x. Preserve all 6 cell positions and native body scale. Transparent background.'''
    (p/'prompt.txt').write_text(prompt,'utf8');(p/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(P),native_cell=[96,96],grid=[2,3],crop=crop,frames=rows,apply_only_keys=[[1,n]for n in refs],head_masks=heads),indent=2)+'\n','utf8')
print(D)
