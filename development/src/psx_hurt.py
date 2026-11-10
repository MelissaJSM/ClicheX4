"""Zero bank0 135..138: a shared body, two spark overlays and a flash silhouette.

No changes to composition, animation events or additional CLUT rows.
"""
from src.psx_player import composition_frame, compose_indices, graphics_bank, decode_stream
from src.psx_frame_edit import edit_frame_indices, frame_coverage

HURT_FRAMES = frozenset(range(135, 139))


def edit_hurt_stream(packed, tiles, compositions, base, *, spark_index=15):
    """Keep the original spark positions; map original white index8 to Riko15."""
    if type(spark_index) is not int or not 1<=spark_index<16:raise ValueError('Spark color must be an opaque 4bpp index')
    if set(compositions) != {135, 136, 137}:
        raise ValueError('Hurt shared stream requires all three compositions')
    comp = compositions[135]
    if len(comp['parts']) != 10:
        raise ValueError('Unexpected hurt base layer')
    base_sources = {s for v in frame_coverage(packed, tiles, comp)[0] for s in v}
    overlay_sources = set()
    def geometry(parts):
        return [{k:v for k,v in p.items() if k != 'record_offset'} for p in parts]
    for n in (136, 137):
        parts = compositions[n]['parts']
        if geometry(parts[:10]) != geometry(comp['parts']) or len(parts) <= 10:
            raise ValueError('Hurt overlay does not share the verified base')
        overlay = {**compositions[n], 'parts': parts[10:]}
        overlay_sources.update(s for v in frame_coverage(packed, tiles, overlay)[0] for s in v)
    if base_sources & overlay_sources:
        raise ValueError('Hurt overlay aliases body source pixels')
    if any((packed[o] >> shift) & 15 not in (0, 8) for o, shift in overlay_sources):
        raise ValueError('Unrecognized hurt spark indices')
    result = bytearray(edit_frame_indices(packed, tiles, comp, *base))
    for o, shift in overlay_sources:
        if (packed[o] >> shift) & 15:
            result[o] = (result[o] & ~(15 << shift)) | (spark_index << shift)
    return bytes(result)


def flash_from_body(base, bounds, target_size, target_bounds, *, fill_index=12, outline_index=15):
    """One-pixel white contour and pale fill follow Riko, never Zero's old silhouette."""
    if any(type(v) is not int or not 1<=v<16 for v in (fill_index,outline_index)):raise ValueError('Flash colors must be opaque 4bpp indices')
    pixels, size = base
    body = {(i % size[0] + bounds[0], i // size[0] + bounds[1]): v
            for i, v in enumerate(pixels) if v}
    expanded = {(x+dx, y+dy) for x,y in body for dx in (-1,0,1) for dy in (-1,0,1)}
    result = bytearray(target_size[0]*target_size[1])
    for x,y in expanded:
        if not target_bounds[0] <= x < target_bounds[2] or not target_bounds[1] <= y < target_bounds[3]:
            raise ValueError('Hurt flash escaped native canvas')
        result[(y-target_bounds[1])*target_size[0]+x-target_bounds[0]] = outline_index if (x,y) not in body or body[x,y] == outline_index else fill_index
    return bytes(result), target_size


def derive_hurt_frames(gfx, parts, base, *, spark_index=15, fill_index=12, outline_index=15):
    bank = graphics_bank(gfx, 0)
    f = bank['frames'][135]
    if any(bank['frames'][n]['offset'] != f['offset'] for n in (136,137)):
        raise ValueError('Hurt stream sharing changed')
    raw = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128).data
    comps = {n: composition_frame(parts, 0, n) for n in (135,136,137)}
    edited = edit_hurt_stream(raw, f['tile_count'], comps, base, spark_index=spark_index)
    frames = {n: compose_indices(edited, f['tile_count'], c)[:2] for n,c in comps.items()}
    bounds = compose_indices(edited, f['tile_count'], comps[135])[2]
    flash = bank['frames'][138]
    original = decode_stream(gfx, flash['offset'], flash['limit'], flash['tile_count']*128).data
    _,size,target_bounds,_ = compose_indices(original, flash['tile_count'], composition_frame(parts,0,138))
    frames[138] = flash_from_body(base, bounds, size, target_bounds, fill_index=fill_index, outline_index=outline_index)
    return frames


def validate_hurt_frames(gfx, parts, frames):
    if not HURT_FRAMES <= frames.keys():
        raise ValueError('Hurt body, sparks and flash must be supplied together')
    expected = derive_hurt_frames(gfx, parts, frames[135])
    for n in HURT_FRAMES:
        if frames[n] != expected[n]:
            raise ValueError(f'Hurt frame {n} differs from the shared body and defined effect')
    return {'frames': sorted(HURT_FRAMES), 'base_frame':135,
            'spark_coordinates_preserved':True, 'spark_index_mapping':{'8':15},
            'flash_from_riko_silhouette':True, 'flash_fill_index':12,'flash_outline_index':15}
