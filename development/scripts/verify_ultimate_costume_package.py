"""Check integrated proposal guards and protected files without writing a BIN."""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ultimate_costume_package import WORK, NAMES, SOURCES, validate_resources, sha, write_json
from scripts.c01_audio_build import read_disc, require
from scripts.discover_inputs import psx_arc
from scripts.ultimate_costume_renderer import off
from src.psx_disc import file_hash


def main():
    reports = {}
    for project, (source, expected) in SOURCES.items():
        require(file_hash(ROOT / source) == expected, 'Parent changed')
        old, _ = read_disc(ROOT / source, NAMES)
        folder = WORK / 'integrated_v1' / project
        proposal = json.loads((folder / 'proposal.json').read_text('utf8'))
        new = {n: (folder / n).read_bytes() for n in NAMES}
        require(validate_resources(old, new) == proposal['checks'], 'Integrated checks changed')
        for name in NAMES:
            require(sha(new[name]) == proposal['files'][name]['sha256'], 'Integrated bytes changed')
        cases = []
        def mutation(label, name, offset):
            data = dict(new); revised = bytearray(data[name]); revised[offset] ^= 1
            data[name] = bytes(revised); cases.append((label, data))
        entries = {int(e['type'], 16): e for e in psx_arc(old['PL02_U.ARC'])}
        mutation('player_palette', 'PL02_U.ARC', entries[9]['offset'] + 2)
        mutation('korean_dialogue', 'PL02_U.ARC', entries[0x15]['offset'] + 16)
        mutation('player_arc_header', 'PL02_U.ARC', 200)
        menu = old['MOJIPAT.ARC']; palettes = struct.unpack_from('<I', menu, 4)[0]
        mutation('black_zero_save_palette', 'MOJIPAT.ARC', palettes + 29 * 32 + 2)
        mutation('menu_other_bank', 'MOJIPAT.ARC', struct.unpack_from('<I', menu, 12)[0] + 4)
        load_entries = [e for e in psx_arc(old['LOAD_U.ARC']) if int(e['type'], 16) != 0x10008]
        mutation('unrelated_load_resource', 'LOAD_U.ARC', load_entries[0]['offset'])
        mutation('nova_ability_code', 'SLUS_005.61', off(0x800375D4))
        mutation('changed_renderer_proposal', 'SLUS_005.61', off(0x800257F8))
        mutation('changed_save_proposal', 'SLUS_005.61', off(0x8001BD20))
        truncated = dict(new); truncated['PL02_U.ARC'] = truncated['PL02_U.ARC'][:-1]
        cases.extend([('truncated_resource', truncated), ('extra_resource', {**new, 'unexpected': b'x'}),
                      ('missing_resource', {n: d for n, d in new.items() if n != 'MOJIPAT.ARC'})])
        rejected = []
        for label, invalid in cases:
            try:
                validate_resources(old, invalid)
            except ValueError:
                rejected.append(label)
            else:
                raise ValueError('Invalid resource set accepted: ' + label)
        reports[project] = {'all_prepared_hashes_verified': True, 'checks': proposal['checks'],
                            'rejected_mutations': rejected}
    protected = json.loads((WORK / 'protection/before.json').read_text('utf8'))['files']
    for name, record in protected.items():
        require(file_hash(ROOT / name) == record['sha256'], 'Protected file changed: ' + name)
    report = {'passed': True, 'projects': reports, 'protected_files_preserved': len(protected),
              'new_bin_created': False, 'current_pointers_unchanged': True,
              'cards_F1_unchanged': True, 'runtime_verified': False}
    write_json(WORK / 'integration_verification.json', report)
    print(json.dumps({'passed': True, 'rejected_mutations': sum(len(v['rejected_mutations']) for v in reports.values()),
                      'protected_files_preserved': len(protected), 'new_bin_created': False}))


if __name__ == '__main__':
    main()
