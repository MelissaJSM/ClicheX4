"""동일한 원래 몸체에 망토 끝만 다른186/187을 새185 몸체에 연결한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/burst_exit_registered01';D.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
oldpath=W/'riko/prepared_ceremony_v2/PL01_U.ARC';old=oldpath.read_bytes();assert sha(old)=='590ed75799910795db7f237688bbd10ef3a282a7d12910956d798f497e67f818'
newpath=W/'riko/prepared_followup_cloth_v1/PL01_U.ARC';new=newpath.read_bytes();assert sha(new)=='105a7ba315a8dc0ef09d229770c4238fd8364adba43b483a5364c83f0ba79141'
before=render(old,1,5,185)[0];master=render(new,1,5,185)[0]
mask=np.zeros_like(master,bool);mask[140:155,152:163]=True
targets={};rows=[]
for n in [186,187]:
    src=render(old,1,5,n)[0];current=render(new,1,5,n)[0]
    assert np.array_equal(src,current)
    assert np.array_equal(src[~mask],before[~mask])
    out=master.copy();out[mask]=src[mask]
    assert np.array_equal(out[~mask],master[~mask])
    p=D/f'b1_{n:03}_indices.png';Image.fromarray(out).save(p);targets[n]=out
    rows.append(dict(bank=1,ref=n,source_body_exact_outside_cape=True,cape_bounds=[152,140,163,155],cape_pixels_changed_from_original_185=int(np.count_nonzero(src!=before)),new_body_185_preserved_outside_cape=True,target=str(p.relative_to(ROOT)),target_sha256=sha(p.read_bytes())))
for label,pr in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(new,9),pr*32);sheet=Image.new('RGB',(1200,800),'#64717b');d=ImageDraw.Draw(sheet)
    for y,(n,target)in enumerate(targets.items()):
        for x,(name,a)in enumerate([('new185',master),('before',render(new,1,5,n)[0]),('new exit',target)]):
            pic=rgba(a,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(pic,(400*x,400*y+40),pic);d.text((400*x+5,400*y+5),f'{n} {name}',fill='white')
    sheet.save(D/f'{label}_comparison.png')
(D/'registration.json').write_text(json.dumps(dict(source_arc=str(newpath.relative_to(ROOT)),source_sha256=sha(new),original_body_comparison_source=str(oldpath.relative_to(ROOT)),original_body_comparison_sha256=sha(old),frames=rows,game_applied=False),indent=2)+'\n','utf8')
print(json.dumps(rows))
