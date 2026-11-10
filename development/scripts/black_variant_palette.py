"""블랙 린의 적색/블랙 리코의 무채색 팔레트를 별도 BIN에 적용한다."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc, require
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from scripts.project import working_cue
from src.psx_disc import file_hash, write_archive_copies
from src.psx_sector import validate_checks

WORK = ROOT / 'work/black_variants_20261105'
NAMES = ('PL01_U.ARC', 'MOJIPAT.ARC')
BASES = {
    'ver_buki_riko': ('shibuki_riko', '6d9f0310be3df40b5000643a1b19d860cc6ebe4f8c476fb4150210ce189ecf88'),
    'ver_rin_nana': ('rin_nana', '0c019de65ea2b39e46cdd215d13f2d1de3a4cbda5aaac1567eecc16a83be4108'),
}
BUILDS = {'ver_buki_riko': 'black_monochrome_riko_20261105_v1',
          'ver_rin_nana': 'black_red_rin_20261105_v1'}
RIN_RGB5 = [
    (0, 0, 0), (5, 2, 4), (9, 4, 6), (14, 6, 8),
    (16, 1, 3), (28, 3, 5), (31, 11, 12), (15, 11, 14),
    (21, 17, 19), (27, 24, 25), (30, 28, 28), (31, 31, 31),
    (26, 18, 15), (31, 25, 19), (31, 28, 24), (31, 8, 12),
]
RIKO_GRAY5 = [0, 4, 9, 7, 10, 12, 15, 17, 20, 21, 23, 24, 26, 28, 29, 31]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')


def source(project):
    stem, expected = BASES[project]
    path = ROOT / 'out' / project / 'c01_x6_sfx_20261105_v1' / (stem + '.bin')
    require(file_hash(path) == expected, 'Unsupported source BIN')
    return path


def make_palette(project, normal):
    require(project in BASES and len(normal) == 32, 'Unexpected palette input')
    old = struct.unpack('<16H', normal)
    rgb = RIN_RGB5 if project == 'ver_rin_nana' else [(v, v, v) for v in RIKO_GRAY5]
    words = [(w & 0x8000) | r | g << 5 | b << 10 for w, (r, g, b) in zip(old, rgb)]
    require(words[0] == old[0] and all((a & 0x8000) == (b & 0x8000) for a, b in zip(old, words)),
            'Transparency/STP changed')
    require(len(set(words[1:])) == 15, 'Palette shades merged')
    if project == 'ver_rin_nana':
        require(words[11:15] == list(old[11:15]), 'White or skin colors changed')
    else:
        require(all((w & 31) == (w >> 5 & 31) == (w >> 10 & 31) for w in words), 'Non-achromatic color')
    return struct.pack('<16H', *words)


def ranges(assets):
    player = next(e for e in psx_arc(assets['PL01_U.ARC']) if int(e['type'], 16) == 9)
    require(player['size'] >= 14 * 32, 'Missing gameplay Black palette')
    menu_base = struct.unpack_from('<I', assets['MOJIPAT.ARC'], 4)[0]
    require(menu_base + 30 * 32 <= len(assets['MOJIPAT.ARC']), 'Missing save Black palette')
    return {'PL01_U.ARC': player['offset'] + 13 * 32, 'MOJIPAT.ARC': menu_base + 29 * 32}


def patch(project, assets):
    require(set(assets) == set(NAMES), 'Unexpected resource set')
    pal = entry(assets['PL01_U.ARC'], 9)
    normal = pal[:32]
    wanted = make_palette(project, normal)
    positions = ranges(assets)
    menu_base = struct.unpack_from('<I', assets['MOJIPAT.ARC'], 4)[0]
    require(assets['MOJIPAT.ARC'][menu_base + 10 * 32:menu_base + 11 * 32] == normal,
            'Save normal palette differs from player')
    new = {}
    for name, old in assets.items():
        at = positions[name]
        require(old[at:at + 32] == normal, 'Expected pre-variant normal-color Black palette')
        output = bytearray(old)
        output[at:at + 32] = wanted
        require(output[:at] == old[:at] and output[at + 32:] == old[at + 32:], 'Change outside authorized palette')
        new[name] = bytes(output)
    require(entry(new['PL01_U.ARC'], 9)[:32] == normal, 'Normal player changed')
    return new, {'normal_sha256': sha(normal), 'black_sha256': sha(wanted),
                 'normal_words': list(struct.unpack('<16H', normal)),
                 'black_words': list(struct.unpack('<16H', wanted)), 'positions': positions,
                 'normal_preserved': True, 'bitmaps_compositions_sound_code_preserved': True,
                 'transparent_index_and_STP_preserved': True, 'all15_shades_distinct': True,
                 'shared_effect_palettes_preserved': True}


def prepare():
    from scripts.overhaul_sprites_audit import render, rgba, board
    output = WORK / 'prepared_v1'
    require(not output.exists(), 'Prepared output already exists')
    plans, review = {}, []
    for project in BASES:
        path = source(project)
        assets, records = read_disc(path, NAMES)
        new, proof = patch(project, assets)
        require(patch(project, assets)[0] == new, 'Preparation not reproducible')
        rejected = []
        for label, bad in [('normal_source', dict(assets)), ('black_source', dict(assets)), ('already_applied', new)]:
            if label != 'already_applied':
                changed = bytearray(bad['PL01_U.ARC'])
                at = proof['positions']['PL01_U.ARC'] - (13 * 32 if label == 'normal_source' else 0)
                changed[at] ^= 1
                bad['PL01_U.ARC'] = bytes(changed)
            try:
                patch(project, bad)
            except ValueError:
                rejected.append(label)
        require(len(rejected) == 3, 'Invalid palette input accepted')
        proof['rejected_inputs'] = rejected
        folder = output / project
        files = {name: {'path': (folder / name).relative_to(ROOT).as_posix(),
                       'before': sha(assets[name]), 'after': sha(new[name]), 'record': records[name],
                       'changed_bytes': sum(a != b for a, b in zip(assets[name], new[name]))} for name in NAMES}
        plans[project] = (new, {'project': project, 'baseline': path.relative_to(ROOT).as_posix(),
                               'baseline_sha256': BASES[project][1], 'files': files, 'checks': proof})
        old_words = list(struct.unpack_from('<64H', entry(assets['PL01_U.ARC'], 9)))
        black_words = proof['black_words'] + old_words[16:]
        for label, words in [('normal', old_words), ('black', black_words)]:
            for frame in (147, 7, 20, 40, 229):
                indices, _ = render(assets['PL01_U.ARC'], 0, 0, frame)
                review.append((project.replace('ver_', '') + ' ' + label + ' ' + str(frame), rgba(indices, words)))
    output.mkdir(parents=True)
    for project, (assets, proposal) in plans.items():
        folder = output / project
        folder.mkdir()
        for name, content in assets.items():
            (folder / name).write_bytes(content)
        write_json(folder / 'proposal.json', proposal)
    board(review, output / 'palette_comparison.png', cols=5)
    write_json(output / 'summary.json', {p: q['checks'] for p, (_, q) in plans.items()})
    print(json.dumps({'prepared': str(output), 'projects': list(plans), 'source_only_read': True}))


def build(project, output):
    path = source(project)
    output = output.resolve()
    require(output.is_relative_to((ROOT / 'out' / project).resolve()) and not output.exists(), 'Fresh output required')
    assets, records = read_disc(path, NAMES)
    new, proof = patch(project, assets)
    proposal_path = WORK / 'prepared_v1' / project / 'proposal.json'
    proposal = json.loads(proposal_path.read_text('utf8'))
    require(proposal['checks'] == {**proof, 'rejected_inputs': ['normal_source', 'black_source', 'already_applied']},
            'Prepared palette specification differs')
    for name in NAMES:
        r = proposal['files'][name]
        require(sha(assets[name]) == r['before'] and sha(new[name]) == r['after'] and
                (ROOT / r['path']).read_bytes() == new[name], 'Prepared resource mismatch')
    output.mkdir(parents=True)
    stem, expected = BASES[project]
    target = output / (stem + '.bin')
    result = write_archive_copies(path, target,
        [({**records[n], 'sha256': sha(assets[n])}, new[n]) for n in NAMES], expected)
    changed = {s['lba'] for s in result['changed_sectors']}
    count = 0
    with path.open('rb') as original, target.open('rb') as revised:
        while old := original.read(2352):
            updated = revised.read(2352)
            require((old != updated) == (count in changed), 'Undeclared sector difference')
            if count in changed:
                validate_checks(updated)
            count += 1
        require(not revised.read(1), 'Disc size changed')
    require(read_disc(target, NAMES)[0] == new and file_hash(path) == expected, 'Readback/source preservation failed')
    (output / (stem + '.cue')).write_text(working_cue(path.with_suffix('.cue').read_text('ascii'), stem + '.bin'), 'ascii')
    report = {'project': project, 'task': 'black_variant_palette', 'parent_sha256': expected,
              'modified_bin': result, 'checks': proof, 'all_disc_sectors_compared': count,
              'all_other_sectors_unchanged': True, 'EDC_ECC_verified': True, 'readback_verified': True,
              'proposal': proposal_path.relative_to(ROOT).as_posix(), 'runtime_verified': False, 'user_accepted': False}
    write_json(output / 'manifest.json', report)
    print(json.dumps({'project': project, 'sha256': result['sha256'], 'changed_sectors': len(changed)}))


def activate():
    proof = json.loads((WORK / 'audit/independent.json').read_text('utf8'))
    require(proof['passed'], 'Independent validation required')
    destination = WORK / 'application'
    require(not destination.exists(), 'Already applied')
    protected = {
        'MegaMan X4.bin': '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
        'Rockman X4.bin': 'a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1',
        'out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin': '8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a',
    }
    preserve = [ROOT / 'projects/ver_buki_riko/final_release.json',
                ROOT / 'character/ver_buki_riko/riko(zero).webp', ROOT / 'character/ver_rin_nana/rin(zero).webp']
    for emulator in (ROOT / 'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator',
                     ROOT / 'work/ver_rin_nana/emulator'):
        preserve += list((emulator / 'memcards').glob('*.mcr'))
        preserve += list((emulator / 'sstates').glob('SLUS_005.61.000*'))
    for path in preserve:
        protected[path.relative_to(ROOT).as_posix()] = file_hash(path)
    for p, expected in protected.items():
        require(file_hash(ROOT / p) == expected, 'Protected input changed')
    pending = {}
    for project, (stem, expected) in BASES.items():
        folder = ROOT / 'projects' / project
        current = json.loads((folder / 'current_build.json').read_text('utf8'))
        config = json.loads((folder / 'project.json').read_text('utf8'))
        require(current['sha256'] == config['latest_integrated_bin_sha256'] == expected, 'Current source changed')
        build_dir = ROOT / 'out' / project / BUILDS[project]
        manifest = json.loads((build_dir / 'manifest.json').read_text('utf8'))
        digest = file_hash(build_dir / (stem + '.bin'))
        require(digest == manifest['modified_bin']['sha256'] == proof['projects'][project]['bin_sha256'],
                'Final build differs from independent result')
        require((build_dir / (stem + '.cue')).read_text('ascii') ==
                working_cue(source(project).with_suffix('.cue').read_text('ascii'), stem + '.bin'), 'CUE mismatch')
        policy = 'shared_bitmap_red_rin_palette' if project == 'ver_rin_nana' else 'shared_bitmap_achromatic_riko_palette'
        current.update(task='black_variant_palette', stage='BLACK_PALETTE_APPLIED_REVIEW',
                       build=build_dir.relative_to(ROOT).as_posix(),
                       cue=(build_dir / (stem + '.cue')).relative_to(ROOT).as_posix(), sha256=digest,
                       status_report='docs/BLACK_VARIANT_PALETTES.md', black_palette_report='docs/BLACK_VARIANT_PALETTES.md',
                       black_zero_policy=policy, black_palette_user_accepted=False, user_accepted=False,
                       previous_pointer=(destination / project / 'current_build.json').relative_to(ROOT).as_posix(),
                       current_runtime_state='Existing session preserved; new Black palette awaits fresh boot or authenticated checkpoint refresh',
                       runtime_verification_scope='Two full discs and exact palette-only changes verified; revised palette live testing pending',
                       next_action='Preserve current unsaved Black Rin before restarting; test new palette after fresh load')
        config.update(active_task='black_variant_palette', active_substage='BLACK_PALETTE_APPLIED_REVIEW',
                      latest_integrated_build=build_dir.relative_to(ROOT).as_posix(), latest_integrated_bin_sha256=digest,
                      black_zero_policy=policy)
        pending[project] = current, config
    destination.mkdir()
    for project in BASES:
        backup = destination / project
        backup.mkdir()
        for name in ('current_build.json', 'project.json'):
            shutil.copyfile(ROOT / 'projects' / project / name, backup / name)
    for project, (current, config) in pending.items():
        write_json(ROOT / 'projects' / project / 'current_build.json', current)
        write_json(ROOT / 'projects' / project / 'project.json', config)
    for p, expected in protected.items():
        require(file_hash(ROOT / p) == expected, 'Protected input changed after activation')
    result = {'passed': True, 'projects': {p: {'cue': c['cue'], 'bin_sha256': c['sha256']} for p, (c, _) in pending.items()},
              'protected_hashes': protected, 'active_F1_cards_written': False, 'live_process_written': False,
              'emulator_restarted': False, 'user_accepted': False}
    write_json(destination / 'applied.json', result)
    print(json.dumps({'applied': result['projects'], 'user_progress_preserved': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'activate'))
    parser.add_argument('--project', choices=BASES)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'activate':
        activate()
    else:
        require(args.project and args.output, 'Build needs project and output')
        build(args.project, args.output)
