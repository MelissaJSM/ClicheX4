"""Replace the US Zero HP emblem, retaining shared effects and HUD geometry."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from scripts.prepare_riko_ui import entry, replace_entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition, tile_pixels, write_tile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/riko_hud_mark_us.json'
STATIC_BANKS = (1, 2, 3, 4, 6)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_hud_mark(archive):
    config = json.loads(CONFIG.read_text('utf8'))
    reference = ROOT / config['reference']
    if sha(reference.read_bytes()) != config['reference_sha256']:
        raise ValueError('HUD reference hash differs')
    texture, parts = entry(archive, 0x10206), entry(archive, 3)
    comps = {(b, n): composition_frame(parts, b, n) for b in STATIC_BANKS
             for n in range(composition_frame(parts, b, 0)['bank_frame_count'])}
    selected = {(1, n) for n in range(69, 78)}
    tiles = set(config['tiles'])
    if sha(b''.join(tile_pixels(texture, t) for t in sorted(tiles))) != config['source_tiles_sha256']:
        raise ValueError('Unsupported HUD source or already replaced')
    for n, expected in config['frames'].items():
        c = comps[1, int(n)]
        records = b''.join(parts[p['record_offset']:p['record_offset']+4] for p in c['parts'])
        if sha(records) != expected:
            raise ValueError('HUD composition differs')
    original, size, bounds, sources = compose_static(texture, local_composition(comps[1, 69]))
    if size != (48, 64) or bounds != (-24, -17, 24, 47):
        raise ValueError('Unsupported HUD frame bounds')
    desired = bytearray(original)
    for y, x1, x2 in config['background_rows']:
        desired[y*48+x1:y*48+x2+1] = bytes([14])*(x2-x1+1)
    # Integrate the supplied alpha silhouette into the native indexed badge.
    # Silver coverage levels retain thin wings without adding a new palette.
    with Image.open(reference) as image:
        alpha = image.convert('RGBA').getchannel('A').resize((10, 13), Image.Resampling.BOX).tobytes()
    for i, value in enumerate(alpha):
        if value >= 30:
            desired[(43+i//10)*48+10+i%10] = 10 if value >= 90 else 11 if value >= 55 else 12
    if sha(desired) != config['target_frame_sha256']:
        raise ValueError('HUD reference conversion differs')
    edited = bytearray(texture)
    for old, new, locations in zip(original, desired, sources):
        if old == new:
            continue
        if len(locations) != 1:
            raise ValueError('HUD pixel has ambiguous ownership')
        off, shift = locations[0]
        tile = (off//128//16)*16 + (off%128)//8
        if tile not in tiles:
            raise ValueError('HUD edit escaped emblem tiles')
        edited[off] = (edited[off] & ~(15 << shift)) | (new << shift)
    used = {p['page']*256+p['tile'] for c in comps.values() for p in c['parts']}
    protected = {p['page']*256+p['tile'] for k, c in comps.items() if k not in selected for p in c['parts']}
    free = iter(sorted(set(range(len(texture)//128))-used))
    output, newparts, mapping = bytearray(texture), bytearray(parts), {}
    for tile in sorted(tiles):
        target = next(free, None) if tile in protected else tile
        if target is None:
            raise ValueError('No unused HUD tile slots')
        mapping[tile] = target
        write_tile(output, target, tile_pixels(edited, tile))
    allowed_parts = set()
    for key in selected:
        for p in comps[key]['parts']:
            tile = p['page']*256+p['tile']
            if tile not in mapping:
                continue
            target, off = mapping[tile], p['record_offset']
            newparts[off:off+2] = bytes(((p['flags'] & ~3) | target//256, target%256))
            allowed_parts.update((off, off+1))
    for key, c in comps.items():
        nc = composition_frame(bytes(newparts), *key)
        actual = compose_static(bytes(output), local_composition(nc))[:3]
        expected = compose_static(bytes(edited) if key in selected else texture, local_composition(c))[:3]
        if actual != expected or (key not in selected and nc != c):
            raise ValueError('HUD replacement changed a protected frame')
    if any(a != b and i not in allowed_parts for i, (a, b) in enumerate(zip(parts, newparts))):
        raise ValueError('HUD replacement changed geometry or body parts')
    result = replace_entry(replace_entry(archive, 0x10206, bytes(output)), 3, bytes(newparts))
    return result, {'config_sha256': sha(CONFIG.read_bytes()), 'reference_sha256': config['reference_sha256'],
        'frames': sorted(selected), 'tile_mapping': mapping, 'protected_static_frames': len(comps)-len(selected),
        'palette_bytes_unchanged': True, 'geometry_timing_unchanged': True,
        'changed_pixel_count_frame69': sum(a != b for a,b in zip(original, desired))}
