"""In-memory format/alpha/sharing checks; never creates a BIN or final artwork."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.prepare_hud_emblems import *

directory = Path(__file__).parent
original, current, palette = load_inputs()
checks = []
for name in RECORDS:
    zero = np.zeros((13, 23), np.uint8)
    result, proof = patch_archive(name, original[name], current[name], zero)
    assert result == current[name]
    checks.append({'name': name, 'test': 'zero_is_identity', 'pass': True})
    pixels, _, bounds, _ = composed(entry(current[name], 0x10206), aliased_composition(entry(current[name], 3), 1, 69))
    ys, xs = inner_slice(bounds)
    native = pixels[ys, xs]
    y, x = next(zip(*np.where(native > 0)))
    edit = zero.copy()
    edit[y, x] = 14 if native[y, x] != 14 else 13
    result, proof = patch_archive(name, original[name], current[name], edit)
    assert result != current[name] and proof['changed_nibbles'] > 0
    assert entry(result, 3) == entry(current[name], 3)
    checks.append({'name': name, 'test': 'single_native_opaque_pixel', 'pass': True,
                   'changed_nibbles': proof['changed_nibbles'], 'static_frames': proof['static_compositions_checked']})
    # Exercise the whole authorized interior and all nonzero palette values,
    # including source overlaps and all nine HP-capacity compositions.
    pattern = np.arange(13 * 23, dtype=np.uint16).reshape(13, 23) % 15 + 1
    pattern = np.where(native > 0, pattern, 0).astype(np.uint8)
    result, proof = patch_archive(name, original[name], current[name], pattern)
    assert result != current[name] and proof['changed_nibbles'] > 1
    checks.append({'name': name, 'test': 'whole_authorized_interior_and_palette', 'pass': True,
                   'changed_nibbles': proof['changed_nibbles'], 'static_frames': proof['static_compositions_checked']})
    y, x = next(zip(*np.where(native == 0)))
    invalid = zero.copy()
    invalid[y, x] = 14
    try:
        patch_archive(name, original[name], current[name], invalid)
    except ValueError as exc:
        assert 'transparent' in str(exc)
        checks.append({'name': name, 'test': 'original_transparency_rejected', 'pass': True})
    else:
        raise AssertionError('Transparent pixel write was not rejected')

for label, mode, shape, value in [('size', 'L', (23, 12), 1), ('rgb', 'RGB', (23, 13), 1),
                                ('index16', 'L', (23, 13), 16), ('valid', 'L', (23, 13), 0)]:
    path = directory / ('format_probe_' + label + '.png')
    Image.new(mode, shape, value).save(path)
    try:
        result = read_overlay(path)
    except ValueError:
        assert label != 'valid'
    else:
        assert label == 'valid' and not result.any()
    checks.append({'test': 'input_' + label, 'pass': True})

protected_hashes()
report = {'kind': 'hud_emblem_technical_in_memory_checks', 'checks': checks,
          'count': len(checks), 'parent_sha256': PARENT_SHA, 'source_sha256': SOURCE_SHA,
          'game_bin_written': False, 'arc_files_written': False, 'art_produced': False,
          'emulator_accessed': False}
(directory / 'self_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'checks': len(checks), 'all_passed': True, 'game_bin_written': False}))
