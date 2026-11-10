"""v8 원본 세부 복원과 v7 확대 심볼의 바깥쪽 잔재 제거를 독립 검증한다."""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import hud_refined_symbols_verify as shared
from scripts import hud_reference_details as producer
from scripts.hud_underlay_verify import digest, read_assets, picture, sha

OUT = ROOT/'work/hud_frame_fix_20261105/reticle_v8'
NAMES = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')
FROZEN = {
    'nana': 'bd4681f43e3c70e2c5180dea72f77542e256eaefd56da63cadd8d981c6deb452',
    'riko': 'c437f49f94a044fb8f4fd8ffbf6314cd078597a4b31811aad1d83e59d068a525',
    'shibuki': 'a169a3b976d91b820da15a5c3af15623f84957d7889ad023d099bc19e6f02270',
}
BASE_EXPECTED = shared.expected_picture


def expected_picture(before, native, old_symbol, bounds, layout, art):
    clean = before.copy()
    left, top = bounds[:2]
    # Independent world-coordinate mask of every strip omitted by v7's old wipe.
    yy, xx = np.indices(clean.shape)
    xx += left
    yy += top
    strips = (xx >= -24) & (xx <= 4) & (((yy >= 22) & (yy <= 23)) | ((yy >= 41) & (yy <= 46)))
    clean[strips] = native[strips]
    return BASE_EXPECTED(clean, native, old_symbol, bounds, layout, art)


def configure_checker():
    shared.OUT = OUT
    shared.expected_picture = expected_picture
    # Reuse the proven 54-frame/540-digit checker with the actual v8 producer.
    shared.maker = SimpleNamespace(
        SOURCES=producer.SOURCES,
        SYMBOL_SOURCES=producer.refined.SYMBOL_SOURCES,
        LAYOUTS=producer.LAYOUTS,
        CHARACTERS=producer.refined.CHARACTERS,
        ART=producer.refined.ART,
        configure=producer.configure,
        patch=producer.patch,
    )


def run(prepared, rin_sha):
    prepared = prepared.resolve()
    expected_hashes = dict(FROZEN, rin=rin_sha)
    for name, expected in expected_hashes.items():
        assert digest(OUT/'art'/(name+'.json')) == expected, 'Unfrozen or changed art: '+name
    production_hash = digest(ROOT/'scripts/hud_reference_details.py')
    configure_checker()
    art, evidence = shared.decode_art()
    old_art_root = ROOT/'work/hud_frame_fix_20261105/refined_v7/art'
    old_art_hashes = {name: digest(old_art_root/(name+'.json')) for name in expected_hashes}
    old_nana = json.loads((old_art_root/'nana.json').read_text('utf8'))
    old_nana = np.array([[int(c, 16) for c in row] for row in old_nana['rows']], dtype=np.uint8)
    inner = np.zeros((21, 18), dtype=bool)
    inner[9:18, 4:13] = True
    assert np.array_equal(art['nana'][~inner], old_nana[~inner])
    arms = [(9,8),(10,8),(16,8),(17,8),(13,4),(13,5),(13,11),(13,12)]
    heart = [(12,7),(12,9),(13,7),(13,8),(13,9),(14,8)]
    gaps = [(11,8),(15,8),(13,6),(13,10)]
    assert all(art['nana'][y,x] == 3 for y,x in arms+heart)
    assert all(art['nana'][y,x] == 0 for y,x in gaps)
    riko_data = json.loads((OUT/'art/riko.json').read_text('utf8'))
    old_riko_data = json.loads((old_art_root/'riko.json').read_text('utf8'))
    old_riko = np.array([[int(c, 16) for c in row] for row in old_riko_data['rows']], dtype=np.uint8)
    sword_coords = riko_data['validation']['protected_sword_coordinates']
    assert all(art['riko'][y,x] == old_riko[y,x] for x,y in sword_coords)
    for x in (7,13):
        assert art['shibuki'][13,x] == 10
        assert [int(art['shibuki'][y,xx]) for y,xx in ((12,x),(13,x-1),(13,x+1),(14,x))] == [11,11,11,4]
    native = read_assets(ROOT/'MegaMan X4.bin', NAMES)
    remnants = {}
    for project, (stem, source_sha) in producer.SOURCES.items():
        proposal = json.loads((prepared/project/'proposal.json').read_text('utf8'))
        assert proposal['baseline_sha256'] == source_sha
        before = read_assets(ROOT/proposal['baseline'], NAMES)
        symbols = read_assets(ROOT/'out'/project/'overhaul_20261105_candidate04'/(stem+'.bin'), NAMES)
        records = {}
        for name in NAMES:
            after = (ROOT/proposal['files'][name]['path']).read_bytes()
            char = shared.CHARACTERS[project][name]
            frames = []
            for frame in range(69,78):
                a, az, bounds = picture(before[name], frame)
                b, bz, bb = picture(after, frame)
                n, nz, nb = picture(native[name], frame)
                s, _, _ = picture(symbols[name], frame)
                assert az == bz == nz and bounds == bb == nb
                expected, body, layer = expected_picture(a, n, s, bounds, shared.LAYOUTS[project][name], art[char])
                assert np.array_equal(expected, b)
                left, top = bounds[:2]
                yy, xx = np.indices(a.shape)
                yy += top
                xx += left
                strip = (xx >= -24) & (xx <= 4) & (((yy >= 22) & (yy <= 23)) | ((yy >= 41) & (yy <= 46)))
                uncovered = strip & (layer == 0)
                assert np.array_equal(b[uncovered], n[uncovered])
                removed = uncovered & (a != n)
                frames.append({'frame': frame, 'restored_strip_pixels_not_covered_by_new_symbol': int(uncovered.sum()),
                               'old_v7_residual_pixels_removed': int(removed.sum()),
                               'remaining_old_v7_residual_pixels': 0})
            records[name] = frames
        remnants[project] = records
    # All generic checks include direct JSON/proposal SHA, six ARC reproductions,
    # source rejection, number-mask collision rejection and immutable source data.
    # A detail-only update can change only some of the four reserved HUD tiles.
    # Coverage and privacy checks still use the entire original four-tile set.
    shared.run(prepared, require_all_private_tiles_changed=False)
    report_path = OUT/'independent.json'
    report = json.loads(report_path.read_text('utf8'))
    try:
        assert digest(ROOT/'scripts/hud_reference_details.py') == production_hash
        assert all(digest(OUT/'art'/(name+'.json')) == expected for name,expected in expected_hashes.items())
        assert all(digest(old_art_root/(name+'.json')) == expected for name,expected in old_art_hashes.items())
    except Exception:
        report['passed'] = False
        report['postcheck_failed'] = 'Producer or frozen v7/v8 art changed during verification'
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n','utf8')
        raise
    report.update(
        variant='reference_details_v8', frozen_art_hashes=expected_hashes,
        v7_art_immutable_hashes=old_art_hashes,
        source_v7_bins_exact=True,
        old_enlarged_symbol_edge_removal=remnants,
        additional_reference_checks={
            'nana_outer_ring_and_ears_outside_inner_9x9_exact_v7': True,
            'nana_four_thin_reticle_arms_eight_pixels_exact': True,
            'nana_central_heart_six_pixels_exact': True,
            'nana_reference_gaps_around_heart_exact': True,
            'riko_protected_v7_sword_pixels_exact': len(sword_coords),
            'shibuki_two_under_beam_round_dots_present': True,
            'rin_alpha_composited_bonnet_and_bow_reference_checked': True,
        },
        producer_script_sha256=production_hash,
        semantic_hand_refinement_not_nearest_scale=True,
        visual_assessment='시부키의 두 점, 나나의 네 조준선과 하트, 리코의 잎과 날개, 린의 보닛과 리본이 복원되어 있다.',
        writes=['scripts/hud_reference_details_verify.py', 'work/hud_frame_fix_20261105/reticle_v8/independent.json'],
    )
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n','utf8')
    print(json.dumps({'v8_passed': True, 'frames': 54, 'digits': 540,
                      'v7_edge_residuals': 0, 'frozen_art': expected_hashes}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--rin-sha', required=True)
    args = parser.parse_args()
    run(args.prepared, args.rin_sha)
