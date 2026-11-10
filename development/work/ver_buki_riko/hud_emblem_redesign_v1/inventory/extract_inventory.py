"""Read-only game extraction; writes only this isolated inventory directory."""
import collections
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from scripts.inventory_shibuki_ui import sheet
from src.psx_ui_atlas import aliased_composition, local_composition
from src.psx_static_effect import compose_static

OUT = Path(__file__).resolve().parent
BUILD = ROOT / 'out/ver_buki_riko/korean_20261028T060610973785Z'
EXPECTED = '03b0160edea2087f8c3b81d6187842085beef9954e08565a688ac409dfc3277d'
SOURCE_SHA = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
NAMES = ['PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC']
TILES = {'PL00_U.ARC': [205, 206, 213, 214],
         'PL01_U.ARC': [469, 470, 471, 472],
         'PL02_U.ARC': [205, 206, 213, 214]}
RECT = (-19, 26, 4, 39)


def main():
    original_bin = ROOT / 'MegaMan X4.bin'
    latest_bin = BUILD / 'shibuki_riko.bin'
    assert digest(original_bin) == SOURCE_SHA
    assert digest(latest_bin) == EXPECTED
    records = {r['name'].split(';')[0]: r for r in json.loads(
        (ROOT / 'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())}
    sources = {}
    for label, path in [('original', original_bin), ('current', latest_bin)]:
        with path.open('rb') as stream:
            disc = DiscReader(stream, path.stat().st_size)
            sources[label] = {name: disc.read(r['lba'], r['size']) for name, r in records.items()
                              if name in NAMES or name.startswith('COL')}
    old_palette = (ROOT / 'work/ver_buki_riko/art_pilot/hud_mark_v1/hud_palette.bin').read_bytes()
    palette = entry(sources['current']['COL00_0X.ARC'], 5)[17 * 32:18 * 32]
    assert palette == old_palette
    words = struct.unpack('<16H', palette)
    (OUT / 'native_hud_palette.bin').write_bytes(palette)
    colors = [[(word >> shift & 31) * 255 // 31 for shift in (0, 5, 10)] for word in words]
    pal_image = Image.new('RGB', (8 * 84, 2 * 66), (35, 37, 44))
    draw = ImageDraw.Draw(pal_image)
    for i, rgb in enumerate(colors):
        x, y = i % 8 * 84, i // 8 * 66
        draw.rectangle((x + 3, y + 3, x + 80, y + 42), fill=tuple(rgb))
        draw.text((x + 3, y + 46), f'{i:02} {words[i]:04X}', fill='white')
    pal_image.save(OUT / 'palette.png')
    palette_sources = []
    palette_differences = []
    for name, raw in sources['current'].items():
        if not name.startswith('COL'):
            continue
        row = entry(raw, 5)[544:576]
        record = {'file': name, 'lba': records[name]['lba'], 'entry': 5,
                  'row': 17, 'entry_offset': 544, 'archive_offset': 2592,
                  'equals_original_row': row == entry(sources['original'][name], 5)[544:576]}
        if row == palette:
            palette_sources.append(record)
        else:
            record['words'] = list(struct.unpack('<16H', row))
            palette_differences.append(record)
    report = {'kind': 'hud_emblem_readonly_inventory', 'bin_modified': False,
              'runtime_tested': False, 'source_sha256': SOURCE_SHA, 'parent_sha256': EXPECTED,
              'palette': {'clut': '0x7841', 'vram_xy': [16, 481], 'words': list(words),
                          'rgb': colors, 'sha256': sha256(palette),
                          'matching_COL_rows': palette_sources,
                          'nonmatching_COL_rows': palette_differences},
              'native_layout': {'exe_draw_address': '0x80025188', 'layout_address': '0x800F30F4',
                                'layout_exe_file_offset': '0xE38F4', 'frame_anchor': [32, 56],
                                'lives_anchor': [39, 88], 'safe_world_rect_exclusive': RECT,
                                'safe_screen_rect_exclusive': [13, 82, 36, 95],
                                'hp_variants': list(range(32, 49, 2)),
                                'frame_formula': '(max_hp - 0x20) / 2 + 0x45'},
              'archives': {}, 'frames': []}
    full_items, crop_items, inner_items = [], [], []
    for name in NAMES:
        current = sources['current'][name]
        assert current == (BUILD / name).read_bytes()
        parts = entry(current, 3)
        texture = entry(current, 0x10206)
        consumers = collections.defaultdict(list)
        banks = []
        for bank in range(struct.unpack_from('<I', parts)[0] // 4):
            count = aliased_composition(parts, bank, 0)['bank_frame_count']
            banks.append({'bank': bank, 'frames': count})
            for frame in range(count):
                comp = aliased_composition(parts, bank, frame)
                for part in comp['parts']:
                    tile = part['page'] * 256 + part['tile']
                    if tile in TILES[name]:
                        assert bank == 1 and 69 <= frame <= 77
                        consumers[tile].append([bank, frame, part['index']])
        report['archives'][name] = {'lba': records[name]['lba'], 'size': len(current),
            'sha256': sha256(current), 'sidecar_matches_disc': True,
            'entries': [e for e in psx_arc(current) if e['type'] in ('0x3', '0x9', '0x10206')],
            'dedicated_emblem_tiles': TILES[name], 'emblem_tile_consumers_all_banks': dict(consumers),
            'banks_scanned': banks}
        for frame in range(69, 78):
            decoded = {}
            for label in ['original', 'current']:
                raw = sources[label][name]
                comp = aliased_composition(entry(raw, 3), 1, frame)
                px, size, bounds, provenance = compose_static(entry(raw, 0x10206), local_composition(comp))
                arr = np.frombuffer(px, np.uint8).reshape(size[1], size[0])
                decoded[label] = (arr, size, bounds, comp)
            a, size, bounds, comp = decoded['current']
            orig, origsize, origbounds, origcomp = decoded['original']
            assert size == origsize and bounds == origbounds
            ys, xs = np.indices(a.shape)
            allowed = ((xs + bounds[0] >= RECT[0]) & (xs + bounds[0] < RECT[2]) &
                       (ys + bounds[1] >= RECT[1]) & (ys + bounds[1] < RECT[3]))
            iy, ix = RECT[1] - bounds[1], RECT[0] - bounds[0]
            mask = (orig[iy:iy + 13, ix:ix + 23] != 0).astype('uint8') * 255
            row = {'file': name, 'frame': frame, 'hp': 32 + (frame - 69) * 2,
                   'size': size, 'bounds': bounds, 'screen_bounds': [bounds[0] + 32, bounds[1] + 56,
                   bounds[2] + 32, bounds[3] + 56], 'parts': comp['parts'],
                   'current_pixels_sha256': sha256(a.tobytes()), 'original_pixels_sha256': sha256(orig.tobytes()),
                   'alpha_equals_original': bool(np.array_equal(a != 0, orig != 0)),
                   'outside_safe_rect_equals_original': bool(np.all(a[~allowed] == orig[~allowed])),
                   'safe_rect_opaque_pixels': int(np.count_nonzero(mask)),
                   'safe_rect_transparent_pixels': int(np.count_nonzero(mask == 0))}
            report['frames'].append(row)
            if frame != 69 and frame != 77:
                continue
            for label, (arr, sz, bb, _) in decoded.items():
                stem = f'{name[:-4]}_{label}_f{frame}'
                im = save_image(arr.tobytes(), sz, words, OUT / f'{stem}.png').convert('RGBA')
                if frame == 69:
                    # Full 48x32 native lower HUD includes the right numeral ring.
                    crop = im.crop((0, 15 - bb[1], 48, 47 - bb[1]))
                    crop.save(OUT / f'{name[:-4]}_{label}_lower48x32.png')
                    crop_items.append((f'{name[:-4]} {label} lower', crop.resize((384, 256), Image.Resampling.NEAREST)))
                    inner = im.crop((RECT[0] - bb[0], RECT[1] - bb[1], RECT[2] - bb[0], RECT[3] - bb[1]))
                    inner.save(OUT / f'{name[:-4]}_{label}_inner23x13.png')
                    inner_items.append((f'{name[:-4]} {label} inner', inner.resize((368, 208), Image.Resampling.NEAREST)))
                full_items.append((f'{name[:-4]} {label} HP{row["hp"]}', im.resize((sz[0] * 4, sz[1] * 4), Image.Resampling.NEAREST)))
            if frame == 69:
                Image.fromarray(mask).save(OUT / f'{name[:-4]}_native_inner_alpha_mask23x13.png')
    for name in NAMES:
        rows = [r for r in report['frames'] if r['file'] == name]
        assert all(r['alpha_equals_original'] and r['outside_safe_rect_equals_original'] for r in rows)
    report['shibuki_normal_ultimate_hud_equal'] = all(
        next(r for r in report['frames'] if r['file'] == 'PL00_U.ARC' and r['frame'] == f)['current_pixels_sha256'] ==
        next(r for r in report['frames'] if r['file'] == 'PL02_U.ARC' and r['frame'] == f)['current_pixels_sha256']
        for f in range(69, 78))
    assert report['shibuki_normal_ultimate_hud_equal']
    sheet(full_items, OUT / 'full_hud_original_current_4x.png', 4, (210, 355))
    sheet(crop_items, OUT / 'lower_hud_original_current_8x.png', 2, (400, 290))
    sheet(inner_items, OUT / 'inner_emblems_original_current_16x.png', 2, (390, 240))
    (OUT / 'inventory.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'output': str(OUT), 'frames': len(report['frames']),
        'palette_matching_rows': len(palette_sources), 'palette_nonmatching_rows': len(palette_differences),
        'safe_mask': [{k: r[k] for k in ('file', 'safe_rect_opaque_pixels', 'safe_rect_transparent_pixels')}
                      for r in report['frames'] if r['frame'] == 69]}))


if __name__ == '__main__':
    main()
