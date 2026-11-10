"""명암 복원의 입력거부·보존 근거를 prepared ARC 읽기 전용으로 추가 검사."""
import sys
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts import restore_shibuki_special_detail as r

def rejected(label, callback):
    try:
        callback()
    except (ValueError, AssertionError) as exc:
        return {'case': label, 'rejected': True, 'reason': str(exc)}
    raise AssertionError(f'Invalid input accepted: {label}')

baseline = (ROOT / 'work/sprite_consistency_20261105/x/shibuki/PL00_U.ARC').read_bytes()
prepared = (r.D / 'prepared_v1/PL00_U.ARC').read_bytes()
proof = json.loads((r.D / 'prepared_v1/verification.json').read_text('utf8'))
assert r.sha(baseline) == r.BASE and r.sha(prepared) == proof['output_sha256']
cases = []
bad = bytes([baseline[0] ^ 1]) + baseline[1:]
cases.append(rejected('unsupported baseline hash', lambda: r.patch_special_detail(baseline, bad)))
cases.append(rejected('unknown input hash', lambda: r.patch_special_detail(bad, baseline)))
cases.append(rejected('repeat patch on selected changed data', lambda: r.patch_special_detail(prepared, baseline, expected_input_sha=r.sha(prepared))))
p = bytearray(r.unique_entry(baseline, 9)); p[3] ^= 1
bad_palette = r.entry_replace(baseline, 9, p)
cases.append(rejected('changed palette with explicit hash', lambda: r.patch_special_detail(bad_palette, baseline, expected_input_sha=r.sha(bad_palette))))
cases.append(rejected('truncated ARC with explicit hash', lambda: r.patch_special_detail(baseline[:-1], baseline, expected_input_sha=r.sha(baseline[:-1]))))
g, c = (r.unique_entry(baseline, t) for t in (2, 3)); desired, _, _ = r.targets()
raw, frame = r.native_raw(g, 0, 101); cp = r.composition_frame(c, 0, 101)
changed_alpha = desired[101].copy(); y, x = np.argwhere(changed_alpha > 0)[0]; changed_alpha[y, x] = 0
cases.append(rejected('selected visible alpha edit', lambda: r.restore_visible_texels(raw, frame['tile_count'], cp, changed_alpha)))
# Independent per-nibble ownership: every changed source remains opaque and is
# one of the original native draw winners at a changed target world position.
checks = []
ng = r.unique_entry(prepared, 2)
for n in r.FRAMES:
    old, f = r.native_raw(g, 0, n); new, _ = r.native_raw(ng, 0, n)
    cp = r.composition_frame(c, 0, n); pixels, size, box, provenance = r.compose_indices(old, f['tile_count'], cp)
    target = desired[n][80+box[1]:80+box[3], 80+box[0]:80+box[2]].tobytes()
    expected = {(provenance[i]['byte'], provenance[i]['shift']): v for i, v in enumerate(target) if v != pixels[i]}
    observed = {(i, shift): (b >> shift) & 15 for i, (a, b) in enumerate(zip(old, new)) for shift in (0, 4) if (a >> shift) & 15 != (b >> shift) & 15}
    assert observed == expected
    assert all(((old[i] >> shift) & 15) and value for (i, shift), value in observed.items())
    checks.append({'frame': n, 'changed_source_nibbles': len(observed), 'only_original_visible_owners_changed': True})
r.write(r.D / 'prepared_v1/independent.json', {'passed': True, 'artifact_sha256': r.sha(prepared), 'negative_tests': cases,
        'source_ownership': checks, 'same_source_alpha': True, 'runtime_verified': False})
print(json.dumps({'passed': True, 'negative_tests': len(cases), 'changed_source_nibbles': sum(x['changed_source_nibbles'] for x in checks)}))
