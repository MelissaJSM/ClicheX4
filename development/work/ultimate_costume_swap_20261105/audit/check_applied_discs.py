"""Independently verify full emitted discs against approved prepared bytes."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from src.psx_sector import rebuild_checks, validate_checks

OUT = Path(__file__).resolve().parent
EXPECTED = {
    'ver_buki_riko': ('shibuki_riko', 'bedba81a4c1263388835e10f57a8e30f6b7e9d9ac6f3f3d3dbf77821f4fb7c08', 58),
    'ver_rin_nana': ('rin_nana', 'b15be8bf18921f06c8e6713c0bdc51a22374764c7d59ec7fca29df97f2e742c1', 52),
}


def sha(b): return hashlib.sha256(b).hexdigest()


def disc_files(path, names):
    with path.open('rb') as f:
        reader = DiscReader(f, path.stat().st_size)
        records = {r['name'].split(';')[0]: r for r in reader.inspect()['files']}
        return ({n: reader.read(records[n]['lba'], records[n]['size']) for n in names},
                {n: records[n] for n in names})


def all_entries(before, after, allowed):
    old, new = psx_arc(before), psx_arc(after)
    assert [(e['type'], e['offset'], e['size']) for e in old] == [(e['type'], e['offset'], e['size']) for e in new]
    ranges = []
    protected, audio = [], []
    # Keep entry ordinal: two distinct VAB headers have the same type 0x6.
    for ordinal, e in enumerate(old):
        kind, start, end = int(e['type'], 16), e['offset'], e['offset'] + e['size']
        if kind in allowed:
            ranges.append((start, end))
        else:
            assert before[start:end] == after[start:end]
            row = dict(ordinal=ordinal, type=e['type'], size=e['size'], sha256=sha(after[start:end]))
            protected.append(row)
            if kind == 6 or kind >> 16 == 2:
                audio.append(row)
    assert len(before) == len(after)
    assert all(x == y or any(lo <= i < hi for lo, hi in ranges) for i, (x, y) in enumerate(zip(before, after)))
    return dict(all_non_target_entries_byte_identical=protected, audio_entries_including_duplicate_type6=audio,
                changed_bytes_only_in_allowed_entries=True)


def main():
    reports = {}
    for project, (stem, expected, expected_count) in EXPECTED.items():
        package_path = OUT.parent / 'integrated_v1' / project / 'proposal.json'
        package = json.loads(package_path.read_text('utf8'))
        parent = ROOT / package['source_bin']
        target_dir = ROOT / 'out' / project / 'ultimate_costumes_swapped_20261105_v1'
        target = target_dir / (stem + '.bin')
        # The writer's completed manifest is only a readiness marker; content
        # below is independently checked against package/source bytes.
        manifest = json.loads((target_dir / 'manifest.json').read_text('utf8'))
        assert target.stat().st_size == parent.stat().st_size == 251793 * 2352
        names = tuple(package['files']) + ('PL00_U.ARC', 'PL01_U.ARC')
        original, source_records = disc_files(parent, names)
        actual, target_records = disc_files(target, names)
        assert source_records == target_records
        replacements = {}
        readback = {}
        for name, row in package['files'].items():
            wanted = (ROOT / row['path']).read_bytes()
            assert sha(wanted) == row['sha256'] and actual[name] == wanted
            assert sha(original[name]) == row['source_sha256']
            assert row['record'] == source_records[name] and len(wanted) == row['size']
            start = row['record']['lba']
            for index in range(math.ceil(len(wanted) / 2048)):
                assert start + index not in replacements
                replacements[start + index] = wanted[index * 2048:(index + 1) * 2048]
            readback[name] = dict(sha256=sha(actual[name]), size=len(actual[name]),
                                  lba=target_records[name]['lba'], package_exact=True)
        source_hash, target_hash = hashlib.sha256(), hashlib.sha256()
        changed = []
        with parent.open('rb') as a, target.open('rb') as b:
            for lba in range(251793):
                left, right = a.read(2352), b.read(2352)
                assert len(left) == len(right) == 2352
                source_hash.update(left); target_hash.update(right)
                if lba in replacements:
                    block = replacements[lba]
                    expected_payload = block + left[24 + len(block):2072]
                    assert right[24:2072] == expected_payload
                if left != right:
                    assert lba in replacements
                    assert left[:24] == right[:24]
                    validate_checks(left)
                    validate_checks(right)
                    independent_expected = rebuild_checks(left[:24] + expected_payload + left[2072:])
                    assert right == independent_expected
                    changed.append(lba)
            assert not a.read(1) and not b.read(1)
        assert source_hash.hexdigest() == package['source_sha256']
        assert target_hash.hexdigest() == expected == manifest['modified_bin']['sha256']
        assert len(changed) == expected_count
        assert actual['PL00_U.ARC'] == original['PL00_U.ARC'] and actual['PL01_U.ARC'] == original['PL01_U.ARC']
        player = all_entries(original['PL02_U.ARC'], actual['PL02_U.ARC'], {2, 3})
        load = all_entries(original['LOAD_U.ARC'], actual['LOAD_U.ARC'], {0x10008})
        menu_before, menu_after = original['MOJIPAT.ARC'], actual['MOJIPAT.ARC']
        old_offsets, new_offsets = struct.unpack_from('<4I', menu_before), struct.unpack_from('<4I', menu_after)
        assert old_offsets == new_offsets
        start, end = old_offsets[1:3]
        assert menu_before[start:end] == menu_after[start:end]
        zero = actual['PL01_U.ARC']
        palettes = next(e for e in psx_arc(zero) if int(e['type'], 16) == 9)
        at = palettes['offset']
        black = zero[at + 13 * 32:at + 14 * 32]
        ui_black = menu_after[start + 29 * 32:start + 30 * 32]
        assert black == ui_black
        cue = target_dir / (stem + '.cue')
        assert cue.read_text('ascii') == parent.with_suffix('.cue').read_text('ascii')
        assert f'FILE "{stem}.bin" BINARY' in cue.read_text('ascii')
        reports[project] = dict(parent_bin=package['source_bin'], parent_sha256=source_hash.hexdigest(),
                                applied_bin=target.relative_to(ROOT).as_posix(), applied_sha256=target_hash.hexdigest(),
                                total_sectors_compared=251793, changed_sector_count=len(changed), changed_lbas=changed,
                                unchanged_sector_count=251793 - len(changed),
                                changed_source_and_target_EDC_ECC_checked=True,
                                changed_sector_headers_and_duplicate_subheaders_preserved=True,
                                all_changed_sectors_reconstructed_from_package_exact=True,
                                all_unrelated_sectors_including_XA_and_movies_byte_identical=True,
                                resource_readback=readback, original_lbas_sizes_preserved=True,
                                base_and_zero_player_archives_all_bytes_preserved=True,
                                ultimate_non_graphics=player, loading_non_atlas=load,
                                all_menu_palette_rows_byte_identical=True,
                                black_palette_gameplay_sha256=sha(black), black_palette_save_UI_sha256=sha(ui_black),
                                black_palette_design='achromatic Riko' if project == 'ver_buki_riko' else 'red Rin',
                                cue_layout_and_target_exact=True)
    report = dict(passed=True, projects=reports,
                  independent_sector_comparisons=503586,
                  scope='Actual completed BIN/CUE files; full raw-sector comparison, package readback, changed Form1 EDC/ECC, unchanged sound and black-palette verification.',
                  no_old_CPU_regression_repeated=True, runtime_verified=False,
                  game_original_pointer_save_card_or_emulator_written=False,
                  saves_cards_and_process_memory_accessed=False)
    (OUT / 'applied_discs.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'sectors_compared': 503586, 'changed': {p: r['changed_sector_count'] for p, r in reports.items()}}))


if __name__ == '__main__': main()
