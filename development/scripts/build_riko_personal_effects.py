"""Rebuild Riko's pure warp colors and 24 stage-local afterimage CLUTs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import new_run, write_json, working_cue, digest, load_project
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.extract_zero import save_image
from scripts.riko_master_sheet import load_model, local
from src.psx_disc import write_archive_copies
from src.psx_personal_effects import apply_warp, recolor_stage, trail_palette, WARP_FRAMES, PARTS_BANKS
from src.psx_player import graphics_bank, decode_stream, composition_frame, compose_indices


def stage_replacements(source, config, palette):
    rows = []
    with source.open('rb') as stream:
        disc = DiscReader(stream, source.stat().st_size)
        actual = {r['path']: r for r in disc.inspect()['files']}
        for rec in config['stage_archives']:
            if any(actual[rec['path']][k] != rec[k] for k in ('lba', 'size')):
                raise ValueError('Stage ISO record changed')
            original = disc.read(rec['lba'], rec['size'])
            rows.append((rec, recolor_stage(original, rec['sha256'], palette)))
    return rows


def validate_layer(build, manifest, model):
    """Resolve the body master through its immutable parent; verify effects separately."""
    effect = manifest['personal_effects']
    parent = local(Path(effect['parent_build']), ROOT / 'out/ver_buki_riko')
    if digest(parent / 'manifest.json') != effect['parent_manifest_sha256']:
        raise ValueError('Effect parent binding changed')
    config_path = ROOT / 'config/riko_personal_effects_us.json'
    if digest(config_path) != effect['config_sha256']:
        raise ValueError('Effect palette configuration changed')
    expected, streams = apply_warp(model['built_arc'])
    if streams != effect['warp_streams'] or (build / 'modified.arc').read_bytes() != expected:
        raise ValueError('Warp layer differs from the verified parent')
    if sha256(expected) != manifest['modified_archive_sha256']:
        raise ValueError('Effect archive hash mismatch')
    for path in parent.glob('*.png'):
        if path.name in {f'bank1_{n:03d}.png' for n in WARP_FRAMES[1]}:
            continue
        if digest(build / path.name) != digest(path):
            raise ValueError('Effect layer changed an accepted PNG')
    config = json.loads(config_path.read_text('utf8'))
    source = ROOT / load_project(ROOT, 'ver_buki_riko')['source_bin']
    stages = stage_replacements(source, config, model['palette'])
    with (build / manifest['bin_file']).open('rb') as handle:
        disc = DiscReader(handle, (build / manifest['bin_file']).stat().st_size)
        for rec, data in stages:
            if disc.read(rec['lba'], rec['size']) != data:
                raise ValueError('Stage afterimage palette differs from source recipe')
    model.update(build=build, manifest=manifest, built_arc=expected)
    return model


def build(parent, extracted):
    m = load_model(parent, extracted)
    if m['manifest'].get('personal_effects'):
        raise ValueError('Expected an unrecolored body build')
    config_path = ROOT / 'config/riko_personal_effects_us.json'
    config = json.loads(config_path.read_text('utf8'))
    if config['source_sha256'] != m['manifest']['source_sha256']:
        raise ValueError('Unsupported source for effects')
    project = load_project(ROOT, 'ver_buki_riko')
    source = ROOT / project['source_bin']
    arc, streams = apply_warp(m['built_arc'])
    stages = stage_replacements(source, config, m['palette'])
    profile = json.loads((ROOT / 'config/ps1_us_slus00561.json').read_text('utf8'))
    out = ROOT / 'out/ver_buki_riko' / ('riko_personal_effects_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    modified = write_archive_copies(source, out / 'riko_motion.bin',
        [(profile['zero_archive'], arc), *stages], config['source_sha256'])
    (out / 'modified.arc').write_bytes(arc)
    (out / 'riko_motion.cue').write_text(working_cue((ROOT / project['source_cue']).read_text('utf-8-sig'), 'riko_motion.bin'), 'ascii')
    for path in parent.glob('*.png'):
        shutil.copyfile(path, out / path.name)
    manifest = dict(m['manifest'])
    manifest['bank1_frame_inputs'] = {k: dict(v) for k, v in manifest['bank1_frame_inputs'].items()}
    gm = m['gmeta']; gfx = arc[gm['offset']:gm['offset'] + gm['size']]
    for bi, numbers in WARP_FRAMES.items():
        bank = graphics_bank(gfx, bi)
        for n in numbers:
            f = bank['frames'][n]
            raw = decode_stream(gfx, f['offset'], f['limit'], f['tile_count'] * 128).data
            data, size = compose_indices(raw, f['tile_count'], composition_frame(m['parts'], PARTS_BANKS[bi], n))[:2]
            name = f'bank1_{n:03d}.png' if bi else f'warp_bank0_{n:03d}.png'
            # save_image uses exclusive creation; only replace our fresh copied preview.
            target = out / name
            if target.exists():
                target.unlink()
            save_image(data, size, m['words'], target)
            if bi:
                manifest['bank1_frame_inputs'][str(n)]['sha256'] = digest(target)
    effect = {'version': 1, 'parent_build': str(parent.resolve()),
        'parent_manifest_sha256': digest(parent / 'manifest.json'),
        'config_sha256': digest(config_path), 'warp_streams': streams,
        'warp_references': 13, 'body_references_unchanged': 266,
        'afterimage_cluts': [13, 14, 15], 'afterimage_palette_hex': trail_palette(m['palette']).hex(),
        'stage_archives': [{**r, 'modified_sha256': sha256(data)} for r, data in stages],
        'excluded_non_afterimage_palette': config['excluded_different_usage'],
        'parts_timing_executable_unchanged': True, 'runtime_verified': False}
    manifest.update(kind='riko_personal_effects_v1', modified_archive_sha256=sha256(arc),
        modified_bin=modified, bin_file='riko_motion.bin', personal_effects=effect)
    write_json(out / 'manifest.json', manifest)
    validate_layer(out, manifest, m)
    print(json.dumps({'output': str(out), 'sha256': modified['sha256'],
        'warp_references': 13, 'stage_palettes': len(stages)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--extract', type=Path, required=True)
    args = parser.parse_args()
    build(args.parent, args.extract)
