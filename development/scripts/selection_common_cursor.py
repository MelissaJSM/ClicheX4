"""선택 커서의 CLUT 오프셋만 공통 회색 행6으로 맞춘다."""
import hashlib
import struct

from scripts.prepare_riko_ui import entry, replace_entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition

TARGETS = {(1, n) for n in range(8, 14)}
ROW6_WORDS = (0x0000, 0x8421, 0x8C63, 0x94A5, 0x9CE7, 0xA529, 0xAD6B,
              0xB18C, 0xB9CE, 0xC210, 0xCA52, 0xD294, 0xDAD6, 0xE318,
              0xF39C, 0xFFDF)
PIXEL_HASHES = {
    8: 'a17046c0b033a32e7874076ad9e65af5421fc31b717bd005c1d853e22986afda',
    9: 'acd9ccd253f6a3e365eec5a68f7f95b7cc7e213cd49e9b3163a891b4bb96e9bb',
    10: '0f6045bc4a373e3248bc3388ad88e9e5c0d62f4d7dc13d57391c319c705a10f1',
    11: '36bedf18c5e453b1b449c5c32b05f0a7c8b5311595dc19c14daa58a2bf607a56',
    12: '48670ad3cf3c57308a8b9d81036c3f878d03331fc04f901eb325bcd12ba38bcd',
    13: '991c734cf2c3b656141b1c6c48ed7aebdd3a54d68b7a2871a9c170b273ce830a',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_palette(col_arc):
    """COL0E_U1 행6을 읽기만 하며 정확한 공통 색상표를 요구한다."""
    palette = entry(col_arc, 5)
    require(len(palette) == 4096, 'Unexpected selection palette size')
    row = palette[192:224]
    require(struct.unpack('<16H', row) == ROW6_WORDS, 'Selection row6 is not the common grayscale ramp')
    return {'palette_row': 6, 'base_row': 4, 'part_clut_offset': 2,
            'row_sha256': sha(row), 'palette_written': False,
            'words': [f'0x{v:04X}' for v in ROW6_WORDS],
            'rgb': [[(v & 31)*255//31, ((v >> 5) & 31)*255//31,
                     ((v >> 10) & 31)*255//31] for v in ROW6_WORDS]}


def patch(arc):
    """Return an equal-length ARC whose six cursor compositions all use row6.

    No palette is accepted for mutation. The caller must verify its COL with
    verify_palette(). No files, source BINs, active saves or emulator are touched.
    Portrait allocation may differ, but the accepted native cursor pixels must
    match exactly. Shared records outside the six cursors are refused.
    """
    require(len(arc) == 217088, 'Unexpected selection ARC size')
    texture, parts = entry(arc, 0x10102), entry(arc, 10)
    require(len(texture) == 116736 and len(parts) == 5368,
            'Unexpected selection texture/parts size')
    require(entry(arc, 12) == struct.pack('<3I', 0, 40960, 90112),
            'Unexpected selection texture bank directory')
    require(struct.unpack_from('<I', parts)[0] == 12, 'Expected three selection banks')
    bank_texture = texture[40960:90112]
    compositions, owners = {}, {}
    for bank in range(3):
        count = composition_frame(parts, bank, 0)['bank_frame_count']
        for n in range(count):
            key = bank, n
            comp = composition_frame(parts, bank, n)
            compositions[key] = comp
            for p in comp['parts']:
                owners.setdefault(p['record_offset'], set()).add(key)
    require(TARGETS <= compositions.keys(), 'Missing selection cursor frames')
    changes, records, details = {}, set(), []
    for key in sorted(TARGETS):
        n = key[1]
        comp = compositions[key]
        require(len(comp['parts']) == 54, 'Unexpected cursor part count')
        pixels, size, bounds, _ = compose_static(bank_texture, local_composition(comp))
        expected_bounds = (-109, -90, 103, 90) if n < 11 else (-105, -90, 107, 90)
        require(size == (212, 180) and bounds == expected_bounds,
                'Unexpected cursor dimensions or origin')
        require(sha(pixels) == PIXEL_HASHES[n], 'Accepted cursor pixels differ')
        original_clut = (n - 8) % 3
        require(all(p['clut'] in {original_clut, 2} for p in comp['parts']),
                'Unexpected cursor palette binding')
        for p in comp['parts']:
            off = p['record_offset']
            require(owners[off] <= TARGETS, 'Cursor record is shared outside target frames')
            records.add(off)
            value = (parts[off] & ~0x0C) | 0x08
            if value != parts[off]:
                changes[off] = value
        details.append({'frame': n, 'parts': 54, 'bounds': list(bounds),
                        'index_sha256': sha(pixels), 'opaque_pixels': sum(v != 0 for v in pixels),
                        'source_clut_offsets': sorted({p['clut'] for p in comp['parts']}),
                        'target_clut_offset': 2, 'target_palette_row': 6})
    updated = bytearray(parts)
    for off, value in changes.items():
        updated[off] = value
    updated = bytes(updated)
    require({i for i, (a, b) in enumerate(zip(parts, updated)) if a != b} == set(changes),
            'Unexpected parts bytes changed')
    for key, old in compositions.items():
        new = composition_frame(updated, *key)
        require(old['bank_frame_count'] == new['bank_frame_count'] and
                len(old['parts']) == len(new['parts']), 'Frame/part count changed')
        for a, b in zip(old['parts'], new['parts']):
            expected = dict(a)
            if key in TARGETS:
                expected['flags'] = (expected['flags'] & ~0x0C) | 0x08
                expected['clut'] = 2
            require(expected == b, 'Geometry, draw order or non-target metadata changed')
        if key in TARGETS:
            before = compose_static(bank_texture, local_composition(old))[:3]
            after = compose_static(bank_texture, local_composition(new))[:3]
            require(before == after, 'Cursor pixels/geometry changed')
    result = replace_entry(arc, 10, updated)
    require(len(result) == len(arc) and replace_entry(result, 10, parts) == arc,
            'Non-parts archive bytes changed')
    require(entry(result, 0x10102) == texture, 'Selection texture changed')
    return result, {
        'kind': 'selection_cursor_common_row6',
        'before_sha256': sha(arc), 'after_sha256': sha(result),
        'frames': details, 'unique_target_records': len(records),
        'changed_flag_bytes': len(changes), 'changed_part_offsets': sorted(changes),
        'frame_count_geometry_draw_order_flips_timing_preserved': True,
        'all_cursor_index_pixels_preserved': True,
        'non_target_aliases': 0, 'other_frame_metadata_exact': True,
        'texture_and_non_parts_entries_exact': True, 'palette_written': False,
        'added_parts_or_bytes': 0, 'runtime_verified': False,
    }
