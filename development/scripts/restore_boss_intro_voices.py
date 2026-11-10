"""미국판 8보스 개전 XA 호출만 복구하고 별도 BIN/CUE를 만든다."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_audio_verify_cpu import banks
from scripts.project import working_cue
from src.psx_disc import file_hash, write_archive_copies
from src.psx_sector import validate_checks

PARENTS = {
    'ver_buki_riko': ('shibuki_riko', '5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d'),
    'ver_rin_nana': ('rin_nana', 'de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679'),
}
EXE_SHA = '1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab'
ADDRESS = 0x800921F8
BEFORE = bytes.fromhex('18004014')
AFTER = bytes(4)
OUTPUT_NAME = 'boss_voice_restored_20261105_v1'
FULL_OUTPUT_NAME = 'boss_voice_restored_20261105_v2'
COMBAT_FILES = {n for s in (1, 2, 3, 5, 6, 7, 8)
                for n in (f'ST{s}_1_1.ARC', f'ONPARE{s}.ARC')}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_exe(path):
    with path.open('rb') as stream:
        reader = DiscReader(stream, path.stat().st_size)
        matches = [r for r in reader.inspect()['files'] if r['path'] == '/SLUS_005.61;1']
        require(len(matches) == 1, 'Unsupported executable directory entry')
        record = matches[0]
        return reader.read(record['lba'], record['size']), record


def patch_exe(before):
    require(sha(before) == EXE_SHA, 'Unsupported current executable hash')
    require(before[:8] == b'PS-X EXE', 'Invalid executable format')
    base, size = struct.unpack_from('<II', before, 0x18)
    offset = ADDRESS - base + 2048
    require(2048 <= offset <= 2048 + size - 4 and offset + 4 <= len(before), 'Instruction outside EXE')
    require(before[offset:offset + 4] == BEFORE, 'Unexpected boss voice branch')
    after = before[:offset] + AFTER + before[offset + 4:]
    require(len(before) == len(after) and before[:offset] == after[:offset]
            and before[offset + 4:] == after[offset + 4:], 'Unrelated executable bytes changed')
    return after, offset


def combat_replacements(project, source, expected, proposal_path):
    proposal_path = proposal_path.resolve()
    work = (ROOT / 'work/boss_voice_restore_20261105').resolve()
    require(proposal_path.is_relative_to(work), 'Proposal outside task workspace')
    proposal = json.loads(proposal_path.read_text('utf8'))
    require(proposal['project'] == project and
            proposal.get('parent_sha256', proposal.get('baseline_sha256')) == expected,
            'Combat proposal targets another parent')
    require(set(proposal['files']) == COMBAT_FILES, 'Unexpected combat resource set')
    replacements, checks = [], {}
    with source.open('rb') as stream:
        disc = DiscReader(stream, source.stat().st_size)
        records = {r['name'].split(';')[0]: r for r in disc.inspect()['files']
                   if not r['directory'] and r['name'].split(';')[0] in COMBAT_FILES}
        require(set(records) == COMBAT_FILES, 'Combat file missing from parent')
        for name, p in proposal['files'].items():
            path = (ROOT / p['path']).resolve()
            require(path.is_relative_to(work), 'Prepared resource outside workspace')
            r = records[name]
            old, new = disc.read(r['lba'], r['size']), path.read_bytes()
            require(sha(old) == p['before'] and sha(new) == p['after'], 'Combat proposal hash mismatch')
            layout = lambda a: [(e['index'], e['type'], e['offset'], e['size']) for e in psx_arc(a)]
            require(len(old) == len(new) and layout(old) == layout(new), 'Combat ARC layout changed')
            prior, fixed = banks(old), banks(new)
            require(set(prior) == set(fixed) and 2 in prior, 'Combat bank set changed')
            for slot in prior:
                if slot != 2:
                    require(prior[slot][:2] == fixed[slot][:2], 'Non-boss sound bank changed')
            h, body, q = prior[2]
            nh, nb, nq = fixed[2]
            for key in ('slot', 'vab_offset', 'body_bytes', 'program_count', 'tone_count',
                        'wave_count', 'command_count'):
                require(q[key] == nq[key], 'Combat bank capacity/layout changed: ' + key)
            allowed = bytearray(len(old))
            found = 0
            for entry in psx_arc(old):
                a, b = entry['offset'], entry['offset'] + entry['size']
                if old[a:b] in (h, body):
                    allowed[a:b] = b'\1' * entry['size']
                    found += 1
            require(found == 2, 'Ambiguous boss audio entries')
            require(all(a == b or allowed[i] for i, (a, b) in enumerate(zip(old, new))),
                    'Graphics or unrelated ARC data changed')
            checks[name] = {'before': sha(old), 'after': sha(new), 'only_bank2_changed': True,
                            'ARC_and_SPU_body_sizes_preserved': True}
            replacements.append(({**r, 'sha256': sha(old)}, new))
    return replacements, checks


def build(project, combat_proposal=None):
    stem, expected = PARENTS[project]
    source = ROOT / 'out' / project / 'sprite_consistency_20261105_v1' / (stem + '.bin')
    output = ROOT / 'out' / project / (FULL_OUTPUT_NAME if combat_proposal else OUTPUT_NAME)
    require(file_hash(source) == expected, 'Unsupported parent disc hash')
    require(not output.exists(), 'Output already exists')
    original, record = read_exe(source)
    updated, offset = patch_exe(original)
    # These independent reports must exist and pass before creating a game file.
    proof_dir = ROOT / 'work/boss_voice_restore_20261105'
    native = json.loads((proof_dir / 'calls/native_voice_probe.json').read_text('utf8'))
    require(native['passed'] and native['cases_boss_by_rng'] == 13 * 256,
            'Complete native boss dispatch verification missing')
    current_native = json.loads((proof_dir / 'audit/current_intro_native.json').read_text('utf8'))
    require(current_native['passed'] and current_native['current_exe_sha256'] == sha(original)
            and current_native['patched_current_exe_sha256'] == sha(updated),
            'Independent current executable verification missing or stale')
    proposal = json.loads((proof_dir / 'calls/branch_proposal.json').read_text('utf8'))
    require(proposal['current_exe_sha256'] == EXE_SHA and len(proposal['patches']) == 1,
            'Unexpected patch proposal')
    p = proposal['patches'][0]
    require(p['file_offset'] == offset and p['before'] == BEFORE.hex() and p['after'] == AFTER.hex(),
            'Patch proposal differs from reviewed instruction')
    replacements, checks = ([({**record, 'sha256': sha(original)}, updated)], {})
    if combat_proposal:
        combat, checks = combat_replacements(project, source, expected, combat_proposal)
        replacements.extend(combat)
    output.mkdir(parents=True)
    target = output / (stem + '.bin')
    result = write_archive_copies(source, target, replacements, expected)
    changed = {r['lba'] for r in result['changed_sectors']}
    require(bool(changed) and (combat_proposal or len(changed) == 1), 'Unexpected changed sector count')
    count = 0
    with source.open('rb') as a, target.open('rb') as b:
        while old := a.read(2352):
            new = b.read(2352)
            require((old != new) == (count in changed), 'Undeclared sector difference')
            if count in changed:
                validate_checks(new)
                require(old[:24] == new[:24], 'Sector header changed')
            count += 1
        require(not b.read(1), 'Disc size changed')
    require(read_exe(target)[0] == updated and file_hash(source) == expected, 'Readback/protection failed')
    with target.open('rb') as stream:
        disc = DiscReader(stream, target.stat().st_size)
        for r, payload in replacements:
            require(disc.read(r['lba'], r['size']) == payload, 'Integrated resource readback mismatch')
    cue = working_cue(source.with_suffix('.cue').read_text('ascii'), stem + '.bin')
    (output / (stem + '.cue')).write_text(cue, encoding='ascii')
    manifest = {
        'project': project, 'task': 'boss_voice_restoration',
        'parent': source.relative_to(ROOT).as_posix(), 'parent_sha256': expected,
        'modified_bin': result,
        'executable': {'path': record['path'], 'before': sha(original), 'after': sha(updated),
                       'instruction_address': hex(ADDRESS), 'offset': offset,
                       'old_instruction': BEFORE.hex(), 'new_instruction': AFTER.hex()},
        'all_disc_sectors_compared': count, 'all_unrelated_sectors_identical': True,
        'all_graphics_dialogue_movie_resources_identical_to_parent': True,
        'combat_proposal': combat_proposal.relative_to(ROOT).as_posix() if combat_proposal else None,
        'combat_checks': checks,
        'EDC_ECC_verified': True, 'disc_readback_verified': True,
        'native_dispatch_evidence': 'work/boss_voice_restore_20261105/calls/native_voice_probe.json',
        'native_dispatch_cases': native['cases_boss_by_rng'],
        'behavior_change': '8보스 개전의 60프레임 무음 대기를 원래 XA 대사 완료 대기로 복구',
        'protagonist_mute_preserved': True,
        'runtime_verified': False, 'user_accepted': False,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'project': project, 'sha256': result['sha256'], 'changed_sectors': len(changed),
                      'cue': (output / (stem + '.cue')).relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', choices=PARENTS, required=True)
    parser.add_argument('--combat-proposal', type=Path)
    args = parser.parse_args()
    build(args.project, args.combat_proposal.resolve() if args.combat_proposal else None)
