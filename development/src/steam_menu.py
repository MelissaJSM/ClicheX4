"""Native PC menu PAT records, including its three appended save slots."""
import struct

from .steam_arc import pat_from_ps1
from .steam_ui import pat_frames


def native_menu_frames(pat):
    # The PC exporter changed labels and appended slots 4..6 without updating
    # old PS1 offset fields. The count table, headers, and quads are complete.
    # Accept only that observed shape, not arbitrary inconsistent PAT records.
    if len(pat) < 16 or pat[:12] != b'PAT\0' + struct.pack('<II', 3, 1):
        raise ValueError('Expected single-bank native menu PAT3')
    n = struct.unpack_from('<I', pat, 12)[0]
    if n not in (118, 126) or len(pat) < 16 + 8*n:
        raise ValueError('Unrecognized native menu frame count')
    counts = struct.unpack_from('<'+'I'*n, pat, 16)
    pos = 16 + 8*n
    if pos + sum(counts)*4 != len(pat):
        raise ValueError('Native menu quad length mismatch')
    frames = []
    previous = -1
    for i, count in enumerate(counts):
        ct, location = struct.unpack_from('<HH', pat, 16+4*n+4*i)
        valid_offset = (location > previous if i < n-3 else location == 0)
        if i == 0:
            valid_offset = location == n-3
        if not 0 < count <= 128 or ct != count or not valid_offset:
            raise ValueError('Unrecognized native menu legacy header')
        frames.append(pat[pos:pos+count*4])
        pos += count*4
        previous = location
    return frames


def encode_frames(frames):
    if not frames or any(len(f)%4 or not f for f in frames):
        raise ValueError('Incomplete menu quad records')
    headers = bytearray()
    location = len(frames)
    for frame in frames:
        count = len(frame)//4
        if location + count > 65535:
            raise ValueError('Menu PAT address overflow')
        headers.extend(struct.pack('<HH', count, location))
        location += count
    result = pat_from_ps1(struct.pack('<I', 4)+headers+b''.join(frames))
    if pat_frames(result) != [frames]:
        raise ValueError('Menu PAT roundtrip mismatch')
    return result
