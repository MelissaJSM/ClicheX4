"""Verify a HUD proposal, or apply only its three ARC textures to a new BIN."""
import argparse
from datetime import datetime, timezone
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_hud_emblems import PARENT, PARENT_SHA, SOURCE_SHA, RECORDS, KIND, require, protected_hashes, validate_candidate
from scripts.discover_inputs import DiscReader, sha256
from scripts.project import working_cue
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks


def build(candidate, check_only=False):
    candidate = Path(candidate).resolve()
    recipe, current, changed = validate_candidate(candidate)
    if check_only:
        result = {'candidate': str(candidate), 'reproduced_resources': len(changed),
                  'target_frames': 27, 'parts_uv_palette_preserved': True,
                  'bin_created': False, 'runtime_verified': False}
        print(json.dumps(result, ensure_ascii=False))
        return result
    source = PARENT / 'shibuki_riko.bin'
    output = ROOT / 'out/ver_buki_riko' / ('hud_emblems_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    require(not output.exists() and output.resolve().is_relative_to((ROOT / 'out/ver_buki_riko').resolve()), 'Unsafe or existing output path')
    updates = [({**RECORDS[name], 'sha256': sha256(current[name])}, data) for name, data in changed.items()]
    output.mkdir(exist_ok=False)
    target = output / 'shibuki_riko.bin'
    result = write_archive_copies(source, target, updates, PARENT_SHA)
    expected = {item['lba'] for item in result['changed_sectors']}
    actual = set()
    require(result['size'] == source.stat().st_size and result['size'] % 2352 == 0, 'Disc size or sector format changed')
    with source.open('rb') as before_stream, target.open('rb') as after_stream:
        for lba in range(result['size'] // 2352):
            before, after = before_stream.read(2352), after_stream.read(2352)
            if before == after:
                continue
            hits = [(record, data) for record, data in updates
                    if record['lba'] <= lba < record['lba'] + (record['size'] + 2047) // 2048]
            require(len(hits) == 1 and lba in expected and before[:24] == after[:24], 'Unexpected sector or track/header mutation')
            record, data = hits[0]
            offset = (lba - record['lba']) * 2048
            chunk = data[offset:offset + 2048]
            require(after[24:24 + len(chunk)] == chunk and after[24 + len(chunk):2072] == before[24 + len(chunk):2072],
                    'Payload writes escape the declared same-size ARC')
            validate_checks(after)
            actual.add(lba)
    require(actual == expected, 'Changed-sector comparison is incomplete')
    with target.open('rb') as stream:
        reader = DiscReader(stream, target.stat().st_size)
        for record, data in updates:
            require(reader.read(record['lba'], record['size']) == data, 'BIN ARC readback differs')
    protected_hashes()
    for name, data in changed.items():
        (output / name).write_bytes(data)
    (output / 'shibuki_riko.cue').write_text(working_cue((PARENT / 'shibuki_riko.cue').read_text('ascii'), 'shibuki_riko.bin'), encoding='ascii')
    for name in ('recipe.json', 'hud_comparison.png', 'shibuki_indices.png', 'riko_indices.png', 'native_hud_palette.bin'):
        shutil.copyfile(candidate / name, output / name)
    manifest = {'project': 'ver_buki_riko', 'task': 'hud_emblem_redesign', 'kind': KIND,
                'source_sha256': SOURCE_SHA, 'parent_build': str(PARENT.relative_to(ROOT)),
                'parent_bin_sha256': PARENT_SHA, 'bin_file': 'shibuki_riko.bin',
                'modified_bin': {key: value for key, value in result.items() if key != 'changed_sectors'},
                'changed_resources': list(changed), 'changed_sectors': len(actual),
                'full_disc_sectors_compared': result['size'] // 2352,
                'target_frames': 27, 'changed_entry': '0x10206',
                'parts_uv_geometry_palette_preserved': True, 'original_alpha_preserved': True,
                'resource_sizes_lbas_tracks_preserved': True, 'exe_changed': False,
                'gameplay_logic_changed': False, 'animation_timing_changed': False,
                'candidate': str(candidate.relative_to(ROOT)), 'runtime_verified': False,
                'active_game_restarted': False}
    for name, data in (('manifest.json', manifest), ('sector_changes.json', result)):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(output), 'sha256': result['sha256'], 'changed_sectors': len(actual),
                      'full_disc_verified': True, 'runtime_verified': False}, ensure_ascii=False))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true', help='Reproduce and verify without creating a game BIN')
    args = parser.parse_args()
    build(args.candidate, args.check_only)
