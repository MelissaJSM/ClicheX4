"""Integrate reviewed resources; disc writing is a separate explicit command.

The prepare command writes only a review package. Apply the new executable
display method to a BIN only after the project's required user confirmation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc, require
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from scripts.project import working_cue
from scripts.ultimate_costume_renderer import patch_executable, off, START, END
from scripts.ultimate_costume_swap_ui import SOURCES, prepare_capsules, patch_save_executable, SAVE_BEGIN, SAVE_END
from src.psx_disc import file_hash, write_archive_copies
from src.psx_sector import validate_checks

WORK = ROOT / 'work/ultimate_costume_swap_20261105'
NAMES = ('PL02_U.ARC', 'MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61')
STEMS = {'ver_buki_riko': 'shibuki_riko', 'ver_rin_nana': 'rin_nana'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')


def safe_work_file(relative):
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(WORK.resolve()) and path.is_file(), 'Resource outside task workspace')
    return path


def validate_resources(old, new):
    require(set(old) == set(new) == set(NAMES), 'Unexpected integrated resource set')
    for name in NAMES:
        require(len(old[name]) == len(new[name]), 'Resource allocation changed: ' + name)
    for name, allowed_types in (('PL02_U.ARC', {2, 3}), ('LOAD_U.ARC', {0x10008})):
        layout = lambda b: [(e['type'], e['offset'], e['size']) for e in psx_arc(b)]
        require(layout(old[name]) == layout(new[name]), 'ARC entries relocated: ' + name)
        allowed = []
        for e in psx_arc(old[name]):
            if int(e['type'], 16) in allowed_types:
                allowed.append((e['offset'], e['offset'] + e['size']))
            else:
                require(entry(old[name], int(e['type'], 16)) == entry(new[name], int(e['type'], 16)),
                        'Non-graphic entry changed: ' + name + '/' + e['type'])
        require(all(x == y or any(a <= p < b for a, b in allowed)
                    for p, (x, y) in enumerate(zip(old[name], new[name]))),
                'Mutation escaped graphics entries: ' + name)
    menu = old['MOJIPAT.ARC']
    require(struct.unpack_from('<I', menu)[0] == 16, 'Unexpected menu layout')
    offsets = struct.unpack_from('<4I', menu)
    require(new['MOJIPAT.ARC'][:offsets[2]] == menu[:offsets[2]] and
            new['MOJIPAT.ARC'][offsets[3]:] == menu[offsets[3]:],
            'Menu palette or other banks changed')
    expected = patch_save_executable(patch_executable(old['SLUS_005.61']))
    require(new['SLUS_005.61'] == expected, 'EXE differs from reviewed display-only proposal')
    spans = [(off(START), off(END)), (off(SAVE_BEGIN), off(SAVE_END)),
             (off(0x8001BE60), off(0x8001BE64))]
    diff = [i for i, (x, y) in enumerate(zip(old['SLUS_005.61'], expected)) if x != y]
    require(all(any(a <= p < b for a, b in spans) for p in diff), 'EXE change escaped display spans')
    return {'resource_lengths_and_lbas_preserved': True,
            'player_audio_palettes_dialogue_other_entries_byte_identical': True,
            'load_background_non_atlas_entries_byte_identical': True,
            'all_menu_palettes_including_red_rin_and_gray_riko_byte_identical': True,
            'exe_changed_bytes': len(diff),
            'exe_allowed_ranges': [[hex(a), hex(b)] for a, b in
                                   ((START, END), (SAVE_BEGIN, SAVE_END), (0x8001BE60, 0x8001BE64))],
            'all_other_exe_bytes_identical': True, 'runtime_verified': False}


def prepare(project, core_path, ui_path, output):
    source, expected = SOURCES[project]
    require(file_hash(ROOT / source) == expected, 'Unsupported parent BIN')
    old, records = read_disc(ROOT / source, NAMES)
    core_path, ui_path = safe_work_file(core_path), safe_work_file(ui_path)
    core, ui = json.loads(core_path.read_text('utf8')), json.loads(ui_path.read_text('utf8'))
    for proposal in (core, ui):
        require(proposal['project'] == project and proposal['baseline_sha256'] == expected,
                'Mixed project or parent proposal')
    require(core['source_arc_sha256'] == sha(old['PL02_U.ARC']), 'Wrong core source')
    modified_core = safe_work_file(core['resource']).read_bytes()
    require(sha(modified_core) == core['after_sha256'], 'Core artifact changed')
    modified_core, capsule_proof, _ = prepare_capsules(modified_core, old['PL02_U.ARC'])
    new = {'PL02_U.ARC': modified_core}
    require(set(ui['files']) == {'MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61'}, 'Unexpected UI source scope')
    for name, row in ui['files'].items():
        new[name] = safe_work_file(row['path']).read_bytes()
        require(row['before'] == sha(old[name]) and row['after'] == sha(new[name]), 'UI artifact changed')
    require(new['SLUS_005.61'] == patch_save_executable(old['SLUS_005.61']), 'Prepared UI code differs')
    new['SLUS_005.61'] = patch_save_executable(patch_executable(old['SLUS_005.61']))
    checks = validate_resources(old, new)
    output = (ROOT / output).resolve()
    require(output.is_relative_to(WORK.resolve()) and not output.exists(), 'Fresh task output required')
    output.mkdir(parents=True)
    files = {}
    for name in NAMES:
        path = output / name
        path.write_bytes(new[name])
        files[name] = {'source_sha256': sha(old[name]), 'sha256': sha(new[name]),
                       'path': path.relative_to(ROOT).as_posix(), 'record': records[name],
                       'size': len(new[name]), 'changed_bytes': sum(x != y for x, y in zip(old[name], new[name]))}
    report = {'kind': 'integrated_review_package_not_applied_to_disc', 'project': project,
              'source_bin': source, 'source_sha256': expected, 'files': files, 'checks': checks,
              'core_proposal': core_path.relative_to(ROOT).as_posix(),
              'ui_proposal': ui_path.relative_to(ROOT).as_posix(),
              'capsule_verification': capsule_proof, 'new_bin_created': False,
              'current_pointer_modified': False, 'requires_display_code_application_confirmation': True}
    write_json(output / 'proposal.json', report)
    print(json.dumps({'project': project, 'package': output.relative_to(ROOT).as_posix(),
                      'files': {n: {'sha256': r['sha256'], 'changed_bytes': r['changed_bytes']}
                                for n, r in files.items()}, 'checks': checks}))


def build(project, proposal_path, output):
    """Run only after user confirmation; keeps all original/current BINs intact."""
    proposal_path = safe_work_file(proposal_path)
    proposal = json.loads(proposal_path.read_text('utf8'))
    source, expected = SOURCES[project]
    require(proposal['project'] == project and proposal['source_sha256'] == expected,
            'Wrong project or parent')
    source = ROOT / source
    require(file_hash(source) == expected, 'Parent BIN changed')
    old, records = read_disc(source, NAMES)
    require(set(proposal['files']) == set(NAMES), 'Unexpected package scope')
    new = {}
    for name, row in proposal['files'].items():
        new[name] = safe_work_file(row['path']).read_bytes()
        require(sha(new[name]) == row['sha256'] and sha(old[name]) == row['source_sha256'] and
                records[name] == row['record'], 'Changed prepared resource or disc placement')
    require(validate_resources(old, new) == proposal['checks'], 'Reviewed checks differ')
    output = (ROOT / output).resolve()
    require(output.is_relative_to((ROOT / 'out' / project).resolve()) and not output.exists(),
            'Fresh project output required')
    output.mkdir(parents=True)
    stem = STEMS[project]
    target = output / (stem + '.bin')
    result = write_archive_copies(source, target,
        [({**records[n], 'sha256': sha(old[n])}, new[n]) for n in NAMES], expected)
    changed = {s['lba'] for s in result['changed_sectors']}
    count = 0
    with source.open('rb') as a, target.open('rb') as b:
        while before := a.read(2352):
            after = b.read(2352)
            require((before != after) == (count in changed), 'Undeclared disc change')
            if count in changed:
                validate_checks(after)
            count += 1
        require(not b.read(1), 'Disc length changed')
    require(read_disc(target, NAMES)[0] == new and file_hash(source) == expected, 'Readback/preservation failed')
    (output / (stem + '.cue')).write_text(working_cue(source.with_suffix('.cue').read_text('ascii'), stem + '.bin'), 'ascii')
    write_json(output / 'manifest.json', {'project': project, 'task': 'ultimate_costume_swap',
        'parent_bin': source.relative_to(ROOT).as_posix(), 'parent_sha256': expected,
        'modified_bin': result, 'all_disc_sectors_compared': count, 'readback_verified': True,
        'checks': proposal['checks'], 'proposal': proposal_path.relative_to(ROOT).as_posix(),
        'runtime_verified': False, 'user_accepted': False})
    print(json.dumps({'project': project, 'bin': target.relative_to(ROOT).as_posix(),
                      'sha256': result['sha256'], 'changed_sectors': len(changed)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'build'))
    parser.add_argument('--project', choices=SOURCES, required=True)
    parser.add_argument('--core')
    parser.add_argument('--ui')
    parser.add_argument('--proposal')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        require(args.core and args.ui, 'Prepare needs both proposals')
        prepare(args.project, args.core, args.ui, args.output)
    else:
        require(args.proposal, 'Build needs integrated proposal')
        build(args.project, args.proposal, args.output)
