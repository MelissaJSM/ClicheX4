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
out = R / 'ground_remaining22/targets01'
out.mkdir(exist_ok=False)
rows, proof, covered, all_old = [], [], {}, {}
for bank in [0, 1]:
    for f in graphics_bank(entry(a, 2), bank)['frames']:
        try:
            all_old[bank, f['index']] = render(a, bank, bank * 5, f['index'])[0]
        except ValueError:
            # Known partial-upload references require previous VRAM; never alias them.
            pass
for page in range(23, 27):
    reg = json.loads((R / f'ground_boots{page}/registered01/registration.json').read_text('utf8'))
    assert reg['source_sha256'] == sha(a)
    for row in reg['frames']:
        k = row['bank'], row['ref']
        f = ROOT / row['target']
        assert sha(f.read_bytes()) == row['target_sha256']
        new = np.array(Image.open(f))
        old = all_old[k]
        keys = [q for q, v in all_old.items() if q[0] == k[0] and np.array_equal(old, v)]
        for q in keys:
            if q in covered:
                assert np.array_equal(covered[q], new)
                continue
            covered[q] = new
            f = out / f'b{q[0]}_{q[1]:03}_indices.png'
            Image.fromarray(new).save(f)
            r = dict(row)
            r.update(bank=q[0], ref=q[1], target=str(f.relative_to(ROOT)),
                     target_sha256=sha(f.read_bytes()), art_key=list(k), exact_whole_body_alias=q != k)
            rows.append(r)
        proof.append({'source_key': list(k), 'exact_whole_body_aliases': [list(q) for q in keys if q != k]})
(out / 'registration.json').write_text(json.dumps({
    'source_arc': str(P.relative_to(ROOT)), 'source_sha256': sha(a),
    'source_pages': list(range(23, 27)), 'frames': rows, 'alias_proof': proof,
    'candidate_only': True, 'game_applied': False}, indent=2) + '\n', 'utf8')
print(json.dumps({'targets': len(rows), 'aliases': proof}))
