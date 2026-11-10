"""Fixed-size UI atlases. Reassign tiles without changing part geometry/timing."""
import struct
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static


def aliased_composition(data, bank, frame):
    """Stage directories can assign two resource IDs to the same parts bank."""
    first=struct.unpack_from('<I',data)[0]
    if first<4 or first%4 or first>=len(data):raise ValueError('Invalid stage parts directory')
    offsets=struct.unpack_from('<'+'I'*(first//4),data)
    if not 0<=bank<len(offsets) or list(offsets)!=sorted(offsets) or any(x<first or x%4 or x>=len(data) for x in offsets):
        raise ValueError('Invalid stage parts bank')
    start=offsets[bank];end=min((x for x in offsets if x>start),default=len(data))
    result=composition_frame(struct.pack('<I',4)+data[start:end],0,frame)
    result['bank']=bank
    for p in result['parts']:p['record_offset']+=start-4
    return result


def local_composition(comp):
    if any(p['unknown_flags'] for p in comp['parts']):
        raise ValueError('Unsupported UI flags')
    return {**comp, 'parts': [{**p, 'clut': 0} for p in comp['parts']]}


def tile_pixels(texture, tile):
    out = bytearray()
    for y in range(16):
        start = (tile // 16 * 16 + y) * 128 + tile % 16 * 8
        row = texture[start:start+8]
        if len(row) != 8:
            raise ValueError('UI tile outside atlas')
        out.extend(v for b in row for v in (b & 15, b >> 4))
    return bytes(out)


def write_tile(texture, tile, pixels):
    if len(pixels) != 256 or any(v > 15 for v in pixels):
        raise ValueError('Invalid 4bpp UI tile')
    for y in range(16):
        start = (tile // 16 * 16 + y) * 128 + tile % 16 * 8
        texture[start:start+8] = bytes(pixels[y*16+x] | pixels[y*16+x+1] << 4 for x in range(0,16,2))


def place_frame(frame, target, texture):
    """Register an existing native-size sprite in the destination's world space."""
    data, size, bounds = frame
    _, ts, tb, coverage = compose_static(texture, local_composition(target))
    out = bytearray(ts[0]*ts[1])
    for i, value in enumerate(data):
        if not value:
            continue
        x = i % size[0] + bounds[0] - tb[0]
        y = i // size[0] + bounds[1] - tb[1]
        if not 0 <= x < ts[0] or not 0 <= y < ts[1] or not coverage[y*ts[0]+x]:
            raise ValueError(f"UI frame {target['frame']} clips an opaque pixel at {(x,y)}")
        out[y*ts[0]+x] = value & 15
    return bytes(out), ts


def repack_frames(texture, parts, bank, targets, clut_overrides=None, reserved_tiles=(), guard_uv_zero=False):
    """Keep every untouched frame/tile; fit replacements in remaining atlas slots.

    All headers, x/y, part order and flips stay fixed. Duplicate part records
    must agree. Transparent overlaps are resolved to one owning part.
    """
    if len(texture) % 2048:
        raise ValueError('UI atlas must contain whole rows')
    overrides = clut_overrides or {}
    count = composition_frame(parts, bank, 0)['bank_frame_count']
    if not targets or not set(targets) <= set(range(count)):
        raise ValueError('Invalid UI replacement frame IDs')
    comps = {n: composition_frame(parts, bank, n) for n in range(count)}
    reserved = {p['page']*256+p['tile'] for n,c in comps.items() if n not in targets for p in c['parts']}
    capacity = len(texture)//128
    if any(type(t) is not int or not 0 <= t < capacity for t in reserved_tiles):
        raise ValueError('Invalid external reserved UI tile')
    reserved.update(reserved_tiles)
    if any(t >= capacity for t in reserved):
        raise ValueError('Protected UI tile outside atlas')
    def safe_edge(pixels, tile):
        return not guard_uv_zero or ((tile % 16 != 0 or not any(pixels[::16]))
                                    and (tile % 256 >= 16 or not any(pixels[:16])))
    free = [t for t in range(capacity) if t not in reserved]
    allocated = {tile_pixels(texture,t):t for t in sorted(reserved)
                 if safe_edge(tile_pixels(texture,t),t)}
    changed_texture, changed_parts = bytearray(texture), bytearray(parts)
    record_demands = {}
    for n, (data,size) in sorted(targets.items()):
        c = local_composition(comps[n])
        _, expected, bounds, sources = compose_static(texture,c)
        if size != expected or len(data) != size[0]*size[1] or any(v>15 for v in data):
            raise ValueError('Invalid UI frame data')
        if any(v and not loc for v,loc in zip(data,sources)):
            raise ValueError('Opaque UI pixels outside parts')
        # Later nonempty parts own overlaps. The earlier parts stay transparent.
        owners = [-1]*len(data)
        for j,p in enumerate(c['parts']):
            for y in range(16):
                for x in range(16):
                    owners[(p['y']-bounds[1]+y)*size[0]+p['x']-bounds[0]+x] = j
        for j,p in enumerate(c['parts']):
            px = bytearray(256)
            for y in range(16):
                for x in range(16):
                    dx = p['x']-bounds[0]+(15-x if p['flip_x'] else x)
                    dy = p['y']-bounds[1]+(15-y if p['flip_y'] else y)
                    i=dy*size[0]+dx
                    px[y*16+x] = data[i] if owners[i]==j else 0
            pixels=bytes(px)
            if pixels not in allocated:
                slot=next((t for t in free if safe_edge(pixels,t)),None)
                if slot is None:
                    raise ValueError('UI atlas capacity exceeded; no expansion performed')
                free.remove(slot)
                allocated[pixels]=slot
                write_tile(changed_texture,slot,pixels)
            tile=allocated[pixels]
            flags=(p['flags'] & ~3) | (tile//256)
            if n in overrides:
                if not 0 <= overrides[n] <= 3:
                    raise ValueError('Invalid UI CLUT override')
                flags=(flags & ~12) | (overrides[n]<<2)
            value=bytes((flags,tile%256))
            offset=p['record_offset']
            if offset in record_demands and record_demands[offset]!=value:
                raise ValueError('Conflicting UI part alias')
            record_demands[offset]=value
            changed_parts[offset:offset+2]=value
    result=bytes(changed_texture),bytes(changed_parts)
    for n,c in comps.items():
        after=compose_static(result[0],local_composition(composition_frame(result[1],bank,n)))[:2]
        expected=targets.get(n,compose_static(texture,local_composition(c))[:2])
        if after!=expected:
            raise ValueError('UI atlas roundtrip/protected-frame mismatch')
    for t in reserved:
        if tile_pixels(result[0],t)!=tile_pixels(texture,t):
            raise ValueError('Protected UI tile changed')
    return *result, {'frames':sorted(targets),'capacity_tiles':capacity,
        'protected_tiles':len(reserved),'allocated_patterns':len(allocated),
        'part_coordinate_bytes_preserved':True,'untouched_frames_preserved':True,
        'uv_zero_edges_guarded':guard_uv_zero}
