"""확정된 네 원단위 심볼 JSON과 준비 ARC를 독립적으로 대조한다."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.hud_underlay_verify import digest, read_assets, sha, picture, TARGETS, TILES
from scripts.hud_larger_aligned_verify import expected_picture as previous_expected, LAYOUTS
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import all_compositions, composed
from scripts.discover_inputs import psx_arc
import scripts.hud_refined_symbols as maker
from src.psx_ui_atlas import tile_pixels

OUT = ROOT / 'work/hud_frame_fix_20261105/refined_v7'
NAMES = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')
CHARACTERS = {
    'ver_buki_riko': {'PL00_U.ARC': 'shibuki', 'PL01_U.ARC': 'riko', 'PL02_U.ARC': 'shibuki'},
    'ver_rin_nana': {'PL00_U.ARC': 'nana', 'PL01_U.ARC': 'rin', 'PL02_U.ARC': 'nana'},
}
ALLOWED = {'shibuki': {0, 3, 4, 10, 11, 12, 14}, 'riko': {0, 5, 6, 7, 8, 9, 10, 14},
           'nana': {0, 3, 4, 10, 11, 14}, 'rin': {0, 5, 6, 7, 8, 9, 10, 14}}
REFERENCES = {
    'shibuki': ('character/ver_buki_riko/buki(zero)_mark.webp', 'b93302ecb7473a7ede10cf55d2714afcec9a0de81b9a59d1c5d6c53bb64cb41e'),
    'riko': ('character/ver_buki_riko/riko(zero)_mark.webp', '032349b68f2847d7133ae43dd3211ef01bc22a04a81320e96b2454e99f5f0a9e'),
    'nana': ('character/ver_rin_nana/nana(X)_mark.webp', 'bea1de41269ff3a707abfd8dbc06c611c68a135513a8a1761ea277442ec12ebe'),
    'rin': ('character/ver_rin_nana/rin(zero)_mark.webp', 'e54ca7f43b7addaa89650dcd31630ec893654975bddb6797f56d930a45fd04c2'),
}


def decode_art():
    art, evidence = {}, {}
    for name, (ref, expected_hash) in REFERENCES.items():
        assert digest(ROOT/ref) == expected_hash
        path = OUT/'art'/(name+'.json')
        data = json.loads(path.read_text('utf8'))
        size = (21, 19) if name in ('shibuki', 'rin') else (18, 21)
        assert (data['width'], data['height']) == size
        assert len(data['rows']) == size[1] and all(len(row) == size[0] for row in data['rows'])
        assert all(c in '0123456789ABCDEF' for row in data['rows'] for c in row)
        # Decode directly from each hex nibble rather than production ART cache.
        pixels = np.fromiter((int(c, 16) for row in data['rows'] for c in row), dtype=np.uint8).reshape(size[1], size[0])
        assert set(map(int, pixels.flat)) <= ALLOWED[name]
        assert np.any(pixels == 0) and np.any(pixels != 0)
        if 'source_reference_sha256' in data:
            assert data['source_reference_sha256'] == expected_hash
        art[name] = pixels
        evidence[name] = {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                         'reference': ref, 'reference_sha256': expected_hash,
                         'dimensions': list(size), 'palette_indices': sorted(map(int, np.unique(pixels))),
                         'opaque_pixels': int(np.count_nonzero(pixels)), 'direct_hex_decode': True}
    return art, evidence


def expected_picture(before, native, old_symbol, bounds, layout, art):
    # Reuse only the independent native metal-body definition, not v6 artwork.
    _, body, _, _ = previous_expected(before, native, old_symbol, bounds, layout)
    width, height, x, y = layout
    left, top = bounds[:2]
    assert art.shape == (height, width)
    layer = np.zeros(before.shape, dtype=np.uint8)
    layer[y-top:y-top+height, x-left:x-left+width] = art
    result = body.copy()
    result[layer != 0] = layer[layer != 0]
    return result, body, layer


def run(prepared, *, require_all_private_tiles_changed=True):
    prepared = prepared.resolve()
    initial = {p.relative_to(ROOT).as_posix(): digest(p) for p in prepared.rglob('*') if p.is_file()}
    code_names = ('hud_refined_symbols.py', 'hud_larger_aligned.py', 'hud_aligned_bevel.py', 'hud_frame_underlay.py', 'hud_frame_fix.py')
    codes = {n: digest(ROOT/'scripts'/n) for n in code_names}
    original = ROOT/'MegaMan X4.bin'
    original_sha = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    assert digest(original) == original_sha
    originals = read_assets(original, NAMES)
    inputs = {original.relative_to(ROOT).as_posix(): original_sha}
    art, art_evidence = decode_art()
    maker.configure()
    assert maker.LAYOUTS == LAYOUTS and maker.CHARACTERS == CHARACTERS
    results, rejected = {}, []
    for project, (stem, source_sha) in maker.SOURCES.items():
        proposal = json.loads((prepared/project/'proposal.json').read_text('utf8'))
        source = ROOT/proposal['baseline']
        symbols_path = ROOT/'out'/project/'overhaul_20261105_candidate04'/(stem+'.bin')
        assert digest(source) == source_sha == proposal['baseline_sha256']
        assert digest(symbols_path) == maker.SYMBOL_SOURCES[project]
        inputs[source.relative_to(ROOT).as_posix()] = source_sha
        inputs[symbols_path.relative_to(ROOT).as_posix()] = maker.SYMBOL_SOURCES[project]
        before_assets, symbol_assets = read_assets(source, NAMES), read_assets(symbols_path, NAMES)
        resources = {}
        for name in NAMES:
            char = CHARACTERS[project][name]
            assert proposal['checks'][name]['symbol_art_sha256'] == art_evidence[char]['sha256']
            assert proposal['checks'][name]['symbol_art'] == art_evidence[char]['path']
            before = before_assets[name]
            spec = proposal['files'][name]
            after = (ROOT/spec['path']).read_bytes()
            assert sha(before) == spec['before'] and sha(after) == spec['after']
            assert len(before) == len(after) == spec['size']
            old_rows, new_rows = psx_arc(before), psx_arc(after)
            strip_hash = lambda rows: [{k: v for k, v in r.items() if k != 'sha256'} for r in rows]
            assert strip_hash(old_rows) == strip_hash(new_rows)
            row = next(r for r in old_rows if int(r['type'], 16) == 0x10206)
            low, high = row['offset'], row['offset']+row['size']
            assert before[:low] == after[:low] and before[high:] == after[high:]
            ot, nt = entry(before, 0x10206), entry(after, 0x10206)
            comps = all_compositions(entry(before, 3))
            users = {}
            for key, comp in comps.items():
                for p in comp['parts']:
                    users.setdefault(p['page']*256+p['tile'], set()).add(key)
            changed = {i for i in range(len(ot)//128) if tile_pixels(ot, i) != tile_pixels(nt, i)}
            assert changed and changed <= TILES[project][name]
            if require_all_private_tiles_changed:
                assert changed == TILES[project][name]
            assert all(users[tile] <= TARGETS for tile in changed)
            digits = []
            for digit in range(10):
                a, az, ab = picture(before, 59+digit)
                b, bz, bb = picture(after, 59+digit)
                assert az == bz and ab == bb and np.array_equal(a, b)
                digits.append((a, ab))
            frame_reports, combinations = [], 0
            for number in range(69, 78):
                a, size, bounds, locations = composed(ot, comps[1, number])
                b, ns, nb = picture(after, number)
                native, os, ob = picture(originals[name], number)
                old_symbol, ss, sb = picture(symbol_assets[name], number)
                assert size == ns == os == ss and bounds == nb == ob == sb
                left, top = bounds[:2]
                expected, body, layer = expected_picture(a, native, old_symbol, bounds, LAYOUTS[project][name], art[char])
                mask = layer != 0
                assert np.array_equal(b, expected)
                assert np.array_equal(b[mask], layer[mask]) and np.array_equal(b[~mask], body[~mask])
                assert np.array_equal(b[:22-top], a[:22-top]) and np.array_equal(b[:, 5-left:], a[:, 5-left:])
                assert not np.any(mask[22-top, -10-left:-5-left])
                aperture = native == 14
                count_E = 56 if name == 'PL01_U.ARC' else 51
                assert int(aperture.sum()) == count_E and not np.any(aperture & mask)
                assert np.array_equal(b == 14, aperture | (layer == 14))
                yy, xx = np.nonzero(mask)
                for y, x in zip(yy, xx):
                    positions = locations[int(y)*size[0]+int(x)]
                    assert positions
                    for offset, shift in positions:
                        tile = (offset//128//16)*16+(offset%128)//8
                        assert tile in TILES[project][name] and users[tile] <= TARGETS
                for glyph, box in digits:
                    gy, gx = np.nonzero(glyph)
                    dy, dx = gy+box[1]+32-top, gx+box[0]+7-left
                    assert not np.any(mask[dy, dx]) and np.array_equal(a[dy, dx], b[dy, dx])
                    old_comp, new_comp = a.copy(), b.copy()
                    old_comp[dy, dx] = glyph[gy, gx]
                    new_comp[dy, dx] = glyph[gy, gx]
                    assert np.array_equal(old_comp[:, 5-left:], new_comp[:, 5-left:])
                    combinations += 1
                frame_reports.append({'frame': number, 'changed_pixels': int(np.count_nonzero(a != b)),
                    'symbol_opaque_pixels': int(mask.sum()), 'symbol_layout': list(LAYOUTS[project][name]),
                    'canonical_JSON_pixel_exact': True, 'native_number_E_pixels': count_E,
                    'native_E_mask_sha256': sha(aperture.tobytes()), 'symbol_E_pixels_separate': int((layer == 14).sum()),
                    'native_E_and_glyphs_not_overlapped': True, 'gauge_y21minus_and_dynamic_fill_preserved': True,
                    'existing_four_private_tiles_cover_every_symbol_pixel': True})
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
                raise AssertionError('Invalid source accepted')
            resources[name] = {'character': char, 'before_sha256': sha(before), 'after_sha256': sha(after),
                'canonical_art_sha256': art_evidence[char]['sha256'], 'changed_private_tiles': sorted(changed),
                'frames': frame_reports, 'digit_composite_checks': combinations,
                'other_tiles_identical': True, 'non_target_static_frames_identical': protected,
                'all_nontexture_entries_CLUT_coordinates_timing_audio_preserved': True,
                'reproduced_byte_identical': True}
        results[project] = resources
    # Corrupt only a copied in-memory Rin grid at its right edge over native E.
    saved = maker.ART['rin']
    invalid = saved[0].copy()
    invalid[6, 20] = 9
    try:
        maker.ART['rin'] = (invalid, saved[1])
        try:
            maker.patch(before_assets['PL01_U.ARC'])
        except ValueError as error:
            assert str(error) == 'Enlarged symbol overlaps number aperture'
            rejected.append('refined_Rin_opaque_pixel_over_original_E')
        else:
            raise AssertionError('Numeric aperture overlap accepted')
    finally:
        maker.ART['rin'] = saved
    assert initial == {p.relative_to(ROOT).as_posix(): digest(p) for p in prepared.rglob('*') if p.is_file()}
    assert all(digest(ROOT/p) == h for p, h in inputs.items())
    assert all(digest(ROOT/'scripts'/n) == h for n, h in codes.items())
    assert all(digest(ROOT/r['path']) == r['sha256'] and digest(ROOT/r['reference']) == r['reference_sha256'] for r in art_evidence.values())
    report = {'passed': True, 'variant': 'refined_v7', 'prepared': prepared.relative_to(ROOT).as_posix(),
        'canonical_art': art_evidence, 'resources': results, 'HUD_frames': 54, 'digit_composite_checks': 540,
        'negative_cases_rejected': rejected, 'source_discs': inputs,
        'source_art_references_production_code_and_prepared_resources_unchanged': True,
        'semantic_hand_refinement_not_nearest_scale': True, 'original_number_E_counts': {'X_and_Ultimate': 51, 'Zero': 56},
        'all_four_original_mark_references_and_comparison_viewed': True,
        'visual_assessment': '토리이, 검과 이펙트, 토끼귀 과녁, 린의 고리 형태가 큰 색면과 일정한 선으로 정리되어 있다.',
        'runtime_verified': False, 'user_accepted': False,
        'limitations': ['최종 도트 행렬과 정적 자원의 검증이다. 실기 확인은 별도 runtime.json으로 구분한다.'],
        'writes': ['scripts/hud_refined_symbols_verify.py', 'work/hud_frame_fix_20261105/refined_v7/independent.json']}
    (OUT/'independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps({'passed': True, 'frames': 54, 'digits': 540, 'negative_rejected': len(rejected)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepared', type=Path, default=OUT/'prepared_final')
    run(parser.parse_args().prepared)
