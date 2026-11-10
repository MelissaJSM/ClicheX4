"""Translate whole sprite compositions without touching pixels or object physics."""
import struct
from src.psx_player import bank_offsets, composition_frame, u32


def translate_compositions(parts, shifts):
    if not shifts or any(not isinstance(key, tuple) or len(key) != 2
                         or any(type(v) is not int for v in (*key, *delta))
                         or len(delta) != 2 for key, delta in shifts.items()):
        raise ValueError('Explicit integer bank/frame and x/y shift required')
    all_frames = {}
    owners = {}
    for bank, base in enumerate(bank_offsets(parts)):
        for frame in range(u32(parts, base) >> 16):
            comp = composition_frame(parts, bank, frame)
            all_frames[bank, frame] = comp
            for part in comp['parts']:
                owners.setdefault(part['record_offset'], set()).add((bank, frame))
    if not shifts.keys() <= all_frames.keys():
        raise ValueError('Selected composition does not exist')
    writes = {}
    for key, (dx, dy) in shifts.items():
        for part in all_frames[key]['parts']:
            offset = part['record_offset']
            if any(shifts.get(owner, (0, 0)) != (dx, dy) for owner in owners[offset]):
                raise ValueError('Translation conflicts with a shared composition')
            x, y = part['x'] + dx, part['y'] + dy
            if not -128 <= x <= 127 or not -128 <= y <= 127:
                raise ValueError('Translated coordinate exceeds signed byte range')
            writes[offset + 2] = x & 255
            writes[offset + 3] = y & 255
    result = bytearray(parts)
    for pos, value in writes.items():
        result[pos] = value
    changed = [i for i, (a, b) in enumerate(zip(parts, result)) if a != b]
    return bytes(result), {'shifts': [{'bank': k[0], 'frame': k[1], 'dx': v[0], 'dy': v[1]}
                                    for k, v in sorted(shifts.items())],
                           'changed_offsets': changed, 'changed_bytes': len(changed),
                           'pixels_changed': False, 'object_coordinates_changed': False,
                           'animation_timing_changed': False}
