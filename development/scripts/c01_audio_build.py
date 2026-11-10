"""C-01 비음성 효과 제안을 검증하고 별도 두 모드 BIN을 만든다."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.inventory_riko_voice import parse_bank
from scripts.project import working_cue
from src.psx_disc import write_archive_copies, file_hash
from src.psx_sector import validate_checks

WORK = ROOT / 'work/audio_c01_revision_20261105'
NAMES = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')
BASES = {
    'ver_buki_riko': ('shibuki_riko', '15b6eec0ff23decff4f42133e20f0d0b33efed40c4ecf3f245905ef2a5357aea'),
    'ver_rin_nana': ('rin_nana', '8c5c7ba9bb2fd6d04080db453c2890c6446350fe19b896013661dc97b21b5bc1'),
}
SOUNDS = {
    'hurt': ('3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029', 59, 83, 90, 0, 1),
    'death': ('bca9ec5b6b47b1247ec483f6b95cb8de3d94c58e03132255c63df5f434e4cfbc', 60, 80, 100, 1, 2),
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_disc(path, names):
    with path.open('rb') as stream:
        reader = DiscReader(stream, path.stat().st_size)
        records = {r['name'].split(';')[0]: r for r in reader.inspect()['files']
                   if r['name'].split(';')[0] in names and not r['directory']}
        require(set(records) == set(names), 'Missing disc resources')
        return {n: reader.read(r['lba'], r['size']) for n, r in records.items()}, records


def get_bank(arc, slot):
    entries = psx_arc(arc)
    found = []
    for i, e in enumerate(entries[:-1]):
        h = arc[e['offset']:e['offset'] + e['size']]
        be = entries[i + 1]
        body = arc[be['offset']:be['offset'] + be['size']]
        try:
            parsed = parse_bank(h, body, False)
        except (ValueError, struct.error, IndexError):
            continue
        if parsed['slot'] == slot:
            found.append((h, body, parsed, e, be))
    require(len(found) == 1, 'Ambiguous sound bank')
    return found[0]


def check_arc(before, after):
    layout = lambda arc: [(e['type'], e['offset'], e['size']) for e in psx_arc(arc)]
    require(len(before) == len(after) and layout(before) == layout(after), 'ARC layout changed')
    h, b, q, he, be = get_bank(before, 3)
    nh, nb, nq, _, _ = get_bank(after, 3)
    mask = bytearray(len(before))
    for e in (he, be):
        mask[e['offset']:e['offset'] + e['size']] = bytes([1]) * e['size']
    require(all(x == y or mask[i] for i, (x, y) in enumerate(zip(before, after))),
            'Non-player audio/graphics/UI/code changed')
    for key in ('slot', 'vab_offset', 'body_bytes', 'program_count', 'tone_count', 'wave_count', 'command_count'):
        require(q[key] == nq[key], 'Bank metadata changed: ' + key)
    require(q['program_count'] == 1 and q['tone_count'] == 16 and q['command_count'] == 13,
            'Unsupported player bank')
    tone_base = q['vab_offset'] + 32 + 128 * 16
    require(h[q['vab_offset']:tone_base] == nh[q['vab_offset']:tone_base],
            'VAB master/header/program records changed')
    require(h[tone_base + 2 * 32:tone_base + 16 * 32] == nh[tone_base + 2 * 32:tone_base + 16 * 32],
            'Unrelated muted-player/Peacock tones changed')
    for w, nw in zip(q['waves'][-2:], nq['waves'][-2:]):
        require(w == nw, 'Restored Peacock waveform or SPU address changed')
        start, end = w['body_offset'], w['body_offset'] + w['bytes']
        require(b[start:end] == nb[start:end], 'Restored Peacock payload changed')
    for command in range(13):
        if command not in (0, 1, 12):
            require(h[8 + command * 4:12 + command * 4] == nh[8 + command * 4:12 + command * 4],
                    'Unrelated protagonist command changed')
    return {'changed_bytes': sum(x != y for x, y in zip(before, after)),
            'only_bank3_changed': True, 'ARC_layout_preserved': True,
            'Peacock_tones_waves_and_addresses_preserved': True,
            'other_commands_preserved': True}


def verify_native(project, old, new, source):
    # The established harness runs the real X4 command decoder; SPU SDK is mocked.
    from scripts.overhaul_audio_verify_cpu import banks, run
    assets, _ = read_disc(source, ('SLUS_005.61', 'ST6_1_1.ARC', 'ONPARE6.ARC'))
    exe = assets['SLUS_005.61']
    rows = []
    for name in NAMES:
        previous, loaded = banks(old[name]), banks(new[name])
        for command in range(13):
            calls = run(exe, loaded, 3, command)
            require(bool(calls), 'No native sound call')
            if command in (0, 1, 12):
                expected_hash, note, center, volume, tone, wave = SOUNDS['death' if command == 12 else 'hurt']
                require(len(calls) == 1 and all(c['bank'] == 3 and c['channel'] == 20 and c['pcm_nonzero']
                            and c['tone'] == tone and c['wave'] == wave and c['left'] > 0 and c['right'] > 0
                            and c['wave_sha256'] == expected_hash and c['note'] == note and c['center'] == center
                            and c['fine'] == 0 and c['tone_volume'] == volume for c in calls),
                        'C01 native call did not reach dedicated audible samples')
            elif command == 10 and name == 'PL01_U.ARC':
                require(calls == run(exe, previous, 3, command), 'Rakuhouha effect changed')
            else:
                require(all(c['bank'] == 3 and not c['pcm_nonzero'] for c in calls),
                        'Protagonist voice no longer muted')
            rows.append({'player': name, 'command': command, 'calls': calls})
        for boss in ('ST6_1_1.ARC', 'ONPARE6.ARC'):
            for command in (196, 199):
                calls = run(exe, {**loaded, **banks(assets[boss])}, 2, command)
                prior = run(exe, {**previous, **banks(assets[boss])}, 2, command)
                require(calls == prior and calls and all(c['pcm_nonzero'] for c in calls),
                        'Restored boss call changed')
                rows.append({'player': name, 'boss': boss, 'command': command, 'calls': calls})
    return {'project': project, 'passed': True, 'cases': rows,
            'native_X4_dispatcher_executed': True, 'SPU_SDK_mocked': True,
            'actual_game_verified': False, 'listening_verified': False}


def build(project, proposal_path, output, verify_only=False):
    stem, expected = BASES[project]
    source = ROOT / 'out' / project / 'selection_unified_20261105_v4' / (stem + '.bin')
    proposal_path, output = proposal_path.resolve(), output.resolve()
    require(proposal_path.is_relative_to(WORK.resolve()), 'Unexpected proposal path')
    require(output.is_relative_to((ROOT / 'out' / project).resolve()) and
            (output.is_dir() if verify_only else not output.exists()), 'Unexpected output directory')
    require(file_hash(source) == expected, 'Unsupported base image')
    proposal = json.loads(proposal_path.read_text('utf8'))
    require(proposal['project'] == project and proposal['baseline_sha256'] == expected,
            'Wrong proposal source')
    require(set(proposal['files']) == set(NAMES), 'Unexpected replacement set')
    old, records = read_disc(source, NAMES)
    new, checks = {}, {}
    for name in NAMES:
        r = proposal['files'][name]
        path = (ROOT / r['path']).resolve()
        require(path.is_relative_to(WORK.resolve()), 'Unexpected prepared resource')
        new[name] = path.read_bytes()
        require(sha(old[name]) == r['before'] and sha(new[name]) == r['after'], 'Proposal hash mismatch')
        checks[name] = check_arc(old[name], new[name])
    cpu = verify_native(project, old, new, source)
    if verify_only:
        target = output / (stem + '.bin')
        manifest = json.loads((output / 'manifest.json').read_text('utf8'))
        require(file_hash(target) == manifest['modified_bin']['sha256'], 'Existing BIN hash mismatch')
        require(read_disc(target, NAMES)[0] == new, 'Existing BIN resource mismatch')
        result = {'passed': True, 'checks': checks, 'native_cases': len(cpu['cases']),
                  'bin_sha256': manifest['modified_bin']['sha256'],
                  'exact_X6_wave_note_center_volume_checked': True, 'VAB_master_program_preserved': True}
        proof = output / 'post_review_verification.json'
        require(not proof.exists(), 'Review already recorded')
        proof.write_text(json.dumps(result, indent=2) + '\n', 'utf8')
        print(json.dumps(result))
        return
    output.mkdir(parents=True)
    target = output / (stem + '.bin')
    result = write_archive_copies(source, target,
        [({**records[n], 'sha256': sha(old[n])}, new[n]) for n in NAMES], expected)
    changed = {r['lba'] for r in result['changed_sectors']}
    count = 0
    with source.open('rb') as a, target.open('rb') as b:
        while before := a.read(2352):
            after = b.read(2352)
            require((before != after) == (count in changed), 'Undeclared sector difference')
            if count in changed:
                validate_checks(after)
            count += 1
        require(not b.read(1), 'Disc length changed')
    readback, _ = read_disc(target, NAMES)
    require(readback == new and file_hash(source) == expected, 'Readback/preservation failed')
    (output / (stem + '.cue')).write_text(working_cue(source.with_suffix('.cue').read_text('ascii'), stem + '.bin'), 'ascii')
    (output / 'cpu_verification.json').write_text(json.dumps(cpu, indent=2) + '\n', 'utf8')
    report = {'project': project, 'task': 'c01_nonvoice_sfx_revision', 'parent_sha256': expected,
              'modified_bin': result, 'checks': checks, 'all_disc_sectors_compared': count,
              'all_unrelated_sectors_identical': True, 'EDC_ECC_verified': True,
              'disc_readback_verified': True, 'proposal': proposal_path.relative_to(ROOT).as_posix(),
              'runtime_verified': False, 'user_accepted': False}
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', 'utf8')
    print(json.dumps({'project': project, 'sha256': result['sha256'], 'changed_sectors': len(changed),
                      'native_checks': len(cpu['cases']), 'output': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', choices=BASES, required=True)
    parser.add_argument('--proposal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    build(args.project, args.proposal, args.output, args.verify_only)
