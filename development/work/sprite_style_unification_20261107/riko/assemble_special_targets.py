"""특수 기술의 원손잡이/망토 변화를 보호하고 입증된 몸체 공유만 전개한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/special_clothes13';ART=D/'registered01';OUT=D/'targets01';OUT.mkdir(exist_ok=False)
arc=(W/'riko/prepared_dash_clothes_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();reg=json.loads((ART/'registration.json').read_text('utf8'));assert reg['source_sha256']==sha(arc)
keys={r['ref']:np.array(Image.open(ROOT/r['target']))for r in reg['frames']};old={n:render(arc,1,5,n)[0]for n in [50,51,53,57,108,110,112,114,116,119,122,125,128,129]}
rows=[]
for n in [108,128]:
    a=keys[n].copy();legs=a[173:].copy();a[173:]=0;a[172:383]=legs;keys[n]=a
    assert np.where(a)[0].max()==np.where(old[n])[0].max()==183
    rows.append(dict(ref=n,new_boot_registration={'rows_from':173,'translation':[0,-1]},sole_y=183,original_pixels_copied=0))
assert np.array_equal(old[50][164:],old[57][164:]);keys[57][164:]=keys[50][164:]
rows.append(dict(ref=57,new_lower_body_master=50,rows_from=164,original_lower_body_exact=True))
targets={50:keys[50].copy(),57:keys[57].copy(),128:keys[128].copy()}
hand=np.zeros((384,384),bool);hand[140:154,145:159]=True
for n in [51,53]:
    assert np.array_equal(old[n][~hand],old[50][~hand]);q=keys[50].copy();q[hand]=old[n][hand];targets[n]=q
    rows.append(dict(ref=n,new_body_master=50,original_body_exact_outside_hand=True,original_hand_region=[145,140,159,154],original_nonzero_hand_pixels=int(np.count_nonzero(old[n][hand]))))
for n in [108,110,112,114,116,119,122,125]:
    dx=-1 if n==110 else 0;base=np.roll(old[108],dx,axis=1);q=np.roll(keys[108],dx,axis=1)
    cape=np.zeros_like(hand);cape[147:165,166+dx:186+dx]=True
    grip=np.zeros_like(hand);grip[156:165,80:127+dx]=True
    protected=cape|grip;assert np.array_equal(base[~protected],old[n][~protected]),n
    q[protected]=old[n][protected];targets[n]=q
    rows.append(dict(ref=n,new_body_master=108,translation=[dx,0],original_body_exact_outside_regions=True,original_cape_tip=[166+dx,147,186+dx,165],original_weapon_region=[80,156,127+dx,165],original_cape_pixels=int(np.count_nonzero(old[n][cape]))))
assert np.array_equal(old[128],old[129]);targets[129]=targets[128].copy();rows.append(dict(ref=129,new_body_master=128,original_full_display_exact=True))
for n,a in targets.items():Image.fromarray(a).save(OUT/f'b1_{n:03}_indices.png')
for label,pr in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),pr*32)
    for page,refs in enumerate([[50,51,53,57],[108,110,114,119],[112,116,122,125],[128,129]]):
        sheet=Image.new('RGB',(1536,400*len(refs)),'#64717b');dr=ImageDraw.Draw(sheet)
        for i,n in enumerate(refs):
            for j,(name,a)in enumerate([('idle',render(arc,0,0,147)[0]),('old',old[n]),('candidate',targets[n])]):
                pic=rgba(a,pal).crop((80,104,208,200)).resize((512,384),Image.Resampling.NEAREST);sheet.paste(pic,(j*512,i*400+16),pic);dr.text((j*512+4,i*400+3),f'{n} {name}',fill='white')
        sheet.save(OUT/f'{label}_comparison_{page:02}.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_sha256=sha(arc),source_registration=reg,derivations=rows,frames=[dict(ref=n,bank=1,target=str((OUT/f'b1_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b1_{n:03}_indices.png').read_bytes()))for n in sorted(targets)],runtime_verified=False),indent=2)+'\n','utf8');print(json.dumps({'targets':sorted(targets)}))
