"""피격 음량과 시부키 캡슐 수정의 서로 겹치지 않는 변경을 새 BIN에 통합한다."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_audio_verify_cpu import banks
from scripts.prepare_riko_ui import entry
from scripts.project import working_cue
from src.psx_disc import file_hash, write_archive_copies
from src.psx_player import bank_offsets
from src.psx_sector import validate_checks

WORK = ROOT / 'work/hurt_capsule_fix_20261106'
BUILD_NAME = 'hurt_capsule_fix_20261106_v1'
PARENTS = {
    'ver_buki_riko': ('shibuki_riko', 'ef2fcec562f02f6ba6b372e26b021924ea595abe4d654a9fc4e632a529804bb7'),
    'ver_rin_nana': ('rin_nana', 'c84dcda554ae6320c9808fc55088731a7f90dc9bda391d5c0674645315b56b31'),
}
NAMES = {'PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC'}


def require(test, message):
    if not test:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', 'utf8')


def changes(old, new):
    require(len(old) == len(new), 'Resource size changed')
    return {i for i, (a, b) in enumerate(zip(old, new)) if a != b}


def proposal(project, path, names):
    path = path.resolve()
    require(path.is_relative_to(WORK.resolve()), 'Proposal outside task workspace')
    data = json.loads(path.read_text('utf8'))
    require(data['project'] == project and data['baseline_sha256'] == PARENTS[project][1],
            'Proposal parent/project mismatch')
    require(set(data['files']) == names, 'Unexpected proposed resources')
    result = {}
    for name, r in data['files'].items():
        p = (ROOT / r['path']).resolve()
        require(p.is_relative_to(WORK.resolve()), 'Resource outside task workspace')
        b = p.read_bytes()
        require(sha(b) == r['after'], 'Prepared resource hash differs')
        result[name] = (r, b)
    return result


def validate_audio(old, new):
    h, body, q = banks(old)[3]
    headers = [e for e in psx_arc(old) if old[e['offset']:e['offset'] + e['size']] == h]
    require(len(headers) == 1 and q['program_count'] == 1, 'Unsupported player bank')
    at = headers[0]['offset'] + q['vab_offset'] + 32 + 128 * 16 + 2
    require(old[at] == 90 and new[at] == 104 and changes(old, new) == {at},
            'Expected only reviewed hurt tone volume90->104')
    require(banks(new)[3][1] == body, 'Hurt waveform bytes changed')
    return {'offset': at, 'before_volume': 90, 'after_volume': 104,
            'all_other_resource_bytes_identical': True}


def validate_capsule(old, new):
    layout = lambda a: [(e['type'], e['offset'], e['size']) for e in psx_arc(a)]
    require(layout(old) == layout(new), 'Capsule ARC layout changed')
    allowed = set()
    for kind, ids in ((2, range(10, 14)), (3, range(18, 22))):
        before, after = entry(old, kind), entry(new, kind)
        starts = bank_offsets(before, allow_aliases=True)
        require(starts == bank_offsets(after, allow_aliases=True), 'Capsule bank boundaries changed')
        resource = next(e for e in psx_arc(old) if int(e['type'], 16) == kind)
        for index in ids:
            a = resource['offset'] + starts[index]
            b = resource['offset'] + (starts[index + 1] if index + 1 < len(starts) else len(before))
            allowed.update(range(a, b))
    changed = changes(old, new)
    require(changed and changed <= allowed, 'Capsule change escaped approved effect banks')
    return {'changed_bytes': len(changed), 'only_capsule_graphics_composition_changed': True,
            'gameplay_audio_palette_animation_preserved': True}


def build(project, audio_path, capsule_path=None, audio_only=False):
    stem, expected = PARENTS[project]
    source = ROOT / 'out' / project / 'boss_voice_restored_20261105_v2' / (stem + '.bin')
    require(file_hash(source) == expected, 'Unsupported parent BIN')
    require(not (audio_only and capsule_path), 'Choose capsule correction or explicit audio-only build')
    require(not capsule_path or project == 'ver_buki_riko', 'Capsule correction is Shibuki-only')
    require(project != 'ver_buki_riko' or capsule_path or audio_only,
            'Unconfirmed capsule defect requires explicit --audio-only; do not invent a correction')
    audio = proposal(project, audio_path, NAMES)
    capsule = proposal(project, capsule_path, {'PL02_U.ARC'}) if capsule_path else {}
    with source.open('rb') as f:
        disc = DiscReader(f, source.stat().st_size)
        records = {r['name'].split(';')[0]: r for r in disc.inspect()['files']
                   if r['name'].split(';')[0] in NAMES and not r['directory']}
        require(set(records) == NAMES, 'Player resource missing')
        old = {n: disc.read(r['lba'], r['size']) for n, r in records.items()}
    payloads, checks = {}, {}
    for name, before in old.items():
        meta, modified = audio[name]
        require(sha(before) == meta['before'], 'Wrong audio source')
        checks[name] = {'audio': validate_audio(before, modified)}
        merged = bytearray(modified)
        if name in capsule:
            cp, effect = capsule[name]
            require(sha(before) == cp['before'], 'Wrong capsule source')
            checks[name]['capsule'] = validate_capsule(before, effect)
            a, b = changes(before, modified), changes(before, effect)
            require(not a & b, 'Audio and capsule changes overlap')
            for at in b:
                merged[at] = effect[at]
            require(changes(before, merged) == a | b, 'Merged change set differs')
            checks[name]['merged_overlap_bytes'] = 0
        payloads[name] = bytes(merged)
    output = ROOT / 'out' / project / BUILD_NAME
    require(not output.exists(), 'Output already exists')
    output.mkdir(parents=True)
    target = output / (stem + '.bin')
    replacements = [({**records[n], 'sha256': sha(old[n])}, data) for n, data in payloads.items()]
    result = write_archive_copies(source, target, replacements, expected)
    changed = {r['lba'] for r in result['changed_sectors']}
    count = 0
    with source.open('rb') as a, target.open('rb') as b:
        while previous := a.read(2352):
            updated = b.read(2352)
            require((previous != updated) == (count in changed), 'Undeclared sector change')
            if count in changed:
                validate_checks(updated)
                require(previous[:24] == updated[:24], 'Raw sector header changed')
            count += 1
        require(not b.read(1), 'Disc size changed')
    with target.open('rb') as f:
        disc = DiscReader(f, target.stat().st_size)
        for record, data in replacements:
            require(disc.read(record['lba'], record['size']) == data, 'Disc resource readback differs')
    require(file_hash(source) == expected, 'Parent image changed')
    cue = working_cue(source.with_suffix('.cue').read_text('ascii'), stem + '.bin')
    (output / (stem + '.cue')).write_text(cue, 'ascii')
    write_json(output / 'manifest.json', {
        'project': project, 'task': 'hurt_capsule_fix', 'parent_sha256': expected,
        'parent': source.relative_to(ROOT).as_posix(), 'modified_bin': result,
        'checks': checks, 'all_disc_sectors_compared': count,
        'all_other_sectors_identical': True, 'EDC_ECC_verified': True,
        'resource_readback_verified': True, 'exe_and_boss_voices_preserved': True,
        'hurt_volume': {'before': 90, 'after': 104, 'raw_adpcm_pitch_duration_preserved': True},
        'audio_proposal': audio_path.resolve().relative_to(ROOT).as_posix(),
        'capsule_proposal': capsule_path.resolve().relative_to(ROOT).as_posix() if capsule_path else None,
        'capsule_status': ('corrected_pending_runtime' if capsule_path else
                           'post_grant_mismatch_not_reproduced_assets_preserved' if project == 'ver_buki_riko'
                           else 'not_in_scope'),
        'prepared_resources': {n: sha(v) for n, v in payloads.items()},
        'runtime_verified': False, 'user_accepted': False,
    })
    print(json.dumps({'project': project, 'sha256': result['sha256'],
                      'changed_sectors': len(changed), 'cue': (output / (stem + '.cue')).relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', choices=PARENTS, required=True)
    p.add_argument('--audio-proposal', type=Path, required=True)
    p.add_argument('--capsule-proposal', type=Path)
    p.add_argument('--audio-only', action='store_true',
                   help='Apply only confirmed hurt gain; preserve unconfirmed capsule visuals')
    a = p.parse_args()
    build(a.project, a.audio_proposal, a.capsule_proposal, a.audio_only)
