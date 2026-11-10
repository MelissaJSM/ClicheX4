"""수용된 린 도트를 선택/저장 전용 타일에 같은 크기와 기준점으로 등록한다."""
import argparse
import json
import struct
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_riko_ui import entry, replace_entry, actual_frame, SELECTION_MAPPING
from scripts.discover_inputs import DiscReader
from scripts.project import digest
from scripts.build_rin_idle import sha
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition, place_frame, repack_frames, tile_pixels
from src.sprite_window_fit import fit_windows

PARENT = ROOT / 'out/ver_rin_nana/rin_chaser_20261029T005715379960Z'
PARENT_SHA = '733b64eded82db18525e77c3f988ef53d5bb37b23884dfc4c0674afca0849803'
CONFIG = ROOT / 'config/riko_ui_us.json'


def read_sources(parent=PARENT):
    manifest = json.loads((parent / 'manifest.json').read_text('utf8'))
    if manifest['modified_bin']['sha256'] != PARENT_SHA:
        raise ValueError('Unsupported accepted Rin parent')
    arc = (parent / 'modified.arc').read_bytes()
    if sha(arc) != manifest['modified_archive_sha256']:
        raise ValueError('Accepted player ARC changed')
    config = json.loads(CONFIG.read_text('utf8'))
    source = parent / 'rin_nana.bin'
    if digest(source) != PARENT_SHA:
        raise ValueError('Parent BIN changed')
    originals = {}
    with source.open('rb') as stream:
        disc = DiscReader(stream, source.stat().st_size)
        iso = {r['path']: r for r in disc.inspect()['files']}
        for rec in config['archives']:
            if any(iso[rec['path']][key] != rec[key] for key in ('lba', 'size')):
                raise ValueError('UI ISO location changed')
            raw = disc.read(rec['lba'], rec['size'])
            if sha(raw) != rec['sha256']:
                raise ValueError('Expected original UI resource')
            originals[rec['path'].split('/')[-1].split(';')[0]] = raw
    return manifest, arc, config, originals


def world(frame):
    data, size, bounds = frame[:3]
    return {(i % size[0] + bounds[0], i // size[0] + bounds[1]): v & 15
            for i, v in enumerate(data) if v}


def register(parts, bank, mapping, texture, arc, idle_positions=None):
    changed = bytearray(parts)
    gp = entry(arc, 3)
    model = {'built_arc': arc}
    targets, layouts = {}, {}
    for n, (source_bank, source_frame) in mapping.items():
        frame = actual_frame(model, source_bank, source_frame)
        c = composition_frame(parts, bank, n)
        src = composition_frame(gp, 0 if source_bank == 0 else 5, source_frame)
        try:
            place_frame(frame, c, texture)
            positions = [(p['x'], p['y']) for p in c['parts']]
        except ValueError:
            if len(c['parts']) == len(src['parts']):
                positions = [(p['x'], p['y']) for p in src['parts']]
            elif (source_bank, source_frame) == (0, 147) and idle_positions is not None:
                positions = idle_positions
            else:
                a = np.frombuffer(frame[0], dtype=np.uint8).reshape(frame[1][1], frame[1][0])
                # Static atlas tiles are reassigned after fitting. Unique dummy
                # IDs remove compressed-stream U0 constraints from this solver.
                dummy = [dict(p, tile=i + 1, flip_x=False) for i, p in enumerate(c['parts'])]
                fit = fit_windows(dummy, a, frame[2][0], frame[2][1])
                if fit is None:
                    raise ValueError(f'UI {bank}:{n} cannot fit original part count')
                by_offset = {p['record_offset']: (x, y) for p, x, y in fit}
                positions = [by_offset[p['record_offset']] for p in c['parts']]
        if len(positions) != len(c['parts']):
            raise ValueError('Part count differs')
        for p, (x, y) in zip(c['parts'], positions):
            if not -128 <= x <= 127 or not -128 <= y <= 127:
                raise ValueError('Position out of range')
            off = p['record_offset'] + 2
            changed[off:off + 2] = bytes((x & 255, y & 255))
        cc = composition_frame(changed, bank, n)
        targets[n] = place_frame(frame, cc, texture)
        layouts[n] = positions
    return bytes(changed), targets, layouts


def protected_repack(texture, original_parts, repositioned, bank, targets, overrides=None):
    # Preserve every atlas tile outside the original target allocation, even
    # tiles with no known composition reference (possible direct GPU users).
    owned = {p['page'] * 256 + p['tile'] for n in targets
             for p in composition_frame(original_parts, bank, n)['parts']}
    reserved = set(range(len(texture) // 128)) - owned
    nt, nparts, report = repack_frames(texture, repositioned, bank, targets, overrides,
                                     reserved_tiles=reserved, guard_uv_zero=True)
    for t in reserved:
        if tile_pixels(nt, t) != tile_pixels(texture, t):
            raise ValueError('Unowned atlas tile changed')
    report['unowned_tiles_preserved'] = len(reserved)
    report['part_coordinate_bytes_preserved'] = all(
        all(a[k] == b[k] for k in ('x', 'y'))
        for n in targets for a, b in zip(composition_frame(original_parts, bank, n)['parts'],
                                        composition_frame(nparts, bank, n)['parts']))
    report['original_part_counts_preserved'] = True
    return nt, nparts, report


def verify(originals, edited, arc):
    model = {'built_arc': arc}
    palette = entry(arc, 9)[:32]
    s, ns = originals['ST0E_U1.ARC'], edited['ST0E_U1.ARC']
    t, nt = entry(s, 0x10102), entry(ns, 0x10102)
    p, nparts = entry(s, 10), entry(ns, 10)
    def check_tile_scope(old_texture, new_texture, old_parts, new_parts, bank, ids):
        owned = {q['page'] * 256 + q['tile'] for n in ids
                 for q in composition_frame(old_parts, bank, n)['parts']}
        for tile in set(range(len(old_texture) // 128)) - owned:
            if tile_pixels(old_texture, tile) != tile_pixels(new_texture, tile):
                raise ValueError('Unowned UI texture changed')
        for n in ids:
            for q in composition_frame(new_parts, bank, n)['parts']:
                tile = q['page'] * 256 + q['tile']
                px = tile_pixels(new_texture, tile)
                if (tile % 16 == 0 and any(px[::16])) or (tile % 256 < 16 and any(px[:16])):
                    raise ValueError('Opaque UV0 boundary may clip under reflection')
    check_tile_scope(t[:40960], nt[:40960], p, nparts, 0, SELECTION_MAPPING)
    if nt[40960:] != t[40960:] or replace_entry(replace_entry(s, 0x10102, nt), 10, nparts) != ns:
        raise ValueError('Portrait/background/other select resource changed')
    allowed, counts = set(), {'selection_targets': 0, 'selection_other_frames': 0, 'save_other_frames': 0}
    for bank, lo, hi in ((0, 0, 40960), (1, 40960, 90112), (2, 90112, len(t))):
        for n in range(composition_frame(p, bank, 0)['bank_frame_count']):
            old, new = composition_frame(p, bank, n), composition_frame(nparts, bank, n)
            if len(old['parts']) != len(new['parts']):
                raise ValueError('Selection part count changed')
            if bank == 0 and n in SELECTION_MAPPING:
                if world(compose_static(nt[lo:hi], local_composition(new))) != world(actual_frame(model, *SELECTION_MAPPING[n])):
                    raise ValueError('Selection sprite resized, clipped, displaced or changed')
                for a, b in zip(old['parts'], new['parts']):
                    if any(a[k] != b[k] for k in ('flip_x', 'flip_y', 'unknown_flags', 'record_offset')):
                        raise ValueError('Selection flip/order changed')
                    if b['clut'] != (0 if n == 38 else a['clut']):
                        raise ValueError('Unexpected UI CLUT selector')
                    allowed.update(range(a['record_offset'], a['record_offset'] + 4))
                counts['selection_targets'] += 1
            else:
                if old != new or compose_static(t[lo:hi], local_composition(old))[:3] != compose_static(nt[lo:hi], local_composition(new))[:3]:
                    raise ValueError('Other selection frame changed')
                counts['selection_other_frames'] += 1
    if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(p, nparts))):
        raise ValueError('Selection headers or untargeted parts changed')
    col = originals['COL0E_U1.ARC']
    if replace_entry(col, 5, palette + entry(col, 5)[32:]) != edited['COL0E_U1.ARC']:
        raise ValueError('Other selection palette changed')
    menu, nm = originals['MOJIPAT.ARC'], edited['MOJIPAT.ARC']
    tex, ntex = entry(originals['LOAD_U.ARC'], 0x10008), entry(edited['LOAD_U.ARC'], 0x10008)
    check_tile_scope(tex, ntex, menu, nm, 2, [43])
    allowed = set(range(7108, 7140))
    for n in range(composition_frame(menu, 2, 0)['bank_frame_count']):
        a, b = composition_frame(menu, 2, n), composition_frame(nm, 2, n)
        if n == 43:
            if len(a['parts']) != len(b['parts']):
                raise ValueError('Save part count changed')
            for x, y in zip(a['parts'], b['parts']):
                if any(x[k] != y[k] for k in ('flip_x', 'flip_y', 'clut', 'unknown_flags', 'record_offset')):
                    raise ValueError('Save flips/CLUT/order changed')
                allowed.update(range(x['record_offset'], x['record_offset'] + 4))
            if world(compose_static(ntex, local_composition(b))) != world(actual_frame(model, 0, 147)):
                raise ValueError('Save sprite differs from accepted idle world pixels')
        else:
            if a != b or compose_static(tex, local_composition(a))[:3] != compose_static(ntex, local_composition(b))[:3]:
                raise ValueError('Other save frame changed')
            counts['save_other_frames'] += 1
    if nm[7108:7140] != palette or any(a != b and i not in allowed for i, (a, b) in enumerate(zip(menu, nm))):
        raise ValueError('Unexpected menu data/palette changed')
    if replace_entry(originals['LOAD_U.ARC'], 0x10008, ntex) != edited['LOAD_U.ARC']:
        raise ValueError('Other load resource changed')
    for name in originals:
        if len(originals[name]) != len(edited[name]):
            raise ValueError('Archive length changed')
    return {**counts, 'native_world_pixels_exact': True, 'clipped_opaque_pixels': 0,
            'source_art_rescaled': False, 'timing_headers_exact': True,
            'portrait_x_background_preserved': True, 'exe_changed': False,
            'black_palette_changed': False, 'runtime_verified': False}


def prepare(out):
    m, arc, config, originals = read_sources()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'originals').mkdir()
    for name, data in originals.items():
        (out / 'originals' / name).write_bytes(data)
    s = originals['ST0E_U1.ARC']
    t, p = entry(s, 0x10102), entry(s, 10)
    if struct.unpack('<3I', entry(s, 12)) != (0, 40960, 90112):
        raise ValueError('Unexpected select bank layout')
    rp, targets, layouts = register(p, 0, SELECTION_MAPPING, t[:40960], arc)
    nt, nparts, select_report = protected_repack(t[:40960], p, rp, 0, targets, {38: 0})
    edited = {'ST0E_U1.ARC': replace_entry(replace_entry(s, 0x10102, nt + t[40960:]), 10, nparts)}
    palette = entry(arc, 9)[:32]
    words = struct.unpack('<16H', palette)
    col = originals['COL0E_U1.ARC']
    edited['COL0E_U1.ARC'] = replace_entry(col, 5, palette + entry(col, 5)[32:])
    menu, load = originals['MOJIPAT.ARC'], originals['LOAD_U.ARC']
    tex = entry(load, 0x10008)
    rm, save_targets, _ = register(menu, 2, {43: (0, 147)}, tex, arc, layouts[0])
    ntex, nm, save_report = protected_repack(tex, menu, rm, 2, save_targets)
    edited['MOJIPAT.ARC'] = nm[:7108] + palette + nm[7140:]
    edited['LOAD_U.ARC'] = replace_entry(load, 0x10008, ntex)
    verification = verify(originals, edited, arc)
    for name, data in edited.items():
        (out / name).write_bytes(data)
    for n in targets:
        save_image(*targets[n], words, out / f'select_{n:03d}.png')
    save_image(*save_targets[43], words, out / 'save_043.png')
    # Native world-aligned comparison sheet; technical preview only.
    board = Image.new('RGB', (8 * 192, 4 * 216), (38, 44, 57))
    draw = ImageDraw.Draw(board)
    for i, n in enumerate(targets):
        c = composition_frame(nparts, 0, n)
        px, sz, bb, _ = compose_static(nt, local_composition(c))
        im = save_image(px, sz, words, out / f'select_{n:03d}.png').convert('RGBA')
        x, y = i % 8 * 192, i // 8 * 216
        draw.text((x + 4, y + 4), f'UI {n} / {SELECTION_MAPPING[n]}', fill='white')
        im = im.resize((sz[0] * 2, sz[1] * 2), Image.Resampling.NEAREST)
        board.paste(im, (x + 80 + bb[0] * 2, y + 112 + bb[1] * 2), im)
    board.save(out / 'selection_review.png')
    recipe = {'kind': 'rin_selection_save_small', 'parent': PARENT.relative_to(ROOT).as_posix(),
              'parent_sha256': PARENT_SHA, 'parent_manifest_sha256': digest(PARENT / 'manifest.json'),
              'parent_arc_sha256': sha(arc), 'config_sha256': digest(CONFIG),
              'mapping': {str(n): list(v) for n, v in SELECTION_MAPPING.items()},
              'selection_atlas': select_report, 'save_atlas': save_report,
              'files': [{'source': rec, 'file': rec['path'].split('/')[-1].split(';')[0],
                         'sha256': sha(edited[rec['path'].split('/')[-1].split(';')[0]])} for rec in config['archives']],
              'verification': verification}
    (out / 'recipe.json').write_text(json.dumps(recipe, indent=2) + '\n', 'utf8')
    print(json.dumps({'output': str(out), 'verification': verification, 'packing': [select_report, save_report]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
