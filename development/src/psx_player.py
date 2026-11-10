"""PS1 플레이어 16-bit 압축 스트림과 조립 레코드의 제한된 읽기/보존 쓰기.

포맷 근거는 docs/SPRITE_SPEC.md. 게임별 주소나 팔레트는 이 모듈에 넣지 않는다.
"""
from dataclasses import dataclass
import struct


def u32(data, offset):
    if offset < 0 or offset+4 > len(data):
        raise ValueError('32-bit read out of bounds')
    return struct.unpack_from('<I', data, offset)[0]


@dataclass
class Stream:
    data: bytes
    groups: list
    owners: list
    start: int
    end: int

    def serialize(self):
        words = []
        for control, tokens in self.groups:
            words.append(control)
            for token in tokens:
                words.extend(token)
        return struct.pack('<'+'H'*len(words), *words)


def decode_stream(source, start, limit, expected_bytes):
    if start < 0 or start % 2 or not start < limit <= len(source):
        raise ValueError('Invalid compressed range')
    if expected_bytes <= 0 or expected_bytes % 2 or expected_bytes > 0x8000:
        raise ValueError('Invalid decompressed size')
    cursor = start
    values, owners, groups = [], [], []

    def take():
        nonlocal cursor
        if cursor+2 > limit:
            raise ValueError('Truncated compressed stream')
        value = struct.unpack_from('<H', source, cursor)[0]
        cursor += 2
        return value

    while True:
        control = take()
        tokens = []
        groups.append((control, tokens))
        for bit in range(15, -1, -1):
            location = cursor
            code = take()
            token = [code]
            tokens.append(token)
            if not control & (1 << bit):
                values.append(code)
                owners.append(location)
            else:
                distance = code & 0x7ff
                count = code >> 11
                if count == 0:
                    count = take()
                    token.append(count)
                if count == distance == 0:
                    if len(values)*2 != expected_bytes:
                        raise ValueError('Decompressed size mismatch')
                    return Stream(struct.pack('<'+'H'*len(values), *values), groups, owners, start, cursor)
                if count == 0 or distance > len(values):
                    raise ValueError('Invalid back-reference')
                if (len(values)+count)*2 > expected_bytes:
                    raise ValueError('Decompression exceeds size budget')
                for _ in range(count):
                    values.append(values[-distance] if distance else 0)
                    owners.append(owners[-distance] if distance else None)
            if len(values)*2 > expected_bytes:
                raise ValueError('Decompression exceeds size budget')


def bank_offsets(data, *, allow_aliases=False):
    first = u32(data, 0)
    if first < 4 or first % 4 or first > len(data):
        raise ValueError('Invalid bank directory')
    offsets = [u32(data, i) for i in range(0, first, 4)]
    expected = sorted(offsets) if allow_aliases else sorted(set(offsets))
    if offsets != expected or any(x < first or x >= len(data) or x % 4 for x in offsets):
        raise ValueError('Invalid bank offsets')
    return offsets


def graphics_bank(data, bank, *, allow_bank_aliases=False):
    offsets = bank_offsets(data, allow_aliases=allow_bank_aliases)
    if not 0 <= bank < len(offsets):
        raise ValueError('Invalid bank index')
    base = offsets[bank]
    # Some X bank IDs share the same physical bank. Their boundary is the
    # next distinct offset, never the alias immediately following this ID.
    end = next((offset for offset in offsets[bank+1:] if offset > base), len(data))
    table_size = u32(data, base) & 0xfffff
    if table_size < 4 or table_size % 4 or base+table_size > end:
        raise ValueError('Invalid graphics table')
    frames = []
    for index in range(table_size//4):
        packed = u32(data, base+index*4)
        offset, tiles = packed & 0xfffff, packed >> 20
        if offset < table_size or base+offset >= end or offset % 2 or not 0 < tiles <= 256:
            raise ValueError('Invalid graphics frame')
        frames.append({'index': index, 'offset': base+offset, 'tile_count': tiles})
    starts = sorted({f['offset'] for f in frames})
    limits = dict(zip(starts, starts[1:]+[end]))
    for f in frames:
        f['limit'] = limits[f['offset']]
    return {'base': base, 'end': end, 'frames': frames}


def composition_frame(data, bank, frame):
    offsets = bank_offsets(data)
    if not 0 <= bank < len(offsets):
        raise ValueError('Invalid composition bank')
    base = offsets[bank]
    end = offsets[bank+1] if bank+1 < len(offsets) else len(data)
    count_frames = (u32(data, base) >> 16)
    if not 0 <= frame < count_frames or base+count_frames*4 > end:
        raise ValueError('Invalid composition frame')
    header = u32(data, base+frame*4)
    count, start = header & 0xffff, base+(header >> 16)*4
    if count > 256 or start < base+count_frames*4 or start+count*4 > end:
        raise ValueError('Invalid composition range')
    parts = []
    for i in range(count):
        flags, tile, x, y = struct.unpack_from('<BBbb', data, start+i*4)
        parts.append({'index': i, 'record_offset': start+i*4, 'flags': flags,
                      'page': flags & 3, 'clut': (flags >> 2) & 3,
                      'unknown_flags': flags & 0x30, 'tile': tile, 'x': x, 'y': y,
                      'flip_x': bool(flags & 0x40), 'flip_y': bool(flags & 0x80)})
    return {'bank': bank, 'frame': frame, 'bank_frame_count': count_frames, 'parts': parts}


def indexed_atlas(packed, tiles):
    """VRAM에 행 단위로 업로드하는 구조를 256px 너비로 복원한다."""
    if len(packed) != tiles*128 or not 0 < tiles <= 256:
        raise ValueError('Invalid packed pixel length')
    height = ((tiles+15)//16)*16
    pixels = bytearray(256*height)
    locations = [None]*(256*height)
    cursor = 0
    for first in range(0, tiles, 16):
        width = min(16, tiles-first)*16
        for row in range(16):
            for x in range(0, width, 2):
                dest = (first//16*16+row)*256+x
                value = packed[cursor]
                pixels[dest:dest+2] = bytes((value & 15, value >> 4))
                locations[dest:dest+2] = [(cursor, 0), (cursor, 4)]
                cursor += 1
    return bytes(pixels), locations, height


def compose_indices(packed, tiles, composition, *, allowed_cluts=None):
    atlas, mapping, height = indexed_atlas(packed, tiles)
    parts = composition['parts']
    if not parts:
        raise ValueError('Empty composition')
    bounds = (min(p['x'] for p in parts), min(p['y'] for p in parts),
              max(p['x']+16 for p in parts), max(p['y']+16 for p in parts))
    width, out_height = bounds[2]-bounds[0], bounds[3]-bounds[1]
    result = bytearray(width*out_height)
    provenance = [None]*len(result)
    for part in parts:
        if (part['page'] or part['unknown_flags'] or
                part['clut'] not in ({0} if allowed_cluts is None else allowed_cluts)):
            raise ValueError('Preview supports only verified page/CLUT 0 parts')
        tx, ty = (part['tile'] & 15)*16, (part['tile'] >> 4)*16
        if ty+16 > height:
            raise ValueError('Tile outside decompressed atlas')
        for y in range(16):
            for x in range(16):
                src = (ty+y)*256+tx+x
                if mapping[src] is None:
                    raise ValueError('Tile references unloaded atlas area')
                px = part['x']-bounds[0]+(15-x if part['flip_x'] else x)
                py = part['y']-bounds[1]+(15-y if part['flip_y'] else y)
                if atlas[src]:
                    dest = py*width+px
                    result[dest] = atlas[src] + (part['clut']*16 if allowed_cluts is not None else 0)
                    provenance[dest] = {'part': part['index'], 'byte': mapping[src][0], 'shift': mapping[src][1]}
    return bytes(result), (width, out_height), bounds, provenance
