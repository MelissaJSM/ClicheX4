"""US Zero death orbs: native mint CLUT, fixed-size atlas, protected effects."""
import hashlib
import json
from pathlib import Path

from scripts.prepare_riko_ui import entry, replace_entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition, tile_pixels, write_tile

CONFIG = Path(__file__).resolve().parents[1] / 'config/riko_death_orbs_us.json'
STATIC_BANKS = (1, 2, 3, 4, 6)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def recolor_death_orbs(archive, *, lut_override=None):
    config = json.loads(CONFIG.read_text('utf8'))
    texture, parts = entry(archive, 0x10206), entry(archive, 3)
    selected = {(1, r['frame']) for r in config['frames']}
    comps = {(b, n): composition_frame(parts, b, n) for b in STATIC_BANKS
             for n in range(composition_frame(parts, b, 0)['bank_frame_count'])}
    for r in config['frames']:
        c = comps[1, r['frame']]
        pixels, size, bounds, _ = compose_static(texture, c)
        records = b''.join(parts[p['record_offset']:p['record_offset'] + 4] for p in c['parts'])
        if (sha(pixels) != r['pixels_sha256'] or list(size) != r['size'] or
                list(bounds) != r['bounds'] or sha(records) != r['part_bytes_sha256']):
            raise ValueError('Unsupported death orb source or already recolored')
    tiles = {p['page'] * 256 + p['tile'] for k in selected for p in comps[k]['parts']}
    if sorted(tiles) != config['tiles'] or sha(b''.join(tile_pixels(texture, t) for t in sorted(tiles))) != config['tile_bytes_sha256']:
        raise ValueError('Death orb source tile hash differs')
    protected = {p['page'] * 256 + p['tile'] for k, c in comps.items() if k not in selected for p in c['parts']}
    free = iter(sorted(set(range(len(texture) // 128)) - protected - tiles))
    changed, newparts, mapping = bytearray(texture), bytearray(parts), {}
    lut = bytes(config['lut'] if lut_override is None else lut_override)
    if len(lut)!=16 or lut[0]!=0 or any(not 1<=v<=15 for v in lut[1:]):raise ValueError('Death LUT must preserve transparency')
    for tile in sorted(tiles):
        target = next(free, None) if tile in protected else tile
        if target is None:
            raise ValueError('No unreferenced static atlas tile available')
        mapping[tile] = target
        write_tile(changed, target, bytes(lut[v] for v in tile_pixels(texture, tile)))
    offsets = set()
    for key in selected:
        for p in comps[key]['parts']:
            off = p['record_offset']; t = mapping[p['page'] * 256 + p['tile']]
            flags = (p['flags'] & ~15) | t // 256 | (config['part_clut_offset'] << 2)
            newparts[off:off + 2] = bytes((flags, t % 256)); offsets.update((off, off + 1))
    for key, c in comps.items():
        after = composition_frame(bytes(newparts), *key)
        before_frame = compose_static(texture, local_composition(c))[:3]
        after_frame = compose_static(bytes(changed), local_composition(after))[:3]
        expected = (bytes(lut[v] for v in before_frame[0]), *before_frame[1:]) if key in selected else before_frame
        if after_frame != expected:
            raise ValueError('Death orb remap changed shape or another static effect')
        if key not in selected and after != c:
            raise ValueError('Protected static composition changed')
    if any(a != b and i not in offsets for i, (a, b) in enumerate(zip(parts, newparts))):
        raise ValueError('Death orb write changed geometry or body parts')
    for tile in protected:
        if tile_pixels(texture, tile) != tile_pixels(changed, tile):
            raise ValueError('Another effect texture changed')
    result = replace_entry(replace_entry(archive, 0x10206, bytes(changed)), 3, bytes(newparts))
    return result, {'frames': sorted(selected), 'tile_mapping': mapping,
        'shared_tiles_copied': sorted(tiles & protected),
        'protected_static_frames': len(comps) - len(selected),
        'config_sha256': sha(CONFIG.read_bytes()), 'clut': '0x7803','effective_lut':list(lut),
        'palette_bytes_unchanged': True, 'geometry_timing_unchanged': True}
