"""최신 ARC에서 남은 이동/기술/등장 자세를 읽기 전용 비교한다."""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_dash_clothes_v1/PL01_U.ARC';arc=P.read_bytes();D=W/'riko/remaining_after_dash12';D.mkdir(exist_ok=False)
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
sets={'movement':[(0,n)for n in range(3,21)],'special':[(1,n)for n in [50,51,52,53,54,55,56,57,108,110,112,114,116,118,120,122,124,126,128]],'rising':[(1,n)for n in range(133,159)],'ceremony':[(0,n)for n in range(249,254)]+[(1,n)for n in range(0,9)],'spin':[(1,n)for n in range(161,176)]}
rows=[]
for name,refs in sets.items():
    for page in range((len(refs)+8)//9):
        part=refs[page*9:page*9+9];sheet=Image.new('RGB',(1152,1152),'#64717b');dr=ImageDraw.Draw(sheet)
        for i,(b,n)in enumerate(part):
            a=render(arc,b,b*5,n)[0];pic=rgba(a,pal).crop(crop).resize((384,384),Image.Resampling.NEAREST);x=i%3*384;y=i//3*384;sheet.paste(pic,(x,y),pic);dr.text((x+5,y+5),f'b{b}_{n:03}',fill='white')
        out=D/f'{name}_{page:02}.png';sheet.save(out);rows.append(dict(path=str(out.relative_to(ROOT)),refs=part,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),root_reviewed=False))
(D/'inventory.json').write_text(json.dumps(dict(source=str(P.relative_to(ROOT)),sha256=hashlib.sha256(arc).hexdigest(),pages=rows),indent=2)+'\n','utf8')
print(json.dumps({'pages':len(rows),'refs':sum(map(len,sets.values()))}))
