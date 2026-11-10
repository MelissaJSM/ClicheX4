"""US static 4bpp atlas: 16 tiles per row, unchanged parts and CLUTs."""
import hashlib


def compose_static(texture, composition):
    parts = composition['parts']
    if not parts or len(texture) % 2048:
        raise ValueError('Invalid static atlas/composition')
    bounds = (min(p['x'] for p in parts), min(p['y'] for p in parts),
              max(p['x'] + 16 for p in parts), max(p['y'] + 16 for p in parts))
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    pixels = bytearray(width * height)
    sources = [[] for _ in pixels]
    for part in parts:
        if part['clut'] or part['unknown_flags']:
            raise ValueError('Unsupported static CLUT/flags')
        tile = part['page'] * 256 + part['tile']
        for y in range(16):
            for x in range(16):
                offset = (tile // 16 * 16 + y) * 128 + tile % 16 * 8 + x // 2
                if offset >= len(texture):
                    raise ValueError('Static tile outside atlas')
                shift = (x % 2) * 4
                px = part['x'] - bounds[0] + (15-x if part['flip_x'] else x)
                py = part['y'] - bounds[1] + (15-y if part['flip_y'] else y)
                dest = py * width + px
                value = texture[offset] >> shift & 15
                sources[dest].append((offset, shift))
                if value:
                    pixels[dest] = value
    return bytes(pixels), (width, height), bounds, sources


def patch_static(texture, compositions, frames):
    """Reject alias conflicts and unrepresented pixels before returning bytes."""
    result = bytearray(texture)
    demands = {}
    for n, (data, size) in frames.items():
        _, expected_size, _, sources = compose_static(texture, compositions[n])
        if size != expected_size or len(data) != size[0]*size[1] or any(v > 15 for v in data):
            raise ValueError('Invalid static frame pixels/size')
        for value, locations in zip(data, sources):
            if not locations:
                if value:
                    raise ValueError('Opaque static pixel outside parts')
                continue
            if len(locations) != 1:
                raise ValueError('Overlapping static parts require explicit handling')
            location = locations[0]
            if location in demands and demands[location] != value:
                raise ValueError('Conflicting shared static pixel')
            demands[location] = value
    for (offset, shift), value in demands.items():
        result[offset] = (result[offset] & ~(15 << shift)) | (value << shift)
    result = bytes(result)
    for n, expected in frames.items():
        if compose_static(result, compositions[n])[:2] != expected:
            raise ValueError('Static frame roundtrip mismatch')
    return result


def sha256(data):
    return hashlib.sha256(data).hexdigest()
