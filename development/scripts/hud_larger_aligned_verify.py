"""v6 확대 심볼/금속 홈을 원소스에서 독립 복원하여 읽기 전용 검증한다."""
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
import scripts.hud_larger_aligned as maker

OUT = ROOT / 'work/hud_frame_fix_20261105/larger_aligned_v6'
NAMES = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')
LAYOUTS = {
    'ver_buki_riko': {'PL00_U.ARC': (21, 19, -18, 23), 'PL01_U.ARC': (18, 21, -17, 22), 'PL02_U.ARC': (21, 19, -18, 23)},
    'ver_rin_nana': {'PL00_U.ARC': (18, 21, -16, 22), 'PL01_U.ARC': (21, 19, -18, 23), 'PL02_U.ARC': (18, 21, -16, 22)},
}


def expected_picture(before, native, symbol, bounds, layout):
    left, top = bounds[:2]
    body = before.copy()
    for y in range(24, 41):
        for x in range(-24, 5):
            value = 0
            if 25 <= y <= 38:
                if -22 <= x <= -15:
                    value = int(native[y-top, -7-x-left])
                elif -14 <= x <= 4:
                    value = int(native[y-top, 5-left])
                if value == 14:
                    value = 10
                if x >= 2:
                    value = int(native[y-top, x-left])
            elif y == 24 and -18 <= x <= 2:
                value = int(native[y-top, x-left])
            body[y-top, x-left] = value
    motif = np.full((5, 21), 12, dtype=np.uint8)
    motif[1:3, 1:20] = 10
    motif[3, 1:20] = 11
    body[29-top:34-top, -19-left:2-left] = motif
    assert np.array_equal(body == 14, native == 14)
    old = symbol[24-top:41-top, -24-left:2-left]
    yy, xx = np.nonzero(old)
    crop = old[yy.min():yy.max()+1, xx.min():xx.max()+1]
    width, height, x0, y0 = layout
    # Integer pixel-center mapping, independently expressed without float casts.
    rows = ((2*np.arange(height)+1)*crop.shape[0]) // (2*height)
    cols = ((2*np.arange(width)+1)*crop.shape[1]) // (2*width)
    expanded = crop[np.ix_(rows, cols)]
    layer = np.zeros(before.shape, dtype=np.uint8)
    layer[y0-top:y0-top+height, x0-left:x0-left+width] = expanded
    result = body.copy()
    result[layer != 0] = layer[layer != 0]
    return result, body, layer, crop


def fingerprints():
    return {p.relative_to(ROOT).as_posix(): digest(p)
            for p in OUT.rglob('*') if p.is_file()
            and p.name != 'independent.json' and 'application' not in p.parts}


def run():
    initial = fingerprints()
    code_names = ('hud_larger_aligned.py', 'hud_aligned_bevel.py', 'hud_beveled_underlay.py', 'hud_frame_underlay.py', 'hud_frame_fix.py')
    code_hashes = {name: digest(ROOT / 'scripts' / name) for name in code_names}
    original = ROOT / 'MegaMan X4.bin'
    original_sha = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    assert digest(original) == original_sha
    natives = read_assets(original, NAMES)
    inputs = {original.relative_to(ROOT).as_posix(): original_sha}
    maker.configure()
    assert maker.LAYOUTS == LAYOUTS
    results, rejected = {}, []
    for project, (stem, expected_sha) in maker.SOURCES.items():
        proposal = json.loads((OUT / project / 'proposal.json').read_text('utf8'))
        source = ROOT / proposal['baseline']
        symbols_path = ROOT / 'out' / project / 'overhaul_20261105_candidate04' / (stem + '.bin')
        assert digest(source) == expected_sha == proposal['baseline_sha256']
        assert digest(symbols_path) == maker.SYMBOL_SOURCES[project]
        inputs[source.relative_to(ROOT).as_posix()] = expected_sha
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
            layout_rows = lambda rows: [{k: v for k, v in r.items() if k != 'sha256'} for r in rows]
            assert layout_rows(old_rows) == layout_rows(new_rows)
            record = next(r for r in old_rows if int(r['type'], 16) == 0x10206)
            low, high = record['offset'], record['offset']+record['size']
            assert before[:low] == after[:low] and before[high:] == after[high:]
            ot, nt = entry(before, 0x10206), entry(after, 0x10206)
            comps = all_compositions(entry(before, 3))
            users = {}
            for key, comp in comps.items():
                for part in comp['parts']:
                    users.setdefault(part['page']*256+part['tile'], set()).add(key)
            changed = {n for n in range(len(ot)//128) if tile_pixels(ot, n) != tile_pixels(nt, n)}
            assert changed == TILES[project][name]
            assert all(users[tile] <= TARGETS for tile in changed)
            digits = []
            for digit in range(10):
                a, az, ab = picture(before, 59+digit)
                b, bz, bb = picture(after, 59+digit)
                assert az == bz and ab == bb and np.array_equal(a, b)
                digits.append((a, ab))
            frames = []
            combinations = 0
            for number in range(69, 78):
                a, size, bounds, locations = composed(ot, comps[1, number])
                b, ns, nb = picture(after, number)
                native, os, ob = picture(natives[name], number)
                symbol, ss, sb = picture(symbols[name], number)
                assert size == ns == os == ss and bounds == nb == ob == sb
                left, top = bounds[:2]
                expected, body, layer, crop = expected_picture(a, native, symbol, bounds, LAYOUTS[project][name])
                mask = layer != 0
                assert np.array_equal(b, expected)
                assert np.array_equal(b[mask], layer[mask])
                assert set(map(int, np.unique(crop))) == set(map(int, np.unique(layer)))
                assert np.array_equal(b[~mask], body[~mask])
                assert np.array_equal(b[:22-top], a[:22-top])
                assert np.array_equal(b[:, 5-left:], a[:, 5-left:])
                assert not np.any(mask & (native == 14))
                dark_count = 56 if name == 'PL01_U.ARC' else 51
                assert int((native == 14).sum()) == dark_count
                assert np.array_equal(b == 14, (native == 14) | (layer == 14))
                yy, xx = np.nonzero(mask)
                for y, x in zip(yy, xx):
                    positions = locations[int(y)*size[0]+int(x)]
                    assert positions
                    for offset, shift in positions:
                        tile = (offset//128//16)*16+(offset%128)//8
                        assert tile in TILES[project][name] and users[tile] <= TARGETS
                for glyph, box in digits:
                    gy, gx = np.nonzero(glyph)
                    dest_y = gy+box[1]+32-top
                    dest_x = gx+box[0]+7-left
                    assert not np.any(mask[dest_y, dest_x])
                    assert np.array_equal(a[dest_y, dest_x], b[dest_y, dest_x])
                    old_comp, new_comp = a.copy(), b.copy()
                    old_comp[dest_y, dest_x] = glyph[gy, gx]
                    new_comp[dest_y, dest_x] = glyph[gy, gx]
                    assert np.array_equal(old_comp[:, 5-left:], new_comp[:, 5-left:])
                    combinations += 1
                frames.append({
                    'frame': number, 'changed_pixels': int(np.count_nonzero(a != b)),
                    'symbol_layout': list(LAYOUTS[project][name]),
                    'source_opaque_pixels': int(np.count_nonzero(crop)),
                    'expanded_opaque_pixels': int(mask.sum()),
                    'expanded_centroid_x': float(xx.mean()+left),
                    'expanded_bbox_inclusive': [int(xx.min()+left), int(yy.min()+top), int(xx.max()+left), int(yy.max()+top)],
                    'expanded_pixel_center_nearest_exact': True,
                    'palette_index_set_preserved': sorted(map(int, np.unique(crop))),
                    'original_number_E_pixels': dark_count,
                    'original_E_mask_sha256': sha((native == 14).tobytes()),
                    'expanded_symbol_E_pixels_separate': int((layer == 14).sum()),
                    'symbol_does_not_overlap_native_E_or_digits': True,
                    'gauge_y21_and_above_preserved': True,
                    'existing_four_private_tiles_cover_entire_symbol': True,
                })
            bank_count = int.from_bytes(entry(before, 3)[:4], 'little')//4
            static = {1, 2, 3, 4, 6} if bank_count == 7 else {1, 2, 3, 4, *range(9, bank_count)}
            protected = 0
            for key, comp in comps.items():
                if key[0] not in static or key in TARGETS:
                    continue
                a, az, ab, _ = composed(ot, comp)
                b, bz, bb, _ = composed(nt, comp)
                assert az == bz and ab == bb and np.array_equal(a, b)
                protected += 1
            fresh, _ = maker.patch(before)
            assert fresh == after
            wrong = bytearray(before)
            wrong[-1] ^= 1
            try:
                maker.patch(bytes(wrong))
            except ValueError as error:
                assert str(error) == 'Unsupported source ARC'
                rejected.append(project+'/'+name+'/wrong_source')
            else:
                raise AssertionError('Wrong source accepted')
            resources[name] = {
                'before_sha256': sha(before), 'after_sha256': sha(after),
                'changed_tiles': sorted(changed), 'frames': frames,
                'all_nontexture_entries_and_layout_preserved': True,
                'CLUT_palette_coordinates_timing_audio_preserved': True,
                'other_tiles_identical': True, 'non_target_static_frames_identical': protected,
                'digit_composite_checks': combinations, 'reproduced_byte_identical': True,
            }
        results[project] = resources
    # Deliberately invalid placement, in-memory only, must not overwrite numeral E.
    before = sources['PL01_U.ARC']
    a, _, bounds = picture(before, 69)
    native, _, _ = picture(natives['PL01_U.ARC'], 69)
    symbol, _, _ = picture(symbols['PL01_U.ARC'], 69)
    saved = maker.CURRENT_LAYOUT
    try:
        maker.CURRENT_LAYOUT = (22, 19, -18, 23)
        try:
            maker.desired(a, native, symbol, bounds)
        except ValueError as error:
            assert str(error) == 'Enlarged symbol overlaps number aperture'
            rejected.append('Rin_22x19_at_minus18_overlaps_native_E')
        else:
            raise AssertionError('Numeral overlap accepted')
    finally:
        maker.CURRENT_LAYOUT = saved
    assert initial == fingerprints()
    assert all(digest(ROOT/p) == h for p, h in inputs.items())
    assert all(digest(ROOT/'scripts'/n) == h for n, h in code_hashes.items())
    report = {
        'passed': True, 'variant': 'larger_aligned_v6', 'resources': results,
        'HUD_frames': 54, 'digit_composite_checks': 540,
        'negative_cases_rejected': rejected, 'source_discs': inputs,
        'source_discs_prepared_files_production_code_unchanged': True,
        'original_number_E_counts': {'X_and_Ultimate': 51, 'Zero': 56},
        'approved_source_symbol_identity_and_index_colors_preserved': True,
        'comparison_png_viewed': True,
        'visual_assessment': '기존 심볼을 확대한 모양이 유지되며, 나나 과녁과 시부키/린 중심이 게이지 아래에 맞고 숫자칸은 가리지 않는다.',
        'runtime_verified': False, 'user_accepted': False,
        'limitations': ['정적/확대 미리보기 검증이며 실제 실행은 별도 runtime.json으로 기록한다.'],
        'writes': ['scripts/hud_larger_aligned_verify.py', 'work/hud_frame_fix_20261105/larger_aligned_v6/independent.json'],
    }
    (OUT/'independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps({'passed': True, 'frames': 54, 'digits': 540, 'negative_rejected': len(rejected)}))


if __name__ == '__main__':
    run()
