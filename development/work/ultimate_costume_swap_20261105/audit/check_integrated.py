"""Independent integrated resource audit, without invoking integration code."""
import hashlib
import json
import struct
from pathlib import Path
from native_contracts import ROOT
from check_special import entries, compose, full, records, SPECIAL, SKIP
from scripts.overhaul_nana_buffer_watch import cpu_checks
from scripts.overhaul_audio_final_audit import ladder_decoder
from src.psx_player import graphics_bank, bank_offsets, composition_frame, decode_stream

OUT = Path(__file__).resolve().parent
TASK = OUT.parent
ARRIVAL = set(range(133, 138))


def sha(b): return hashlib.sha256(b).hexdigest()
def off(at): return at - 0x80010000 + 2048


def main():
    reports = {}
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        folder = TASK / 'integrated_v1' / project
        proposal = json.loads((folder / 'proposal.json').read_text('utf8'))
        data = {n: (ROOT / r['path']).read_bytes() for n, r in proposal['files'].items()}
        for n, row in proposal['files'].items(): assert sha(data[n]) == row['sha256'] and len(data[n]) == row['size']
        source = (OUT / project / 'source_PL02_U.ARC').read_bytes()
        a = entries(source)
        b = entries(data['PL02_U.ARC'])
        complete = entries((TASK / 'core/prepared_complete_v1' / project / 'PL02_U.ARC').read_bytes())
        special = entries((TASK / 'core/prepared_special_v1' / project / 'PL02_U.ARC').read_bytes())
        capsule = entries((TASK / 'ui/capsules_v1' / project / 'PL02_U.ARC').read_bytes())
        assert set(a) == set(b) and all(a[k] == b[k] for k in a if k not in (2, 3))
        assert bank_offsets(a[2], allow_aliases=True) == bank_offsets(b[2], allow_aliases=True)
        assert bank_offsets(a[3]) == bank_offsets(b[3])
        untouched = 0
        caps_checked = 0
        for bank in range(len(bank_offsets(a[2], allow_aliases=True))):
            old, new = graphics_bank(a[2], bank, allow_bank_aliases=True), graphics_bank(b[2], bank, allow_bank_aliases=True)
            assert (old['base'], old['end'], len(old['frames'])) == (new['base'], new['end'], len(new['frames']))
            expected_entry = capsule[2] if bank in range(10, 14) else complete[2]
            assert b[2][new['base']:new['end']] == expected_entry[new['base']:new['end']]
            for of, nf in zip(old['frames'], new['frames']):
                left = decode_stream(a[2], of['offset'], of['limit'], of['tile_count'] * 128).data
                right = decode_stream(b[2], nf['offset'], nf['limit'], nf['tile_count'] * 128).data
                if bank == 0 and of['index'] in SPECIAL | ARRIVAL:
                    continue
                if bank in range(10, 14):
                    ref = graphics_bank(capsule[2], bank, allow_bank_aliases=True)['frames'][of['index']]
                    assert right == decode_stream(capsule[2], ref['offset'], ref['limit'], ref['tile_count'] * 128).data
                    caps_checked += 1
                else:
                    assert left == right
                    untouched += 1
        for bank in range(len(bank_offsets(a[3]))):
            offsets = bank_offsets(b[3]) + [len(b[3])]
            start, end = offsets[bank:bank + 2]
            expected = capsule[3] if bank in range(18, 22) else complete[3]
            assert b[3][start:end] == expected[start:end]
            count = composition_frame(a[3], bank, 0)['bank_frame_count']
            assert composition_frame(b[3], bank, 0)['bank_frame_count'] == count
            for n in range(count):
                allowed = bank in range(18, 22) or bank in (0, 5) and n in SPECIAL or bank == 5 and n in ARRIVAL
                if not allowed: assert records(a, bank, n) == records(b, bank, n)
        same_pre, same_full = 0, 0
        for n in range(237):
            if n in SKIP: continue
            if n not in SPECIAL:
                assert compose(a, n, 0).tobytes() == compose(b, n, 0).tobytes()
                same_pre += 1
            if n not in SPECIAL | ARRIVAL:
                assert full(a, n).tobytes() == full(b, n).tobytes()
                same_full += 1
            if n in SPECIAL:
                assert full(special, n).tobytes() == full(b, n).tobytes()
                assert compose(special, n, 0).tobytes() == compose(b, n, 0).tobytes()
            if n in ARRIVAL:
                assert full(complete, n).tobytes() == full(b, n).tobytes()
                assert records(a, 0, n) == records(b, 0, n)
        exe = data['SLUS_005.61']
        old_exe = (TASK / 'renderer' / (project + '.exe')).read_bytes()
        renderer = (TASK / 'renderer' / (project + '.renderer.exe')).read_bytes()
        save = (TASK / 'ui/prepared_v1' / project / 'SLUS_005.61').read_bytes()
        expected = bytearray(old_exe)
        expected[off(0x800257BC):off(0x8002588C)] = renderer[off(0x800257BC):off(0x8002588C)]
        for lo, hi in ((0x8001BD1C, 0x8001BD9C), (0x8001BE60, 0x8001BE64)):
            expected[off(lo):off(hi)] = save[off(lo):off(hi)]
        assert exe == bytes(expected)
        assert sum(x != y for x, y in zip(exe, old_exe)) == 265
        for name in ('MOJIPAT.ARC', 'LOAD_U.ARC'):
            assert data[name] == (TASK / 'ui/prepared_v1' / project / name).read_bytes()
        bank = graphics_bank(b[2], 0, allow_bank_aliases=True)
        native = []
        for n in sorted(ARRIVAL):
            fr = bank['frames'][n]
            observed = ladder_decoder(exe, b[2], fr, True)
            plain = ladder_decoder(exe, b[2], fr, False)
            assert observed == plain
            native.append(observed)
        assert max(f['tile_count'] for f in bank['frames']) == 32
        # The wrapper uses the final integrated EXE as well as its final ARC.
        selected = {f['index']: (f, decode_stream(b[2], f['offset'], f['limit'], f['tile_count'] * 128).data) for f in bank['frames'] if f['index'] in ARRIVAL | SPECIAL}
        wrapper = cpu_checks(exe, b, bank, selected)
        for n, row in proposal['files'].items(): assert sha((ROOT / row['path']).read_bytes()) == row['sha256']
        reports[project] = dict(resource_hashes={n: sha(v) for n, v in data.items()},
                               original_graphics_references_preserved=untouched,
                               capsule48_matches_separate_prepared_resource=caps_checked,
                               unchanged_pre_RGBA_frames=same_pre, unchanged_full_RGBA_frames=same_full,
                               original_arrival5_base_pixels_and_composition_exact=True,
                               special14_matches_previous_independent_review=True,
                               arrival5_matches_final_core=True,
                               palette_audio_animation_all_other_entries_exact=True,
                               all_bank_boundaries_and_allocations_fixed=True,
                               menu_load_equals_independently_checked_UI=True,
                               exe265bytes_exact_union_of_independently_checked_code=True,
                               max_main_tiles=32, native_arrival_decoder_checks=native,
                               native_final_wrapper_checks=wrapper)
    report = dict(passed=True, projects=reports,
                  source_game_or_pointer_written=False, new_BIN_created=False,
                  actual_emulator_run=False,
                  visual_review='Both arrival_review.png sheets viewed; new jacket overlays are newly prepared costume pieces, while original body and effect poses are retained.',
                  limitations=['The actual disc has not been built or executed.', 'Menu constructor ABI and primitive/header selection evidence are separate linked audits.', 'New arrival clothing and the final swapped look still require the user review.'])
    (OUT / 'integrated_independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'projects': list(reports), 'capsule_refs': sum(x['capsule48_matches_separate_prepared_resource'] for x in reports.values())}))


if __name__ == '__main__': main()
