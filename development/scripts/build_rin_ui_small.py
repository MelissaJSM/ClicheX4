"""린 선택/저장 UI만 수용 부모 BIN에 누적하고 전체 섹터를 대조한다."""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_rin_ui_small import PARENT, PARENT_SHA, CONFIG, read_sources, verify
from scripts.build_rin_idle import sha
from scripts.project import digest
from scripts.discover_inputs import DiscReader
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks


def main(art):
    art = art.resolve()
    if not art.is_relative_to(ROOT / 'work/ver_rin_nana/ui_small'):
        raise ValueError('Unexpected UI art folder')
    m, arc, config, originals = read_sources()
    r = json.loads((art / 'recipe.json').read_text('utf8'))
    if r['parent_sha256'] != PARENT_SHA or r['parent_arc_sha256'] != sha(arc) or r['config_sha256'] != digest(CONFIG) or r['parent_manifest_sha256'] != digest(PARENT / 'manifest.json'):
        raise ValueError('UI recipe source changed')
    edited = {}
    replacements = []
    if len(r['files']) != len(config['archives']):
        raise ValueError('UI recipe file count changed')
    for rec, item in zip(config['archives'], r['files']):
        name = rec['path'].split('/')[-1].split(';')[0]
        if item['source'] != rec or item['file'] != name:
            raise ValueError('UI recipe source binding changed')
        raw = (art / name).read_bytes()
        if sha(raw) != item['sha256']:
            raise ValueError('Prepared UI hash changed')
        edited[name] = raw
        replacements.append((rec, raw))
    verification = verify(originals, edited, arc)
    preservation = json.loads((PARENT / 'preservation.json').read_text('utf8'))
    def protected():
        for q in preservation['files']:
            if digest(ROOT / q['path']) != q['expected_sha256']:
                raise ValueError('Protected input changed: ' + q['path'])
    protected()
    out = ROOT / 'out/ver_rin_nana' / ('rin_ui_small_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir()
    source = PARENT / 'rin_nana.bin'
    result = write_archive_copies(source, out / 'rin_nana.bin', replacements, PARENT_SHA)
    shutil.copyfile(PARENT / 'rin_nana.cue', out / 'rin_nana.cue')
    shutil.copyfile(PARENT / 'modified.arc', out / 'modified.arc')
    shutil.copytree(art, out / 'ui')
    changed = {q['lba'] for q in result['changed_sectors']}
    count = 0
    with source.open('rb') as before, (out / 'rin_nana.bin').open('rb') as after:
        while True:
            a, b = before.read(2352), after.read(2352)
            if not a:
                if b:
                    raise ValueError('Output too long')
                break
            if len(a) != len(b) or (a != b) != (count in changed):
                raise ValueError('Unexpected sector change')
            if count in changed:
                validate_checks(b)
            count += 1
    with (out / 'rin_nana.bin').open('rb') as stream:
        disc = DiscReader(stream, result['size'])
        for rec, data in replacements:
            if disc.read(rec['lba'], rec['size']) != data:
                raise ValueError('UI readback differs')
        player = json.loads((ROOT / 'config/ps1_us_slus00561.json').read_text('utf8'))['zero_archive']
        if disc.read(player['lba'], player['size']) != arc:
            raise ValueError('Accepted gameplay ARC changed')
    protected()
    verification.update(all_disc_sectors_compared=count, changed_sectors=len(changed),
                        edc_ecc_checked=True, all_other_parent_sectors_exact=True,
                        ui_readback_identical=True, accepted_gameplay_arc_exact=True,
                        protected_files=len(preservation['files']),
                        embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest = {**m, 'kind': 'rin_selection_save_small', 'parent': PARENT.relative_to(ROOT).as_posix(),
                'parent_sha256': PARENT_SHA, 'modified_bin': result,
                'verification': verification, 'inherited_verification': m['verification'],
                'ui_overlay': {'recipe': (out / 'ui/recipe.json').relative_to(ROOT).as_posix(),
                               'recipe_sha256': digest(out / 'ui/recipe.json'),
                               'runtime_verified': False}, 'runtime_verified': False}
    for name, data in [('manifest.json', manifest), ('verification.json', verification), ('preservation.json', preservation)]:
        (out / name).write_text(json.dumps(data, indent=2) + '\n', 'utf8')
    pointer = {'project': 'ver_rin_nana', 'task': 'zero_rin', 'build': out.relative_to(ROOT).as_posix(),
               'cue': (out / 'rin_nana.cue').relative_to(ROOT).as_posix(), 'sha256': result['sha256'],
               'frames': m['cumulative_frames'], 'bank1_frames': m['cumulative_bank1_frames'],
               'runtime_verified': False}
    (ROOT / 'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer, indent=2) + '\n', 'utf8')
    print(json.dumps({'output': str(out), 'sha256': result['sha256'], 'verification': verification}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--art', type=Path, required=True)
    main(p.parse_args().art)
