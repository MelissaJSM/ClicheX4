"""단일 새 몸체를 페이지 첫열 패딩과 함께 패킹하고 나머지 타일은 보존한다."""
import numpy as np
from scripts.prepare_shibuki_ultimate_production import fast_fit
from src.psx_player import indexed_atlas

def pack_single_safe(raw, count, image, pool, limit):
    rects = fast_fit(image > 0, limit)
    if rects is None:
        raise ValueError('Single layer composition capacity')
    patterns = []
    records = []
    remaining = image.copy()
    for left, top in rects:
        patch = remaining[top:top+16, left:left+16].copy()
        remaining[top:top+16, left:left+16] = 0
        ys, xs = np.nonzero(patch)
        if not len(xs):
            continue
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)
        compact = patch[y0:y1, x0:x1]
        key = (compact.shape, compact.tobytes())
        if key not in patterns:
            patterns.append(key)
        records.append((patterns.index(key), left+x0, top+y0))
    if remaining.any() or len(patterns) > len(pool):
        raise ValueError(f'Single layer needs {len(patterns)} patterns, pool {len(pool)}')
    chosen, used = {}, set()
    ids = sorted(pool, key=lambda t: (t % 16 == 0, t))
    for key, (shape, data) in sorted(enumerate(patterns), key=lambda v: v[1][0][1], reverse=True):
        tile = next((t for t in ids if t not in used and (t % 16 != 0 or shape[1] < 16)), None)
        if tile is None:
            raise ValueError('No page-edge-safe tile allocation')
        used.add(tile)
        chosen[key] = (tile, 1 if tile % 16 == 0 else 0)
    _, locations, _ = indexed_atlas(raw, count)
    out = bytearray(raw)
    for tile in pool:
        for y in range(16):
            for x in range(16):
                pos, shift = locations[(tile//16*16+y)*256+tile%16*16+x]
                out[pos] &= ~(15 << shift)
    for key, (shape, data) in enumerate(patterns):
        tile, pad = chosen[key]
        raster = np.frombuffer(data, np.uint8).reshape(shape)
        for y, x in np.argwhere(raster):
            pos, shift = locations[(tile//16*16+int(y))*256+tile%16*16+int(x)+pad]
            out[pos] |= int(raster[y, x]) << shift
    assignments = [(chosen[k][0], x-chosen[k][1], y, 0) for k, x, y in records]
    return bytes(out), [assignments]
