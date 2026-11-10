"""US Zero warp texels and stage-local afterimage palette data only."""
from hashlib import sha256
import struct

from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices
from src.psx_frame_edit import frame_coverage
from src.psx_compress import replace_stream

WARP_FRAMES = {0: tuple(range(53, 61)), 1: tuple(range(9, 14))}
PARTS_BANKS = {0: 0, 1: 5}
# Original red/pink/white/gold -> approved Riko cyan/mint/white.
WARP_LUT = bytes((0, 1, 2, 3, 10, 6, 2, 2, 15, 12, 7, 1, 14, 10, 6, 14))
OLD_TRAIL = b''.join(struct.pack('<16H', 0, *([word] * 15))
                     for word in (0x8032, 0x800e, 0x8009))


def trail_palette(palette, *, reference_index=10):
    if len(palette) != 32:
        raise ValueError('Expected a single 16-color palette')
    if not 1<=reference_index<=15:raise ValueError('Invalid trail reference index')
    word = struct.unpack_from('<H', palette, reference_index*2)[0]
    rgb = (word & 31, word >> 5 & 31, word >> 10 & 31)
    if not max(rgb):
        raise ValueError('Empty mint reference')
    colors = [0x8000 | sum((c * peak // max(rgb)) << (5 * i)
                          for i, c in enumerate(rgb)) for peak in (18, 14, 9)]
    return b''.join(struct.pack('<16H', 0, *([color] * 15)) for color in colors)


def recolor_stage(archive, expected_sha, palette, *, reference_index=10):
    from scripts.discover_inputs import psx_arc
    if sha256(archive).hexdigest() != expected_sha:
        raise ValueError('Stage palette source hash mismatch')
    entries = psx_arc(archive)
    if len(entries) != 1 or entries[0]['type'] != '0x5' or entries[0]['size'] != 4096:
        raise ValueError('Unexpected stage palette structure')
    offset = entries[0]['offset'] + 13 * 32
    if archive[offset:offset + 96] != OLD_TRAIL:
        raise ValueError('Stage does not contain the verified Zero afterimage palette')
    return archive[:offset] + trail_palette(palette,reference_index=reference_index) + archive[offset + 96:]


def remap_warp(graphics, parts, *, lut=WARP_LUT):
    """Remap every source texel, including hidden overlaps, only in pure beams.

    Shared departure streams also contain accepted body flashes. Their complete
    source coverage is protected, not just the visible flattened preview.
    """
    if len(bank_offsets(graphics)) != 2:
        raise ValueError('Unsupported player bank layout')
    if len(lut)!=16 or lut[0]!=0 or any(not 1<=v<=15 for v in lut[1:]):raise ValueError('Warp LUT must preserve transparency')
    groups = {}
    for bi in range(2):
        for f in graphics_bank(graphics, bi)['frames']:
            groups.setdefault(f['offset'], []).append((bi, f))
    result = graphics
    reports = []
    for offset, refs in groups.items():
        targets = [(bi, f) for bi, f in refs if f['index'] in WARP_FRAMES[bi]]
        if not targets:
            continue
        f = refs[0][1]
        if len({(r['tile_count'], r['limit']) for _, r in refs}) != 1:
            raise ValueError('Inconsistent shared warp stream')
        raw = decode_stream(graphics, offset, f['limit'], f['tile_count'] * 128).data
        changed = bytearray(raw)
        selected, protected = set(), set()
        for bi, r in refs:
            comp = composition_frame(parts, PARTS_BANKS[bi], r['index'])
            coverage, _, _ = frame_coverage(raw, f['tile_count'], comp)
            sources = {s for cell in coverage for s in cell}
            (selected if r['index'] in WARP_FRAMES[bi] else protected).update(sources)
        for pos, shift in selected:
            old = raw[pos] >> shift & 15
            new = lut[old]
            if (pos, shift) in protected and new != old:
                raise ValueError('Warp remap conflicts with a protected body texel')
            changed[pos] = (changed[pos] & ~(15 << shift)) | (new << shift)
        for bi, r in refs:
            comp = composition_frame(parts, PARTS_BANKS[bi], r['index'])
            before = compose_indices(raw, f['tile_count'], comp)
            after = compose_indices(bytes(changed), f['tile_count'], comp)
            expected = bytes(lut[v] for v in before[0]) if r['index'] in WARP_FRAMES[bi] else before[0]
            if after[0] != expected or after[1:] != before[1:]:
                raise ValueError('Warp shape or protected body changed')
        if bytes(changed) == raw:
            raise ValueError('Warp already recolored or unsupported source')
        result, report = replace_stream(result, f, bytes(changed))
        reports.append({**report, 'references': [[bi, r['index']] for bi, r in refs],
                        'recolored': [[bi, r['index']] for bi, r in targets],
                        'protected_source_texels': len(protected),
                        'decoded_sha256': sha256(changed).hexdigest()})
    if sum(len(r['recolored']) for r in reports) != 13:
        raise ValueError('Incomplete warp selection')
    # Every other compressed stream, pointer, unused byte, and header survives.
    allowed = [(r['start'], r['start'] + r['encoded_bytes']) for r in reports]
    if len(result) != len(graphics) or any(a != b and not any(lo <= i < hi for lo, hi in allowed)
            for i, (a, b) in enumerate(zip(graphics, result))):
        raise ValueError('Warp write escaped allowed stream bytes')
    return result, reports


def apply_warp(archive, *, lut=WARP_LUT):
    from scripts.discover_inputs import psx_arc
    entries = psx_arc(archive)
    gm = next(e for e in entries if e['type'] == '0x2')
    pm = next(e for e in entries if e['type'] == '0x3')
    lo, hi = gm['offset'], gm['offset'] + gm['size']
    graphics, reports = remap_warp(archive[lo:hi], archive[pm['offset']:pm['offset'] + pm['size']],lut=lut)
    return archive[:lo] + graphics + archive[hi:], reports
