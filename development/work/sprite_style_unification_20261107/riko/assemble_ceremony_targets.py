"""Collect nine authored poses; reproduce the proven departure rule on new pose3."""
from pathlib import Path
import sys,json,hashlib,shutil,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).resolve().parent/'ceremony_clothes16';O=D/'targets01';assert not O.exists();O.mkdir()
P=D.parent/'prepared_rising_clothes_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='dd61d2f1b77cab1c43256dd6e2553f631067100338352c86aaea1d5d41eddec7'
rows=[]
for i in range(1,6):
    d=D/f'page{i}/registered01';reg=json.loads((d/'registration.json').read_text('utf8'))
    for r in reg['frames']:
        p=ROOT/r['target'];assert sha(p)==r['target_sha256'];q=O/p.name;shutil.copyfile(p,q)
        rows.append(dict(r,source_registration=str((d/'registration.json').relative_to(ROOT)),target=str(q.relative_to(ROOT)),target_sha256=sha(q)))
def derive(a,n):
    radius=1 if n==7 else 2;out=np.zeros_like(a);mask=a>0
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if abs(dx)+abs(dy)<=radius:out[np.roll(np.roll(mask,dy,0),dx,1)]=15 if n==7 else 12
    pale=np.array([0,12,12,12,15,15,12,15,15,15,12,12,15,12,15,15],np.uint8)
    out[mask]=a[mask] if n==7 else pale[a[mask]]
    return out
old=render(arc,1,5,3)[0];new=np.array(Image.open(O/'b1_003_indices.png'))
for n in(7,8):
    assert np.array_equal(derive(old,n),render(arc,1,5,n)[0]),f'Existing flash rule mismatch {n}'
    q=O/f'b1_{n:03}_indices.png';Image.fromarray(derive(new,n)).save(q)
    rows.append(dict(bank=1,ref=n,target=str(q.relative_to(ROOT)),target_sha256=sha(q),derived_from='b1_003',radius_manhattan=1 if n==7 else 2,original_rule_error_pixels=0))
for label,pr in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),pr*32)
    page([(f'{n} before',rgba(render(arc,1,5,n)[0],pal))for n in(3,7,8)]+[(f'{n} after',rgba(np.array(Image.open(O/f'b1_{n:03}_indices.png')),pal))for n in(3,7,8)],rgba(render(arc,0,0,147)[0],pal),O/f'{label}_departure.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps(dict(source_arc=str(P.relative_to(ROOT)),source_sha256=sha(P),frames=rows,candidate_only=True,runtime_verified=False),indent=2)+'\n','utf8')
print('Authored9 + derived2; old departure rules reproduced exactly')
