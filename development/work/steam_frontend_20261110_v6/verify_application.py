"""Read-only installation audit and final packaged launcher verification."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
D = Path(__file__).parent
W = ROOT / 'work/steam_port_20261109'
BUILD = ROOT / 'work/steam_distribution_20261110_v103'


def load(path):
    return json.loads(path.read_text('utf8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


baseline = load(W / 'backup_manifest.json')
game = Path(baseline['steam_root'])
old = {r['relative_path']: r['installed_sha256'] for r in load(D / 'install_state_before.json')['files']}
current = load(W / 'install_state.json')['files']
assert all(sha(game / r['relative_path']) == r['installed_sha256'] for r in current)
assert all(sha(W / 'original' / r['relative_path']) == r['sha256'] for r in baseline['originals'])
changed = [r['relative_path'] for r in current if r['installed_sha256'] != old[r['relative_path']]]
assert set(changed) == {r['relative_path'] for r in load(D / 'builds.json')} and len(changed) == 3
preserved = {
    'out/ver_rin_nana/hq_armor_20261109_v3/rin_nana.bin': '03bb660be698dd7dd1b1b3fbf6612bcd1ed111cff47b5eda7c186ded3f343f3a',
    'out/ver_buki_riko/capsule_outline_20261109_v1/shibuki_riko.bin': '0d76b1e983275482e4aa5d56ebdaa4a7d6f01a571e8cea218337df9eb84ed46e',
    'out/releases/ClicheX4_Steam_v1.0.0.zip': 'a32982a8c6000e6dc0e5d040539596a4ca9da63ff0d23e8ba37b81bac798d58b',
    'out/releases/ClicheX4_Steam_v1.0.1.zip': 'a1ee4a0187bd83b33c057e2512c9f1d464bc6899d610de0413a8006418247a92',
    'out/releases/ClicheX4_Steam_v1.0.2.zip': 'e3025e98e58b6a27b86abc4176e07e95cb90b30bbe4b4294d67e44f4459b06c8',
}
assert all(sha(ROOT / path) == expected for path, expected in preserved.items())
launch = load(D / 'live_launch.json')
assert launch['ok'] and len(launch['result']['runtime_checks']) == 7
assert (D / 'live_00.png').exists()

destination = BUILD / '압축 해제 실행 확인'
destination.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT / 'out/releases/ClicheX4_Steam_v1.0.3.zip') as archive:
    assert all((destination / name).resolve().is_relative_to(destination.resolve()) for name in archive.namelist())
    for name in archive.namelist():
        target = destination / name
        data = archive.read(name)
        if target.exists():
            assert target.read_bytes() == data
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
environment = dict(os.environ)
environment['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
report = BUILD / 'validation/extracted_clean_path_verify.json'
result = subprocess.run([
    str(destination / 'ClicheX4_Steam_v1.0.3/ClicheX4.exe'), '--action', 'verify',
    '--game-dir', str(game), '--report', str(report),
], env=environment, creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
proof = load(report)
assert result.returncode == 0 and proof['ok'] and proof['result']['installed'] == 237
record = {
    'passed': True,
    'installed_files_verified': len(current),
    'original_backups_verified': len(baseline['originals']),
    'changed_files': changed,
    'only_3_intended_resources_changed': True,
    'ps1_and_previous_releases_preserved': True,
    'original_executable_preserved': True,
    'runtime_checks': 7,
    'pid': launch['result']['pid'],
    'observed_captures': ['live_00.png'],
    'capture_scope': 'X4 intro side wallpaper; selector acceptance comes from user feedback, not a new automated capture',
    'zip_extracted_verify_without_python_path': True,
    'user_design_acceptance': True,
    'user_acceptance_quote': '좋아! 일러 고쳐졌다!',
    'all_aspect_ratios_tested': False,
    'art_sources': {name: sha(D / 'art' / name) for name in ['ensemble_v6.png', 'pillar_pair_v5.png']},
}
(D / 'application.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps(record, ensure_ascii=False))
