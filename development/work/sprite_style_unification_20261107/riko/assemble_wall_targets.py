"""벽 정지 루프의 같은 몸은 공유하고 실제 변하는 망토 영역만 새 원화에서 연결한다."""
from pathlib import Path
import json,sys,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/wall_clothes10';OUT=D/'targets01';OUT.mkdir(exist_ok=False)
arc=(W/'riko/prepared_vehicle_clothes_v2/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
targets={};sources=[]
for folder in [D/'registered01',D/'page2/registered01']:
    r=json.loads((folder/'registration.json').read_text('utf8'));assert r['source_sha256']==sha(arc);sources.append(r)
    for f in r['frames']:
        p=ROOT/f['target'];assert sha(p.read_bytes())==f['target_sha256'];targets[f['ref']]=np.array(Image.open(p))
assert sorted(targets)==list(range(37,44))
old={n:render(arc,0,0,n)[0]for n in [41,42,43]}
variation=(old[41]!=old[42])|(old[41]!=old[43])
# One-pixel allowance is only for the newly drawn cape edge, not a whole-image filter.
region=binary_dilation(variation,iterations=1);region[171:]=False
yy,xx=np.where(region);bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
master=targets[41].copy();rows=[]
for n in [42,43]:
    authored=targets[n].copy();targets[n]=master.copy();targets[n][region]=authored[region]
    assert np.array_equal(targets[n][~region],master[~region])
    rows.append(dict(ref=n,body_master=41,cape_region=bounds,body_outside_cape_region_exact=True,original_body_outside_cape_region_exact=bool(np.array_equal(old[n][~region],old[41][~region])),old_pixels_copied=0))
assert all(r['original_body_outside_cape_region_exact']for r in rows)
Image.fromarray(region.astype('uint8')*255).save(OUT/'cape_region.png')
for n,a in targets.items():Image.fromarray(a).save(OUT/f'b0_{n:03}_indices.png')
pal=struct.unpack_from('<16H',entry(arc,9));sheet=Image.new('RGB',(1200,400*3),'#64717b');dr=ImageDraw.Draw(sheet)
for i,n in enumerate([41,42,43]):
    for j,(name,a)in enumerate([('old',old[n]),('authored',np.array(Image.open((D/'registered01'if n==41 else D/'page2/registered01')/f'b0_{n:03}_indices.png'))),('shared body / authored cape',targets[n])]):
        pic=rgba(a,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(pic,(j*400,i*400+30),pic);dr.text((j*400+4,i*400+5),f'{n} {name}',fill='white')
sheet.save(OUT/'shared_body_comparison.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_sha256=sha(arc),sources=sources,loop_body_registration=rows,frames=[dict(ref=n,bank=0,target=str((OUT/f'b0_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b0_{n:03}_indices.png').read_bytes()))for n in sorted(targets)],runtime_verified=False),indent=2)+'\n','utf8')
print(json.dumps(rows))
