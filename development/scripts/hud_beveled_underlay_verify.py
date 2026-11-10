"""v4 금속 홈 연장 결과를 원본 숫자칸/승인 심볼과 독립 대조한다."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.hud_underlay_verify import digest, read_assets, sha, picture, TARGETS, TILES
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import all_compositions, composed
from scripts.discover_inputs import psx_arc
from src.psx_ui_atlas import tile_pixels
import scripts.hud_beveled_underlay as maker

OUT = ROOT / 'work/hud_frame_fix_20261105/beveled_v4'
NAMES = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')


def fingerprints():
    # Runtime evidence may be added independently while this static check runs.
    return {p.relative_to(ROOT).as_posix(): digest(p)
            for p in OUT.rglob('*') if p.is_file()
            and p.name != 'independent.json' and 'application' not in p.parts}


def expected_picture(before, symbol, bounds):
    left, top = bounds[:2]
    result = before.copy()
    # Explicit 21-column x 5-row groove; no copy from the production function.
    motif = np.full((5, 21), 12, dtype=np.uint8)
    motif[1:3, 1:20] = 10
    motif[3, 1:20] = 11
    allowed = np.zeros(before.shape, dtype=bool)
    allowed[29-top:34-top, -19-left:2-left] = True
    result[29-top:34-top, -19-left:2-left] = motif
    foreground = np.zeros(before.shape, dtype=bool)
    foreground[24-top:41-top, -24-left:2-left] = symbol[24-top:41-top, -24-left:2-left] != 0
    result[foreground] = symbol[foreground]
    return result, allowed, foreground


def run():
    prepared = fingerprints()
    code_names = ('hud_beveled_underlay.py', 'hud_frame_underlay.py', 'hud_frame_fix.py')
    code_hashes = {name: digest(ROOT / 'scripts' / name) for name in code_names}
    original = ROOT / 'MegaMan X4.bin'
    original_sha = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    assert digest(original) == original_sha
    natives = read_assets(original, NAMES)
    inputs = {original.relative_to(ROOT).as_posix(): original_sha}
    results = {}
    negatives = []
    maker.configure()
    for project, (stem, source_sha) in maker.SOURCES.items():
        proposal = json.loads((OUT / project / 'proposal.json').read_text('utf8'))
        source = ROOT / proposal['baseline']
        symbols_path = ROOT / 'out' / project / 'overhaul_20261105_candidate04' / (stem + '.bin')
        assert digest(source) == source_sha == proposal['baseline_sha256']
        assert digest(symbols_path) == maker.SYMBOL_SOURCES[project]
        inputs[source.relative_to(ROOT).as_posix()] = source_sha
        inputs[symbols_path.relative_to(ROOT).as_posix()] = maker.SYMBOL_SOURCES[project]
        sources = read_assets(source, NAMES)
        symbols = read_assets(symbols_path, NAMES)
        resources = {}
        for name in NAMES:
            before = sources[name]
            spec = proposal['files'][name]
            after = (ROOT / spec['path']).read_bytes()
            assert sha(before) == spec['before'] and sha(after) == spec['after']
            assert len(before) == len(after) == spec['size']
            old_rows, new_rows = psx_arc(before), psx_arc(after)
            layout = lambda rows: [{k: v for k, v in r.items() if k != 'sha256'} for r in rows]
            assert layout(old_rows) == layout(new_rows)
            record = next(r for r in old_rows if int(r['type'], 16) == 0x10206)
            low, high = record['offset'], record['offset'] + record['size']
            assert before[:low] == after[:low] and before[high:] == after[high:]
            old_texture, new_texture = entry(before, 0x10206), entry(after, 0x10206)
            comps = all_compositions(entry(before, 3))
            users = {}
            for key, comp in comps.items():
                for part in comp['parts']:
                    users.setdefault(part['page'] * 256 + part['tile'], set()).add(key)
            changed = {n for n in range(len(old_texture) // 128)
                       if tile_pixels(old_texture, n) != tile_pixels(new_texture, n)}
            assert changed and changed <= TILES[project][name]
            assert all(users[t] <= TARGETS for t in changed)
            digits = []
            for digit in range(10):
                a, az, ab = picture(before, 59 + digit)
                b, bz, bb = picture(after, 59 + digit)
                assert az == bz and ab == bb and np.array_equal(a, b)
                digits.append((a, ab))
            frame_results = []
            combinations = 0
            for number in range(69, 78):
                a, size, bounds = picture(before, number)
                b, new_size, new_bounds = picture(after, number)
                native, ns, nb = picture(natives[name], number)
                symbol, ss, sb = picture(symbols[name], number)
                assert size == new_size == ns == ss and bounds == new_bounds == nb == sb
                left, top = bounds[:2]
                expected, allowed, foreground = expected_picture(a, symbol, bounds)
                assert int(allowed.sum()) == 105
                assert np.array_equal(b, expected)
                assert np.array_equal(a[~allowed], b[~allowed])
                assert np.array_equal(a > 0, b > 0)
                assert np.array_equal(b[foreground], symbol[foreground])
                assert not np.any((a != b) & foreground)
                assert set(map(int, b[(a != b)])) <= {10, 11, 12}
                assert np.array_equal(b[:, 2-left:], a[:, 2-left:])
                assert np.array_equal(b[:29-top], a[:29-top])
                assert np.array_equal(b[34-top:], a[34-top:])
                # Left cap, original upper shoulder and numeric rim stay exact.
                assert np.array_equal(b[:, -22-left:-19-left], a[:, -22-left:-19-left])
                assert np.array_equal(b[24-top], a[24-top])
                assert np.array_equal(b[25-top:39-top, 2-left:], native[25-top:39-top, 2-left:])
                aperture = native == 14
                symbol_dark = foreground & (symbol == 14)
                dark_count = 56 if name == 'PL01_U.ARC' else 51
                assert int(aperture.sum()) == dark_count
                assert not np.any(aperture & foreground)
                assert np.array_equal(b == 14, aperture | symbol_dark)
                assert np.all(b[31-top, -22-left:16-left] != 0)
                for glyph, box in digits:
                    yy, xx = np.nonzero(glyph)
                    gy = yy + box[1] + 32 - top
                    gx = xx + box[0] + 7 - left
                    assert np.array_equal(a[gy, gx], b[gy, gx])
                    old_composite, new_composite = a.copy(), b.copy()
                    old_composite[gy, gx] = glyph[yy, xx]
                    new_composite[gy, gx] = glyph[yy, xx]
                    assert np.array_equal(old_composite[:, 2-left:], new_composite[:, 2-left:])
                    combinations += 1
                frame_results.append({
                    'frame': number, 'changed_pixels': int(np.count_nonzero(a != b)),
                    'only_allowed_105px_motif_changed': True,
                    'symbol_opaque_pixels_preserved': int(foreground.sum()),
                    'original_number_E_pixels': dark_count,
                    'original_number_mask_sha256': sha(aperture.tobytes()),
                    'symbol_E_pixels_separate': int(symbol_dark.sum()),
                    'geometry_alpha_gauge_upper_shoulder_caps_digit_rim_preserved': True,
                })
            bank_count = int.from_bytes(entry(before, 3)[:4], 'little') // 4
            static = {1, 2, 3, 4, 6} if bank_count == 7 else {1, 2, 3, 4, *range(9, bank_count)}
            protected_frames = 0
            for key, comp in comps.items():
                if key[0] not in static or key in TARGETS:
                    continue
                a, az, ab, _ = composed(old_texture, comp)
                b, bz, bb, _ = composed(new_texture, comp)
                assert az == bz and ab == bb and np.array_equal(a, b)
                protected_frames += 1
            reproduced, _ = maker.patch(before)
            assert reproduced == after
            wrong = bytearray(before)
            wrong[-1] ^= 1
            try:
                maker.patch(bytes(wrong))
            except ValueError as error:
                assert str(error) == 'Unsupported source ARC'
                negatives.append(project + '/' + name + '/wrong_source')
            else:
                raise AssertionError('Wrong source accepted')
            resources[name] = {
                'before_sha256': sha(before), 'after_sha256': sha(after),
                'changed_private_tiles': sorted(changed), 'frames': frame_results,
                'non_target_static_frames_identical': protected_frames,
                'nontexture_entries_palette_coordinates_timing_audio_identical': True,
                'digit_composite_checks': combinations, 'reproduced_byte_identical': True,
            }
        results[project] = resources
    # Memory-only rejection checks. No altered input is written to disk.
    sample = sources['PL00_U.ARC']
    a, _, box = picture(sample, 69)
    n, _, _ = picture(natives['PL00_U.ARC'], 69)
    s, _, _ = picture(symbols['PL00_U.ARC'], 69)
    left, top = box[:2]
    for case, x, y, value in (('erase_native_E', 5, 31, 0), ('extend_native_E', 5, 24, 14)):
        invalid = a.copy()
        invalid[y-top, x-left] = value
        try:
            maker.desired(invalid, n, s, box)
        except ValueError as error:
            assert str(error) == 'Native number aperture or symbol dark pixels changed'
            negatives.append(case)
        else:
            raise AssertionError('Bad aperture accepted')
    regular = maker.previous.desired
    calls = [0]
    def conflict(before, native, symbol, bounds):
        result = regular(before, native, symbol, bounds)
        calls[0] += 1
        result[30-bounds[1], -1-bounds[0]] = 1 if calls[0] == 1 else 2
        return result
    try:
        maker.previous.desired = conflict
        try:
            maker.patch(sample)
        except ValueError as error:
            assert str(error) == 'Shared HUD pixel conflict'
            negatives.append('conflicting_shared_HUD_pixel')
        else:
            raise AssertionError('Shared pixel conflict accepted')
    finally:
        maker.previous.desired = regular
    assert prepared == fingerprints()
    assert all(digest(ROOT / p) == h for p, h in inputs.items())
    assert all(digest(ROOT / 'scripts' / n) == h for n, h in code_hashes.items())
    report = {
        'passed': True, 'variant': 'beveled_v4', 'resources': results,
        'HUD_frames': 54, 'digit_composite_checks': 540,
        'negative_cases_rejected': negatives, 'source_discs': inputs,
        'source_discs_prepared_files_production_code_unchanged': True,
        'groove_world_bounds_exclusive': [-19, 29, 2, 34],
        'native_number_E_counts': {'X_and_Ultimate': 51, 'Zero': 56},
        'accepted_symbol_pixels_and_alpha_exact': True,
        'comparison_and_original_X_Zero_images_viewed': True,
        'visual_assessment': '왼쪽 금속 홈이 심볼 뒤로 연결되고, 숫자칸과 심볼은 원래 위치를 유지한다.',
        'runtime_verified': False, 'user_accepted': False,
        'limitations': ['정적 검증이며 실제 GPU/프레임버퍼 검사는 별도 runtime.json으로 기록한다.'],
        'writes': ['scripts/hud_beveled_underlay_verify.py',
                   'work/hud_frame_fix_20261105/beveled_v4/independent.json'],
    }
    (OUT / 'independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'passed': True, 'frames': 54, 'digits': 540, 'negative_rejected': len(negatives)}))


if __name__ == '__main__':
    run()
