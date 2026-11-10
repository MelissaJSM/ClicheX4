"""C-09: align the separate attract-demo logo with the loading logo."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.overhaul_ui_inventory import BUILDS, D, load
from scripts.overhaul_ui_fixes import loading, require
from scripts.discover_inputs import sha256
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition

TABLE_ADDRESS = 0x8010E6D0
TABLE_OFFSET = 0xFEED0
EXPECTED_X = (160, 160, 96, 208, 256, 0)
EXPECTED_Y = (120, 120, 112, 192, 192, 0)


def demo_logo(exe):
    require(struct.unpack_from('<I', exe, 0x18)[0] == 0x80010000,
            'Unexpected executable load address')
    require(struct.unpack_from('<6h', exe, TABLE_OFFSET) == EXPECTED_X,
            'Unexpected demo X table')
    require(struct.unpack_from('<6h', exe, TABLE_OFFSET + 12) == EXPECTED_Y,
            'Unexpected demo Y table')
    out = bytearray(exe)
    struct.pack_into('<hh', out, TABLE_OFFSET + 6, 184, 232)
    edits = [{'offset': i, 'before': a, 'after': b}
             for i, (a, b) in enumerate(zip(exe, out)) if a != b]
    require([x['offset'] for x in edits] == [0xFEED6, 0xFEED8, 0xFEED9],
            'Unexpected demo edit scope')
    return bytes(out), {
        'x_table_address': hex(TABLE_ADDRESS),
        'before_x': [208, 256], 'after_x': [184, 232],
        'shift_x': -24, 'y': 192, 'width': 112,
        'right_margin_before': 0, 'right_margin_after': 24,
        'object_id': 18, 'object_subtypes': [3, 4],
        'initializer': '0x800CB048', 'x_table_load': '0x800CB0F8',
        'exe_data_edits': edits,
        'instructions_uv_palette_timing_other_coords_exact': True,
    }


def prepare(out):
    out = out.resolve()
    require(out.is_relative_to(D) and not out.exists(), 'Fresh UI output required')
    out.mkdir(parents=True)
    checks = {'passed': True, 'resources_reproduced': 0, 'negative_cases': 0,
              'loading_delta_conflicts': 0, 'runtime_verified': False}
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        old, records = load(project)
        before = old['SLUS_005.61']
        after, proof = demo_logo(before)
        reproduced, repeat_proof = demo_logo(before)
        require(reproduced == after and repeat_proof == proof, 'Reproduction differs')
        checks['resources_reproduced'] += 1
        altered = bytearray(before)
        altered[TABLE_OFFSET + 6] ^= 1
        try:
            demo_logo(bytes(altered))
        except ValueError:
            checks['negative_cases'] += 1
        else:
            raise ValueError('Corrupt demo table was accepted')
        load_after, _ = loading(before)
        require(not any(a != b and a != c for a, b, c in zip(before, after, load_after)),
                'Demo and loading patches conflict')
        bounds = {}
        for name, bank in (('PL00_U.ARC', 9), ('PL01_U.ARC', 4), ('PL02_U.ARC', 9)):
            frames = []
            for frame in (1, 2):
                c = aliased_composition(entry(old[name], 3), bank, frame)
                bb = (min(p['x'] for p in c['parts']), min(p['y'] for p in c['parts']),
                      max(p['x'] + 16 for p in c['parts']), max(p['y'] + 16 for p in c['parts']))
                require(bb == (0, 0, 80 if frame == 1 else 64, 32),
                        'Demo composition extent changed')
                frames.append({'frame': frame, 'bounds': list(bb)})
            bounds[name] = {'bank': bank, 'frames': frames}
        proof['player_compositions'] = bounds
        folder = out / project
        folder.mkdir()
        path = folder / 'SLUS_005.61'
        path.write_bytes(after)
        proposal = {
            'project': project, 'baseline': BUILDS[project][0],
            'baseline_sha256': BUILDS[project][1],
            'files': {'SLUS_005.61': {
                'before': sha256(before), 'after': sha256(after), 'size': len(after),
                'path': path.relative_to(ROOT).as_posix(), 'record': records['SLUS_005.61'],
                'changed_bytes': 3}},
            'issues': ['C-09'], 'checks': proof, 'runtime_verified': False,
        }
        (folder / 'proposal.json').write_text(json.dumps(proposal, indent=2) + '\n', 'utf8')
    (out / 'verification.json').write_text(json.dumps(checks, indent=2) + '\n', 'utf8')
    print(str(out))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True, type=Path)
    prepare(p.parse_args().output)
