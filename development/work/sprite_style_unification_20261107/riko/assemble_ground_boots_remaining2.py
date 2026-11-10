"""Collect local boot targets and only proven exact whole-body aliases."""
from pathlib import Path
import sys, json, hashlib
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
R = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank

P = R / 'prepared_ground_boots_v4/PL01_U.ARC'
a = P.read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(a) == '540658ec80aa24415d1df97e37dac0c1a28898907cc8778ba5fa037224e87eb2'
out = R / 'ground_remaining22/targets02'
out.mkdir(exist_ok=False)
rows, proof, covered, all_old = [], [], {}, {}
for bank in [0, 1]:
    for f in graphics_bank(entry(a, 2), bank)['frames']:
        try:
            all_old[bank, f['index']] = render(a, bank, bank * 5, f['index'])[0]
        except ValueError:
            # Known partial-upload references require previous VRAM; never alias them.
            pass
def signature(v):
    yy,xx=np.nonzero(v)
    if not len(xx):return None,None
    x0,y0=int(xx.min()),int(yy.min());cut=v[y0:int(yy.max())+1,x0:int(xx.max())+1]
    return (cut.shape,sha(cut.tobytes())),(x0,y0)
signatures={k:signature(v) for k,v in all_old.items()}
for page in range(23, 27):
    reg = json.loads((R / f'ground_boots{page}/registered01/registration.json').read_text('utf8'))
    assert reg['source_sha256'] == sha(a)
    for row in reg['frames']:
        k = row['bank'], row['ref']
        f = ROOT / row['target']
        assert sha(f.read_bytes()) == row['target_sha256']
        new = np.array(Image.open(f))
        old = all_old[k]
        keys = [q for q in all_old if q[0] == k[0] and signatures[q][0] == signatures[k][0]]
        for q in keys:
            dx=signatures[q][1][0]-signatures[k][1][0];dy=signatures[q][1][1]-signatures[k][1][1]
            shifted=np.roll(np.roll(new,dy,axis=0),dx,axis=1)
            assert np.array_equal(np.roll(np.roll(old,dy,axis=0),dx,axis=1),all_old[q])
            assert np.array_equal(shifted>0,all_old[q]>0)
            if q in covered:
                assert np.array_equal(covered[q], shifted)
                continue
            covered[q] = shifted
            f = out / f'b{q[0]}_{q[1]:03}_indices.png'
            Image.fromarray(shifted).save(f)
            r = dict(row)
            r.update(bank=q[0], ref=q[1], target=str(f.relative_to(ROOT)),
                     target_sha256=sha(f.read_bytes()), art_key=list(k), exact_whole_body_alias=q != k,
                     native_translation=[dx,dy], original_game_origin_preserved=True,
                     boot_material_regions=[[x0+dx,y0+dy,x1+dx,y1+dy] for x0,y0,x1,y1 in row["boot_material_regions"]])
            rows.append(r)
        proof.append({'source_key': list(k), 'exact_whole_body_aliases': [{'key':list(q),'dx':signatures[q][1][0]-signatures[k][1][0],'dy':signatures[q][1][1]-signatures[k][1][1]} for q in keys if q != k]})
(out / 'registration.json').write_text(json.dumps({
    'source_arc': str(P.relative_to(ROOT)), 'source_sha256': sha(a),
    'source_pages': list(range(23, 27)), 'frames': rows, 'alias_proof': proof,
    'candidate_only': True, 'game_applied': False}, indent=2) + '\n', 'utf8')
print(json.dumps({'targets': len(rows), 'aliases': proof}))
