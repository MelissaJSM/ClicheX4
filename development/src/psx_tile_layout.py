"""기존 16x16 타일 수 안에서 픽셀 소유권을 분리하여 다시 배치한다."""
from src.psx_player import indexed_atlas


def fill_redundant_pixels(packed,tile_count,assignments,targets,changes,writable):
    """중첩 파츠 사이 픽셀 소유권을 옮기되 모든 사용 자세의 조립 결과를 보존한다."""
    atlas,positions,_=indexed_atlas(packed,tile_count);result=bytearray(packed);seen=set()
    if set(assignments)!=set(targets):raise ValueError('Overlap target set differs')
    for tile,x,y,value in changes:
        if any(type(v) is not int for v in (tile,x,y,value)) or tile not in writable or not 0<=tile<tile_count or not 0<=x<16 or not 0<=y<16 or not 0<=value<16:
            raise ValueError('Invalid overlap pixel')
        key=(tile,x,y)
        if key in seen:raise ValueError('Duplicate overlap pixel')
        seen.add(key);idx=(tile//16*16+y)*256+tile%16*16+x
        uses=0
        for n,records in assignments.items():
            for t,left,top,flag in records:
                if t!=tile:continue
                uses+=1;px=left+(15-x if flag&64 else x);py=top+(15-y if flag&128 else y)
                target=targets[n]
                if not 0<=px<target.shape[1] or not 0<=py<target.shape[0] or (value and int(target[py,px])!=value):
                    raise ValueError('Overlap would change a visible variant')
                if value and tile%16==0 and (x==0 or flag&64):raise ValueError('Overlap at GPU U boundary')
                if value and flag&128 and (tile//16)%16==0 and y==0:raise ValueError('Overlap at GPU V boundary')
        if not uses:raise ValueError('Unreferenced overlap tile')
        off,shift=positions[idx];result[off]=(result[off]&~(15<<shift))|(value<<shift)
    rendered,_,_=indexed_atlas(result,tile_count)
    for n,records in assignments.items():
        target=targets[n];height,width=target.shape;canvas=bytearray(height*width)
        for tile,left,top,flag in records:
            for y in range(16):
                for x in range(16):
                    value=rendered[(tile//16*16+y)*256+tile%16*16+x]
                    if not value:continue
                    px=left+(15-x if flag&64 else x);py=top+(15-y if flag&128 else y)
                    if not 0<=px<width or not 0<=py<height:raise ValueError('Overlap outside target')
                    canvas[py*width+px]=value
        if bytes(canvas)!=target.tobytes():raise ValueError('Overlap would change a visible variant')
    return bytes(result)


def remap_tiles(packed,tile_count,mapping,flips=None,shifts=None):
    """표시 픽셀을 보존하는 타일 순열·반전·투명 여백 이동. 파츠 좌표도 함께 갱신해야 한다."""
    flips=flips or {};shifts=shifts or {}
    if set(mapping)!=set(mapping.values()) or any(type(t) is not int or not 0<=t<tile_count for t in mapping):
        raise ValueError('Invalid tile permutation')
    if not set(flips)<=set(mapping) or any(v not in (0,64,128,192) for v in flips.values()):
        raise ValueError('Invalid tile flip')
    if not set(shifts)<=set(mapping):raise ValueError('Unknown shifted tile')
    atlas,positions,_=indexed_atlas(packed,tile_count);dst=bytearray(packed)
    for old,new in mapping.items():
        flag=flips.get(old,0);dx,dy=shifts.get(old,(0,0))
        if type(dx) is not int or type(dy) is not int or abs(dx)>15 or abs(dy)>15:raise ValueError('Invalid tile shift')
        if new%16==0 and flag&64:raise ValueError('Page-edge tile cannot be flipped horizontally')
        tile=bytearray(256)
        for y in range(16):
            for x in range(16):
                value=atlas[(old//16*16+y)*256+old%16*16+x]
                if not value:continue
                tx,ty=x+dx,y+dy
                if not 0<=tx<16 or not 0<=ty<16:raise ValueError('Tile shift would discard visible pixels')
                if flag&64:tx=15-tx
                if flag&128:ty=15-ty
                if new%16==0 and tx==0:raise ValueError('Opaque page-edge source column')
                if flag&128 and (new//16)%16==0 and ty==0:raise ValueError('Opaque page-edge source row under vertical flip')
                tile[ty*16+tx]=value
        for y in range(16):
            for x in range(16):
                off,shift=positions[(new//16*16+y)*256+new%16*16+x]
                dst[off]=(dst[off]&~(15<<shift))|(tile[y*16+x]<<shift)
    return bytes(dst)


def pack_rectangles(packed, tile_count, pixels, size, rectangles, tile_ids, cleared_tiles):
    """한 화면 픽셀은 한 타일만 소유한다. 지정하지 않은 타일은 보존한다."""
    width, height = size
    if width <= 0 or height <= 0 or len(pixels) != width * height or any(p > 15 for p in pixels):
        raise ValueError('Invalid indexed canvas')
    if len(rectangles) != len(tile_ids) or len(set(tile_ids)) != len(tile_ids):
        raise ValueError('Tile assignment must be one-to-one')
    cleared = set(cleared_tiles)
    if not set(tile_ids) <= cleared or any(type(t) is not int or not 0 <= t < tile_count for t in cleared):
        raise ValueError('Tile assignment escaped writable tiles')
    for r in rectangles:
        if len(r) != 2 or any(type(v) is not int for v in r):
            raise ValueError('Invalid tile rectangle')
        x, y = r
        if x < 0 or y < 0 or x + 16 > width or y + 16 > height:
            raise ValueError('Tile rectangle outside canvas')
    _, mapping, _ = indexed_atlas(packed, tile_count)
    result = bytearray(packed)

    def put(tile, x, y, value):
        off, shift = mapping[((tile // 16) * 16 + y) * 256 + (tile % 16) * 16 + x]
        result[off] = (result[off] & ~(15 << shift)) | (value << shift)

    for tile in cleared:
        for y in range(16):
            for x in range(16):
                put(tile, x, y, 0)
    remaining = bytearray(pixels)
    for (left, top), tile in zip(rectangles, tile_ids):
        for y in range(16):
            for x in range(16):
                position = (top + y) * width + left + x
                value = remaining[position]
                if value:
                    put(tile, x, y, value)
                    remaining[position] = 0
    if any(remaining):
        raise ValueError('Opaque pixels were not covered by allocated parts')
    atlas,_,_=indexed_atlas(result,tile_count)
    for tile in tile_ids:
        if tile%16==0 and any(atlas[((tile//16)*16+y)*256] for y in range(16)):
            raise ValueError('Opaque page-edge source column would clip when mirrored')
    return bytes(result)
