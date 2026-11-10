"""Verify three title labels against saved native RAM/VRAM; no emulator access."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.verify_korean_runtime_page import digest, native_draw_buffers, require
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition, local_composition

TITLE_INITS = 0x10E71C
MENU = ((2, 2, '게임 시작', 128), (13, 29, '이어하기', 144),
        (14, 30, '설정', 160))
PALETTE_SOURCE = ROOT / 'work/ver_buki_riko/korean_v1/ui_inventory/COL0E_U0.ARC'


def rooted(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def expected_menu(resource, exe, ram):
    """Decode resource parts and actual US EXE init data without proposal checks."""
    load_address = struct.unpack_from('<I', exe, 0x18)[0] & 0x1FFFFFFF
    table_offset = TITLE_INITS - load_address + 2048
    table = exe[table_offset:table_offset + 0x84]
    require(len(table) == 0x84, 'Incomplete US title object init table')
    require(ram[TITLE_INITS:TITLE_INITS + len(table)] == table,
            'Captured RAM and build title object init tables differ')
    texture = entry(resource, 0x10002)
    parts = struct.pack('<I', 4) + entry(resource, 0x12)
    result = []
    for index, frame, label, expected_y in MENU:
        x, y, sprite, palette_row = struct.unpack_from('<hhBB', table, index * 6)
        require((x, y, sprite, palette_row) == (160, expected_y, frame, 7),
                f'Unexpected native title object init: {index}')
        composition = local_composition(aliased_composition(parts, 0, frame))
        pixels, (width, height), bounds, _ = compose_static(texture, composition)
        ink = [(x + bounds[0] + n % width, y + bounds[1] + n // width, value)
               for n, value in enumerate(pixels) if value]
        require(ink, f'Empty title label: {frame}')
        left = min(p[0] for p in ink)
        top = min(p[1] for p in ink)
        right = max(p[0] for p in ink) + 1
        bottom = max(p[1] for p in ink) + 1
        result.append({'frame': frame, 'label': label, 'init_index': index,
                       'anchor': [x, y], 'composition_bounds': list(bounds),
                       'composition_size': [width, height],
                       'ink_bounds_exclusive': [left, top, right, bottom],
                       'ink_center_x': (left + right) / 2,
                       'ink_bottom_exclusive': bottom,
                       'ink_pixels': len(ink), 'palette_indices': sorted({p[2] for p in ink}),
                       'pixels_sha256': digest(pixels), '_ink': ink})
    # Index 15 is the selection overlay. title_draw sets its frame and y to
    # the selected menu row; its original palette row is 6 (inactive rows 7).
    require(struct.unpack_from('<hhBB', table, 15 * 6) == (160, 128, 2, 6),
            'Unexpected native selected-menu overlay init')
    return result, table


def compare_buffer(vram, buffer, frames, palettes):
    clip_x, clip_y, width, height = buffer['draw_clip']
    offset_x, offset_y = buffer['draw_offset']
    checks = []
    for frame in frames:
        palette_checks = []
        for row, palette in palettes.items():
            matching = 0
            mismatches = []
            for x, y, index in frame['_ink']:
                xx, yy = offset_x + x, offset_y + y
                require(clip_x <= xx < clip_x + width and clip_y <= yy < clip_y + height,
                        'Title ink leaves native framebuffer')
                actual = struct.unpack_from('<H', vram, (yy * 1024 + xx) * 2)[0]
                expected = palette[index]
                # Framebuffer bit15 is a mask, not visible RGB.
                if actual & 0x7FFF == expected & 0x7FFF:
                    matching += 1
                elif len(mismatches) < 8:
                    mismatches.append({'screen': [x, y], 'vram': [xx, yy],
                                       'actual': hex(actual), 'expected': hex(expected)})
            palette_checks.append({'palette_row': row,
                                   'state': 'selected' if row == 6 else 'inactive',
                                   'matching_ink_pixels': matching,
                                   'ink_pixels': frame['ink_pixels'],
                                   'all_ink_matches': matching == frame['ink_pixels'],
                                   'first_mismatches': mismatches})
        matching_rows = [p['palette_row'] for p in palette_checks if p['all_ink_matches']]
        checks.append({'frame': frame['frame'], 'label': frame['label'],
                       'matching_palette_rows': matching_rows,
                       'whole_label_matches': bool(matching_rows),
                       'palette_checks': palette_checks})
    return {'draw_info': buffer, 'labels': checks,
            'all_three_labels_match': all(c['whole_label_matches'] for c in checks)}


def verify(capture):
    evidence = json.loads((capture / 'evidence.json').read_text('utf-8'))
    require(len(evidence['ram_bases']) == len(evidence['vram_bases']) == 1,
            'Capture must contain exactly one native RAM and VRAM')
    ram = (capture / f"ram_{evidence['ram_bases'][0]}.bin").read_bytes()
    vram = (capture / f"vram_{evidence['vram_bases'][0]}.bin").read_bytes()
    require(len(ram) == 0x200000 and len(vram) == 0x100000, 'Invalid native memory sizes')
    session_path = rooted(evidence['session']) / 'session.local.json'
    session = json.loads(session_path.read_text('utf-8'))
    require(evidence['bin_sha256'] == session['bin_sha256'], 'Session/capture build mismatch')
    build = rooted(session['cue']).parent
    resource = (build / 'ST0E_U0.ARC').read_bytes()
    exe = (build / 'SLUS_005.61').read_bytes()
    frames, table = expected_menu(resource, exe, ram)
    preserved_palette = PALETTE_SOURCE.read_bytes()
    palette_entry = entry(preserved_palette, 5)
    palettes = {row: struct.unpack_from('<16H', palette_entry, row * 32) for row in (6, 7)}
    # Verify the build did not change either palette row when it includes COL.
    build_palette = build / 'COL0E_U0.ARC'
    if build_palette.exists():
        actual_palette = entry(build_palette.read_bytes(), 5)
        require(all(actual_palette[row * 32:(row + 1) * 32] ==
                    palette_entry[row * 32:(row + 1) * 32] for row in (6, 7)),
                'Build title menu palette differs from preserved source')
    checks = [compare_buffer(vram, buffer, frames, palettes) for buffer in native_draw_buffers(ram)]
    centers = [f['ink_center_x'] for f in frames]
    bottoms = [f['ink_bottom_exclusive'] for f in frames]
    gaps = [b - a for a, b in zip(bottoms, bottoms[1:])]
    # Odd/even raster widths place geometric centres half a pixel apart on
    # an integer grid; baseline rows and the native object anchors stay exact.
    alignment = all(abs(c-160)<=0.5 for c in centers) and gaps == [16, 16]
    return {'kind': 'captured_native_korean_title_menu_verification',
            'capture': str(capture), 'session_metadata': str(session_path), 'build': str(build),
            'bin_sha256': evidence['bin_sha256'], 'ram_sha256': digest(ram),
            'vram_sha256': digest(vram), 'title_resource_sha256': digest(resource),
            'build_exe_sha256': digest(exe),
            'native_title_init_address': hex(TITLE_INITS | 0x80000000),
            'native_title_init_sha256': digest(table), 'native_title_init_matches_ram': True,
            'palette_source': str(PALETTE_SOURCE), 'palette_source_sha256': digest(preserved_palette),
            'palettes': {str(row): [hex(v) for v in pal] for row, pal in palettes.items()},
            'frames': [{k: v for k, v in frame.items() if k != '_ink'} for frame in frames],
            'ink_centers_x': centers, 'ink_bottom_intervals': gaps,
            'expected_alignment_verified': alignment, 'framebuffer_checks': checks,
            'captured_title_menu_verified': alignment and any(c['all_three_labels_match'] for c in checks),
            'scope': 'Three composed labels at native EXE anchors: every nontransparent ink pixel must match one complete selected/inactive palette per label, all in the same actual DrawInfo framebuffer. No screenshot search, coordinate fitting, background or other screen verification.',
            'source_basis': ['work/research/decomp/config/symbols.us.txt: title_object_inits',
                             'work/research/decomp/include/main/misc/misc_19_title.h: TitleObjectInit',
                             'work/research/decomp/src/main/misc/misc_19_title.c: title_init/title_draw',
                             'work/research/decomp/src/main/2824.c: DrawInfo framebuffers'],
            'emulator_accessed': False, 'process_memory_written': False, 'keys_sent': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.capture)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({key: result[key] for key in ('capture', 'bin_sha256', 'ink_centers_x',
                      'ink_bottom_intervals', 'captured_title_menu_verified')}, ensure_ascii=False))
    sys.exit(0 if result['captured_title_menu_verified'] else 1)
