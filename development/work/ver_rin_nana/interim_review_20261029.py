"""Record the tested build and audit protected inputs for the interim handoff."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return json.loads((ROOT / path).read_text('utf-8'))

def write(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')

def digest(path):
    with (ROOT / path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

build = 'out/ver_rin_nana/rin_ice_20261028T204000812726Z'
spin_build = 'out/ver_rin_nana/rin_spin_20261028T131143880636Z'
project = read('projects/ver_rin_nana/project.json')
provision = read('work/ver_rin_nana/emulator/provision.json')
original_emulator = Path(provision['cards'][0]['source']).parent.parent
protected = {project['source_bin']: project['source_sha256']}
protected.update({item['path']: item['sha256'] for item in project['references']})
protected.update({str(original_emulator / path): sha for path, sha in provision['protected_saves'].items()})
protected.update({item['copy']: item['sha256'] for item in provision['cards']})
first_hash = project['integration_policy']['common_source_sha256']
protected['out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin'] = first_hash
protected['completed/ver_buki_riko/v1.0.0/ClicheX4_Shibuki_Riko_v1.0.0.bin'] = first_hash
audit = []
for path, expected in protected.items():
    actual = digest(path)
    audit.append({'path': path, 'expected_sha256': expected, 'actual_sha256': actual, 'unchanged': actual == expected})
assert all(item['unchanged'] for item in audit), 'Protected input changed'
current = read('projects/ver_rin_nana/current_build.json')
assert current['build'] == build and digest(build + '/rin_nana.bin') == current['sha256']
assert digest('work/ver_rin_nana/emulator/sstates/SLUS_005.61.000') == '99cc1b93b18ea4eb9d9f7100ca5f4503fe6d250d3a17d0578d9aa2215113691c'
write(build + '/preservation_handoff.json', {'utc': datetime.now(timezone.utc).isoformat(), 'files': audit, 'all_unchanged': True})

records = [
    (spin_build, '20261028T131343523326Z', 'spaceport_spin_b8fc', 'air_spin_runtime/20261028T131442177397Z', 'input_playback/20261028T131442144562Z'),
    (build, '20261028T204052402450Z', 'spaceport_ice_320d', 'ice_runtime/20261028T204452143755Z', 'input_playback/20261028T204452114696Z'),
]
for out, session, checkpoint, capture, inputs in records:
    root = 'work/ver_rin_nana/'
    refresh = root + 'checkpoints/' + checkpoint + '/refresh.json'
    record_path = root + 'emulator_sessions/' + session + '/session.local.json'
    record = read(record_path)
    record.update({'save_state_loaded': True, 'save_state_provenance': refresh,
                   'runtime_evidence_kind': 'asset-refreshed checkpoint, not fresh disc loading',
                   'runtime_capture': root + capture + '/verification.local.json',
                   'input_playback': root + inputs + '/playback.local.json'})
    write(record_path, record)
    observed = read(root + capture + '/verification.local.json')
    frames = observed['frames']
    verified = observed['verified_frames']
    pipeline = observed['pipeline_verified_frames']
    pending = sorted(int(n) for n in frames if int(n) not in verified and int(n) not in pipeline)
    write(out + '/runtime_verification.json', {
        'build': out, 'bin_sha256': record['bin_sha256'],
        'evidence_kind': record['runtime_evidence_kind'], 'checkpoint_refresh': refresh,
        'capture': record['runtime_capture'], 'input_playback': record['input_playback'],
        'simultaneous_display_matches': verified, 'pipeline_display_matches': pipeline,
        'observed_scope_without_full_match': pending,
        'unobserved_recipe_frames': sorted(set(read(out + '/manifest.json')['verification']['new_frames']) - set(map(int, frames))),
        'whole_build_runtime_verified': False, 'user_art_acceptance': False,
        'process_memory_written': observed['process_memory_written'],
    })
write(build + '/tests_handoff.json', {
    'command': 'python -m unittest tests.test_rin_spin tests.test_rin_effects tests.test_rin_motion tests.test_psx_beam_in tests.test_psx_victory tests.test_psx_bank_patch tests.test_psx_frame_edit tests.test_rin_checkpoint',
    'result': 'OK', 'tests': 40, 'seconds': 1.732,
    'source': 'Executed at handoff; stdout recorded in Codex tool output.'
})
print(json.dumps({'protected_files': len(audit), 'all_unchanged': True, 'build': build}))
