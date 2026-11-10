"""대시의 실제 공유 몸체와 X축 1px 파생을 원본으로 입증해 새 원화에 적용한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/dash_clothes11';OUT=D/'targets01';OUT.mkdir(exist_ok=False)
arc=(W/'riko/prepared_wall_clothes_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
targets={};sources=[]
for page,folder in [(1,'registered02'),(2,'registered01'),(3,'registered01')]:
    r=json.loads((D/f'page{page}'/folder/'registration.json').read_text('utf8'));assert r['source_sha256']==sha(arc);sources.append(r)
    for f in r['frames']:
        p=ROOT/f['target'];assert sha(p.read_bytes())==f['target_sha256'];targets[f['ref']]=np.array(Image.open(p))
assert sorted(targets)==list(range(44,53))
authored={n:q.copy()for n,q in targets.items()};old={n:render(arc,0,0,n)[0]for n in targets}
region=binary_dilation((old[46]!=old[47])|(old[48]!=old[47]),iterations=1)
region[171:]=False
yy,xx=np.where(region);bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
rows=[]
for n in [46,48]:
    assert np.array_equal(old[n][~region],old[47][~region])
    targets[n]=targets[47].copy();targets[n][region]=authored[n][region]
    rows.append(dict(ref=n,body_master=47,original_body_exact_outside_region=True,cape_region=bounds,new_body_exact_outside_region=bool(np.array_equal(targets[n][~region],targets[47][~region])),old_body_pixels_copied=0))
assert np.array_equal(np.roll(old[51],-1,axis=1),old[52])
targets[52]=np.roll(targets[51],-1,axis=1)
rows.append(dict(ref=52,body_master=51,translation=[-1,0],original_full_display_exact=True,new_full_display_exact=True,old_body_pixels_copied=0))
Image.fromarray(region.astype('uint8')*255).save(OUT/'cape_region.png')
for n,q in targets.items():Image.fromarray(q).save(OUT/f'b0_{n:03}_indices.png')
for label,pr in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),pr*32)
    for page,refs in enumerate([[44,45,46],[47,48,49],[50,51,52]]):
        sheet=Image.new('RGB',(1200,1200),'#64717b');dr=ImageDraw.Draw(sheet)
        for i,n in enumerate(refs):
            for j,(name,q)in enumerate([('old',old[n]),('new authored',authored[n]),('shared family',targets[n])]):
                pic=rgba(q,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(pic,(j*400,i*400+35),pic);dr.text((j*400+4,i*400+5),f'{n}: {name}',fill='white')
        sheet.save(OUT/f'{label}_comparison_{page:02}.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_sha256=sha(arc),sources=sources,derived_shared_body=rows,frames=[dict(ref=n,bank=0,target=str((OUT/f'b0_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b0_{n:03}_indices.png').read_bytes()))for n in sorted(targets)],runtime_verified=False),indent=2)+'\n','utf8')
print(json.dumps(rows))
