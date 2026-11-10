"""Prepare two 23x13 HUD index overlays without changing parts, UVs or alpha.

PNG inputs must be P or L mode with index values 0..15. Index 0 means KEEP
the accepted pixel, never erase it; 1..15 replace an opaque native pixel.
The PNG palette is only a display aid: game colors use the existing HUD CLUT.
No resizing, palette quantization, RGB conversion or game-BIN writes occur.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.project import digest
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition, local_composition, tile_pixels

WORK = ROOT / 'work/ver_buki_riko/hud_emblem_redesign_v1'
PARENT = ROOT / 'out/ver_buki_riko/korean_20261028T060610973785Z'
PARENT_SHA = '03b0160edea2087f8c3b81d6187842085beef9954e08565a688ac409dfc3277d'
SOURCE_SHA = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
ORIGINAL = ROOT / 'MegaMan X4.bin'
KIND = 'hud_emblems_native_overlay_v1'
RECT = (-19, 26, 4, 39)  # Exclusive right/bottom, 23x13 native pixels.
TARGETS = {(1, frame) for frame in range(69, 78)}
RECORDS = {
    'PL00_U.ARC': {'lba': 1135, 'size': 796672, 'sha256': '92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a'},
    'PL01_U.ARC': {'lba': 1525, 'size': 741376, 'sha256': '35414320eff2bb0a196b88f70ccd69ecfe9adb25c4ed5c82f24a96efd3c35359'},
    'PL02_U.ARC': {'lba': 1887, 'size': 796672, 'sha256': 'fa8accf20e35634120fd4fc59bac1f31b0fdadaf639b06a783e92189e93c8042'},
}
CHARACTERS = {'PL00_U.ARC': 'shibuki', 'PL01_U.ARC': 'riko', 'PL02_U.ARC': 'shibuki'}
EXCLUSIVE_TILES = {'PL00_U.ARC': {205, 206, 213, 214},
                   'PL01_U.ARC': {469, 470, 471, 472},
                   'PL02_U.ARC': {205, 206, 213, 214}}
INPUT_CONTRACT = {'format': 'PNG P or L, exact raw index values; no image conversion',
                  'size': [23, 13], 'indices': [0, 15],
                  'zero': 'keep accepted current pixel; not transparent erasure',
                  'nonzero': 'replace opaque pixel with native HUD palette index',
                  'world_rect_exclusive': list(RECT),
                  'opaque_input_on_original_transparency': 'rejected',
                  'palette': 'unchanged native stage HUD CLUT 0x7841 / COL entry5 row17'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def protected_hashes():
    require(digest(ORIGINAL) == SOURCE_SHA, 'Original US BIN hash differs')
    require(digest(PARENT / 'shibuki_riko.bin') == PARENT_SHA, 'Accepted parent BIN hash differs')
    manifest = json.loads((PARENT / 'manifest.json').read_text('utf-8'))
    require(manifest['modified_bin']['sha256'] == PARENT_SHA, 'Parent manifest hash differs')


def load_inputs():
    protected_hashes()
    original, current = {}, {}
    for path, values in ((ORIGINAL, original), (PARENT / 'shibuki_riko.bin', current)):
        with path.open('rb') as stream:
            reader = DiscReader(stream, path.stat().st_size)
            for name, record in RECORDS.items():
                values[name] = reader.read(record['lba'], record['size'])
                if path == ORIGINAL:
                    require(sha256(values[name]) == record['sha256'], f'Original resource differs: {name}')
            if path != ORIGINAL:
                # Verified US COL00_0X record; palette is read from this parent.
                palette = entry(reader.read(32, 6144), 5)[17 * 32:18 * 32]
                require(len(palette) == 32, 'Incomplete native HUD palette')
    return original, current, palette


def read_overlay(path):
    path = Path(path).resolve()
    with Image.open(path) as picture:
        require(picture.format == 'PNG', 'HUD input must be PNG')
        require(picture.mode in ('P', 'L'), 'HUD input must contain explicit indices (P or L mode)')
        require(picture.size == (23, 13), 'HUD input must be exactly 23x13; automatic resize refused')
        require(getattr(picture, 'n_frames', 1) == 1, 'Animated PNG input refused')
        values = np.array(picture, dtype=np.uint8)
        require(values.shape == (13, 23) and int(values.max()) <= 15, 'HUD input contains a non-4bpp index')
    return values


def all_compositions(parts):
    count = struct.unpack_from('<I', parts)[0] // 4
    return {(bank, frame): aliased_composition(parts, bank, frame)
            for bank in range(count)
            for frame in range(aliased_composition(parts, bank, 0)['bank_frame_count'])}


def static_banks(name):
    return {1, 2, 3, 4, 6} if name == 'PL01_U.ARC' else {1, 2, 3, 4, *range(9, 22)}


def composed(texture, composition):
    pixels, size, bounds, sources = compose_static(texture, local_composition(composition))
    return np.frombuffer(pixels, np.uint8).reshape(size[1], size[0]), size, bounds, sources


def inner_slice(bounds):
    left, top, right, bottom = RECT
    require(bounds[0] <= left < right <= bounds[2] and bounds[1] <= top < bottom <= bounds[3],
            'Native HUD frame does not cover the declared emblem rectangle')
    return slice(top - bounds[1], bottom - bounds[1]), slice(left - bounds[0], right - bounds[0])


def patch_archive(name, original, current, overlay):
    require(name in RECORDS, 'Unexpected player archive')
    require(overlay.shape == (13, 23) and np.issubdtype(overlay.dtype, np.integer)
            and int(overlay.min()) >= 0 and int(overlay.max()) <= 15, 'Invalid overlay array')
    texture, parts = entry(current, 0x10206), entry(current, 3)
    old_texture, old_parts = entry(original, 0x10206), entry(original, 3)
    comps = all_compositions(parts)
    users = {}
    for key, comp in comps.items():
        for part in comp['parts']:
            users.setdefault(part['page'] * 256 + part['tile'], set()).add(key)
    exclusive = EXCLUSIVE_TILES[name]
    require(all(users.get(tile) and users[tile] <= TARGETS for tile in exclusive),
            'Accepted emblem tile is shared with another composition')
    result = bytearray(texture)
    demands, frames, targets = {}, [], {}
    for key in sorted(TARGETS):
        comp = comps[key]
        before, size, bounds, sources = composed(texture, comp)
        native, native_size, native_bounds, _ = composed(old_texture, aliased_composition(old_parts, *key))
        require(size == native_size and bounds == native_bounds, 'HUD geometry differs from original')
        require(np.array_equal(before > 0, native > 0), 'Accepted HUD already differs from original alpha')
        ys, xs = inner_slice(bounds)
        outside = np.ones(before.shape, bool)
        outside[ys, xs] = False
        require(np.array_equal(before[outside], native[outside]), 'Accepted frame outside emblem differs from original')
        require(not np.any((overlay != 0) & (native[ys, xs] == 0)),
                f'{name} frame{key[1]}: nonzero overlay would paint native transparent pixels')
        after = before.copy()
        region = after[ys, xs]
        region[overlay != 0] = overlay[overlay != 0]
        require(np.array_equal(after > 0, native > 0), 'Overlay changed native alpha')
        for y, x in zip(*np.where(after != before)):
            locations = sources[int(y) * size[0] + int(x)]
            # Only the last opaque source draws this final indexed pixel.
            visible = [(offset, shift) for offset, shift in locations if (texture[offset] >> shift) & 15]
            require(bool(visible), 'Opaque pixel has no visible native tile source')
            offset, shift = visible[-1]
            texture_y, row_byte = divmod(offset, 128)
            tile = texture_y // 16 * 16 + row_byte // 8
            require(tile in exclusive, 'Emblem change leaves its exclusive native tiles')
            value = int(after[y, x])
            location = (offset, shift)
            require(location not in demands or demands[location] == value, 'Shared HUD pixel has conflicting frame demands')
            demands[location] = value
        targets[key] = after
        frames.append({'bank': key[0], 'frame': key[1], 'size': list(size), 'bounds': list(bounds),
                       'changed_pixels': int(np.count_nonzero(after != before)),
                       'alpha_equals_original': True, 'outside_emblem_equals_original': True,
                       'inside_original_transparent_pixels': int(np.count_nonzero(native[ys, xs] == 0))})
    for (offset, shift), value in demands.items():
        result[offset] = (result[offset] & ~(15 << shift)) | (value << shift)
    result = bytes(result)
    checked = 0
    for key, comp in comps.items():
        if key[0] not in static_banks(name):
            continue
        before, size, bounds, _ = composed(texture, comp)
        after, other_size, other_bounds, _ = composed(result, comp)
        require(size == other_size and bounds == other_bounds, 'Static frame geometry changed')
        require(np.array_equal(after, targets.get(key, before)), f'Non-target or target static frame mismatch: {name} {key}')
        checked += 1
    for tile in range(len(texture) // 128):
        if tile not in exclusive:
            require(tile_pixels(texture, tile) == tile_pixels(result, tile), 'Nonexclusive texture tile changed')
    output = replace_entry(current, 0x10206, result)
    layout = lambda data: [{key: value for key, value in item.items() if key != 'sha256'} for item in psx_arc(data)]
    require(len(output) == len(current) and layout(output) == layout(current), 'ARC length, entry sizes or offsets changed')
    require(entry(output, 3) == parts, 'Native parts or UVs changed')
    for descriptor in psx_arc(current):
        if descriptor['type'] != '0x10206':
            lo, length = descriptor['offset'], descriptor['size']
            require(output[lo:lo + length] == current[lo:lo + length], 'Nontexture ARC entry changed')
    texture_descriptor = next(d for d in psx_arc(current) if d['type'] == '0x10206')
    lo, hi = texture_descriptor['offset'], texture_descriptor['offset'] + texture_descriptor['size']
    require(output[:lo] == current[:lo] and output[hi:] == current[hi:], 'ARC bytes outside texture changed')
    return output, {'frames': frames, 'world_rect_exclusive': list(RECT),
                    'exclusive_tiles': sorted(exclusive), 'tile_users': {str(t): [list(k) for k in sorted(users[t])] for t in sorted(exclusive)},
                    'static_compositions_checked': checked, 'nontarget_static_compositions_preserved': checked - len(TARGETS),
                    'all_bank_part_references_scanned': len(comps), 'static_banks': sorted(static_banks(name)),
                    'changed_nibbles': len(demands), 'changed_texture_bytes': sum(a != b for a, b in zip(texture, result)),
                    'parts_uv_geometry_order_clut_flips_unchanged': True, 'palette_unchanged': True,
                    'original_alpha_preserved': True, 'outside_emblem_equals_original': True,
                    'all_other_arc_entries_and_padding_unchanged': True,
                    'compressed_body_armor_animation_text_entries_preserved': True,
                    'texture_entry': '0x10206', 'runtime_verified': False}


def render_pixels(array, palette):
    words = struct.unpack('<16H', palette)
    colors = np.array([((w & 31) * 255 // 31, ((w >> 5) & 31) * 255 // 31,
                        ((w >> 10) & 31) * 255 // 31, 255 if i else 0)
                       for i, w in enumerate(words)], np.uint8)
    return Image.fromarray(colors[array])


def preview(current, changed, palette, output):
    items = []
    for name in RECORDS:
        for number in (69, 77):
            for label, data in (('이전', current[name]), ('수정', changed[name])):
                array, size, bounds, _ = composed(entry(data, 0x10206), aliased_composition(entry(data, 3), 1, number))
                image = render_pixels(array, palette)
                filename = f'{name}_{number}_{"before" if label == "이전" else "after"}.png'
                image.save(output / filename)
                items.append((f'{name} / {number} / {label} · 정적 자산', image))
    cell = (330, 440)
    board = Image.new('RGB', (cell[0] * 4, cell[1] * 3), '#263343')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 14)
    for i, (label, image) in enumerate(items):
        x, y = i % 4 * cell[0], i // 4 * cell[1]
        draw.text((x + 5, y + 5), label, fill='white', font=font)
        image = image.resize((image.width * 4, image.height * 4), Image.Resampling.NEAREST)
        require(image.width <= cell[0] - 12 and image.height <= cell[1] - 34, 'HUD preview clips the native frame')
        board.paste(image, (x + 8, y + 30), image)
    board.save(output / 'hud_comparison.png')


def prepare(shibuki, riko, output):
    output = Path(output).resolve()
    require(output.is_relative_to(WORK.resolve()) and output != WORK.resolve(), 'Output must be a new task work subdirectory')
    require(not output.exists(), 'Output already exists')
    paths = {'shibuki': Path(shibuki).resolve(), 'riko': Path(riko).resolve()}
    overlays = {name: read_overlay(path) for name, path in paths.items()}
    original, current, palette = load_inputs()
    changed, checks = {}, {}
    for name in RECORDS:
        changed[name], checks[name] = patch_archive(name, original[name], current[name], overlays[CHARACTERS[name]])
        require(changed[name] != current[name], f'Input does not change the requested emblem: {name}')
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, data in changed.items():
        (output / name).write_bytes(data)
        files[name] = {'record': RECORDS[name], 'before': sha256(current[name]), 'after': sha256(data), 'size': len(data)}
    art = {}
    for character, path in paths.items():
        copy_name = f'{character}_indices.png'
        (output / copy_name).write_bytes(path.read_bytes())
        art[character] = {'file': copy_name, 'input_path': str(path), 'sha256': digest(path),
                          'indices_sha256': sha256(overlays[character].tobytes()), 'indices_used': sorted(np.unique(overlays[character]).tolist())}
    (output / 'native_hud_palette.bin').write_bytes(palette)
    preview(current, changed, palette, output)
    recipe = {'kind': KIND, 'parent_build': str(PARENT.relative_to(ROOT)), 'parent_sha256': PARENT_SHA,
              'source_sha256': SOURCE_SHA, 'input_contract': INPUT_CONTRACT, 'art': art, 'files': files,
              'checks': checks, 'native_palette_sha256': sha256(palette),
              'bin_applied': False, 'runtime_verified': False, 'exe_changed': False,
              'parts_or_uv_changed': False, 'resource_lengths_and_lbas_preserved': True}
    protected_hashes()
    (output / 'recipe.json').write_text(json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(output), 'changed_resources': len(files), 'frames': 27,
                      'bin_applied': False, 'runtime_verified': False}, ensure_ascii=False))
    return output


def validate_candidate(candidate):
    candidate = Path(candidate).resolve()
    require(candidate.is_relative_to(WORK.resolve()), 'Candidate leaves the task work directory')
    recipe = json.loads((candidate / 'recipe.json').read_text('utf-8'))
    require(recipe['kind'] == KIND and recipe['parent_sha256'] == PARENT_SHA and recipe['source_sha256'] == SOURCE_SHA,
            'Unsupported HUD candidate or parent hash')
    require(recipe['parent_build'] == str(PARENT.relative_to(ROOT)) and recipe['input_contract'] == INPUT_CONTRACT,
            'Candidate input contract or parent path differs')
    require(set(recipe['files']) == set(RECORDS) and set(recipe['art']) == {'shibuki', 'riko'}, 'Wrong candidate resource or art set')
    original, current, palette = load_inputs()
    require(sha256(palette) == recipe['native_palette_sha256'], 'Native HUD palette differs')
    require((candidate / 'native_hud_palette.bin').read_bytes() == palette, 'Candidate preview palette differs from native HUD palette')
    overlays = {}
    for character, record in recipe['art'].items():
        require(record['file'] == f'{character}_indices.png', 'Unexpected candidate art path')
        path = candidate / record['file']
        require(digest(path) == record['sha256'], 'Candidate input image changed')
        overlays[character] = read_overlay(path)
        require(sha256(overlays[character].tobytes()) == record['indices_sha256'], 'Input index bytes changed')
    changes = {}
    for name, record in recipe['files'].items():
        require(record['record'] == RECORDS[name] and record['before'] == sha256(current[name]), 'Candidate resource source differs')
        expected, checks = patch_archive(name, original[name], current[name], overlays[CHARACTERS[name]])
        actual = (candidate / name).read_bytes()
        require(actual == expected and actual != current[name], 'Candidate resource does not reproduce from accepted parent and supplied overlay')
        require(len(actual) == record['size'] == RECORDS[name]['size'] and sha256(actual) == record['after'], 'Candidate resource hash/length differs')
        require(checks == recipe['checks'][name], 'Candidate preservation checks do not reproduce')
        changes[name] = actual
    protected_hashes()
    return recipe, current, changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shibuki', type=Path, required=True)
    parser.add_argument('--riko', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.shibuki, args.riko, args.output)
