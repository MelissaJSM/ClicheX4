"""Apply the approved jump alignment request as 28 graphics-coordinate bytes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import digest, load_project, write_json, working_cue
from scripts.discover_inputs import psx_arc, sha256
from scripts.riko_master_sheet import load_model, local
from scripts.build_riko_personal_effects import stage_replacements
from src.psx_disc import write_archive_copies
from src.psx_composition_shift import translate_compositions

SHIFTS = {(0, n): (-8, 0) for n in (22, 23, 24)}


def apply_alignment(archive):
    e = next(e for e in psx_arc(archive) if e['type'] == '0x3')
    lo, hi = e['offset'], e['offset'] + e['size']
    parts = archive[lo:hi]
    profile = json.loads((ROOT / 'config/riko_jump_alignment_us.json').read_text('utf8'))
    if sha256(parts) != profile['original_parts_sha256']:
        raise ValueError('Unsupported composition source hash')
    changed, report = translate_compositions(parts, SHIFTS)
    if report['changed_bytes'] != 28:
        raise ValueError('Unexpected jump part count')
    return archive[:lo] + changed + archive[hi:], report


def validate_layer(build, manifest, model):
    layer = manifest['jump_alignment']
    parent = local(Path(layer['parent_build']), ROOT / 'out/ver_buki_riko')
    if digest(parent / 'manifest.json') != layer['parent_manifest_sha256']:
        raise ValueError('Jump alignment parent changed')
    if digest(ROOT / 'config/riko_jump_alignment_us.json') != layer['config_sha256']:
        raise ValueError('Jump alignment config changed')
    expected, report = apply_alignment(model['built_arc'])
    if report != layer['coordinate_changes'] or (build / 'modified.arc').read_bytes() != expected:
        raise ValueError('Jump alignment archive differs from recipe')
    if sha256(expected) != manifest['modified_archive_sha256']:
        raise ValueError('Jump alignment archive hash mismatch')
    for p in parent.glob('*.png'):
        if digest(build / p.name) != digest(p):
            raise ValueError('Jump alignment must preserve every existing PNG')
    # The bitmap canvas and head rectangles are identical. Only the world
    # placement changes, so the editable master records the corrected bounds.
    for (_, n), (dx, dy) in SHIFTS.items():
        key = f'bank0_{n:03d}'
        pixels, size, bounds = model['frames'][key]
        moved = tuple(v + (dx if i % 2 == 0 else dy) for i, v in enumerate(bounds))
        model['frames'][key] = pixels, size, moved
        model['records'][key]['bounds'] = list(moved)
    entry=next(e for e in psx_arc(expected) if e['type']=='0x3')
    model.update(build=build, manifest=manifest, built_arc=expected,
                 display_parts=expected[entry['offset']:entry['offset']+entry['size']])
    return model


def build(parent, extracted):
    parent = local(parent, ROOT / 'out/ver_buki_riko')
    m = load_model(parent, extracted)
    if not m['manifest'].get('personal_effects') or m['manifest'].get('jump_alignment'):
        raise ValueError('Expected the accepted personal-effects build')
    config_path = ROOT / 'config/riko_jump_alignment_us.json'
    config = json.loads(config_path.read_text('utf8'))
    if config['source_sha256'] != m['manifest']['source_sha256']:
        raise ValueError('Unsupported source hash')
    changed, report = apply_alignment(m['built_arc'])
    profile = json.loads((ROOT / 'config/ps1_us_slus00561.json').read_text('utf8'))
    project = load_project(ROOT, 'ver_buki_riko')
    source = ROOT / project['source_bin']
    effect_config = json.loads((ROOT / 'config/riko_personal_effects_us.json').read_text('utf8'))
    stages = stage_replacements(source, effect_config, m['palette'])
    out = ROOT / 'out/ver_buki_riko' / ('riko_jump_alignment_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    result = write_archive_copies(source, out / 'riko_motion.bin',
        [(profile['zero_archive'], changed), *stages], config['source_sha256'])
    (out / 'modified.arc').write_bytes(changed)
    (out / 'riko_motion.cue').write_text(working_cue((ROOT / project['source_cue']).read_text('utf-8-sig'), 'riko_motion.bin'), 'ascii')
    for p in parent.glob('*.png'):
        shutil.copyfile(p, out / p.name)
    manifest = dict(m['manifest'])
    layer = {'parent_build': str(parent), 'parent_manifest_sha256': digest(parent / 'manifest.json'),
        'config_sha256': digest(config_path), 'coordinate_changes': report,
        'shared_animations': [10, 11, 14, 20, 99], 'runtime_verified': False}
    manifest.update(kind='riko_jump_alignment_v1', modified_archive_sha256=sha256(changed),
        modified_bin=result, jump_alignment=layer)
    write_json(out / 'manifest.json', manifest)
    validate_layer(out, manifest, m)
    print(json.dumps({'output': str(out), 'sha256': result['sha256'], 'coordinate_bytes': report['changed_bytes']}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--extract', type=Path, required=True)
    a = p.parse_args()
    build(a.parent, a.extract)
