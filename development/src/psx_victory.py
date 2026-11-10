"""US Zero victory and departure, retaining original pure warp texels."""
from src.psx_player import graphics_bank, decode_stream, composition_frame, compose_indices

SCOPE = 'wall_spin_ice_rise_burst_thrust_victory_bank1_v1'
BODY = frozenset(range(9))
KEYS = frozenset(range(7))
FLASH = frozenset((7, 8))
EFFECTS = frozenset(range(9, 14))
HEAD_VIEWS = {str(n): ('front' if n < 2 else 'front_mirrored') for n in KEYS}


def departure_flash(base, bounds, size, target_bounds, phase):
    pixels, (width, height) = base
    if phase not in FLASH or len(pixels) != width * height or any(v > 15 for v in pixels):
        raise ValueError('Invalid indexed departure body or phase')
    body = {(i % width + bounds[0], i // width + bounds[1]): v
            for i, v in enumerate(pixels) if v}
    if not body:
        raise ValueError('Empty departure body')
    image = {}
    radius = 1 if phase == 7 else 2
    for x, y in body:
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:
                    image[x + dx, y + dy] = 15 if phase == 7 else 12
    pale = (0, 12, 12, 12, 15, 15, 12, 15, 15, 15, 12, 12, 15, 12, 15, 15)
    image.update({xy: v if phase == 7 else pale[v] for xy, v in body.items()})
    out = bytearray(size[0] * size[1])
    for (x, y), v in image.items():
        if not target_bounds[0] <= x < target_bounds[2] or not target_bounds[1] <= y < target_bounds[3]:
            raise ValueError('Departure glow escaped original canvas')
        out[(y - target_bounds[1]) * size[0] + x - target_bounds[0]] = v
    return bytes(out), size


def derive_flashes(gfx, parts, base):
    bank = graphics_bank(gfx, 1)
    def native(n):
        f = bank['frames'][n]
        raw = decode_stream(gfx, f['offset'], f['limit'], f['tile_count'] * 128).data
        return compose_indices(raw, f['tile_count'], composition_frame(parts, 5, n))
    _, size, bounds, _ = native(3)
    if tuple(base[1]) != size:
        raise ValueError('Departure base dimensions changed')
    return {n: departure_flash(base, bounds, native(n)[1], native(n)[2], n) for n in FLASH}


def validate_victory(gfx, parts, frames):
    if not BODY <= frames.keys():
        raise ValueError('Victory needs all body and departure flash frames')
    for n, expected in derive_flashes(gfx, parts, frames[3]).items():
        if frames[n] != expected:
            raise ValueError('Departure flash differs from the new Riko body')
    return {'body_frames': sorted(BODY), 'flash_source': 3,
            'preserved_pure_effects': sorted(EFFECTS), 'original_zero_flash_body_reused': False}
