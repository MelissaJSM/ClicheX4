"""정수 좌표의 인덱스 마스터 시트. 패딩을 프레임 데이터로 잘라 버리지 않는다."""


def validate_layout(layout):
    width, height = layout['size']
    if any(type(v) is not int or v <= 0 for v in (width, height)):
        raise ValueError('Invalid sheet size')
    used = bytearray(width*height)
    keys = set()
    for frame in layout['frames']:
        key = frame['key']
        if key in keys:
            raise ValueError('Duplicate frame key')
        keys.add(key)
        x, y, w, h = frame['rect']
        if any(type(v) is not int for v in (x, y, w, h)) or min(w,h) <= 0 or min(x,y) < 0 or x+w > width or y+h > height:
            raise ValueError('Frame rectangle outside sheet')
        for row in range(y, y+h):
            start = row*width+x
            if any(used[start:start+w]):
                raise ValueError('Overlapping frame rectangles')
            used[start:start+w] = b'\1'*w
    if not keys:
        raise ValueError('Empty frame layout')
    return used


def pack_frames(frames, columns=8, cell=(96,96), origin=(48,48), *, max_index=15):
    """frames: key -> (indices, native_size, world_bounds). 축척/자동 크롭 없음."""
    if not frames or columns < 1 or min(cell) <= 0 or max_index not in (15,63):
        raise ValueError('Invalid sheet geometry')
    width, height = columns*cell[0], ((len(frames)+columns-1)//columns)*cell[1]
    records = []
    for index, (key, (_, size, bounds)) in enumerate(frames.items()):
        w, h = size
        x0, y0, x1, y1 = bounds
        if (x1-x0,y1-y0) != tuple(size):
            raise ValueError('Native bounds and dimensions differ')
        cx, cy = index%columns*cell[0], index//columns*cell[1]
        x, y = cx+origin[0]+x0, cy+origin[1]+y0
        if x<cx or y<cy or x+w>cx+cell[0] or y+h>cy+cell[1]:
            raise ValueError('Frame does not fit fixed cell')
        records.append({'key':key,'rect':[x,y,w,h],'bounds':list(bounds),
                        'cell':[cx,cy,*cell],'world_origin':[cx+origin[0],cy+origin[1]]})
    layout = {'size':[width,height],'cell':list(cell),'origin':list(origin),'columns':columns,'frames':records}
    if max_index != 15: layout['max_index'] = max_index
    validate_layout(layout)
    pixels = bytearray(width*height)
    for record in records:
        data, size, _ = frames[record['key']]
        x,y,w,h = record['rect']
        if len(data)!=w*h or max(data,default=0)>max_index:
            raise ValueError('Invalid 4bpp frame')
        for row in range(h):
            pixels[(y+row)*width+x:(y+row)*width+x+w] = data[row*w:(row+1)*w]
    return bytes(pixels), layout


def unpack_frames(pixels, size, layout):
    if tuple(size) != tuple(layout['size']) or len(pixels)!=size[0]*size[1]:
        raise ValueError('Master sheet dimensions changed')
    used = validate_layout(layout)
    limit=layout.get('max_index',15)
    if limit not in (15,63) or max(pixels,default=0)>limit:
        raise ValueError('Pixel index exceeds 4bpp palette')
    if any(pixel and not occupied for pixel,occupied in zip(pixels,used)):
        raise ValueError('Opaque pixel outside native frame rectangles')
    width = size[0]
    result = {}
    for frame in layout['frames']:
        x,y,w,h = frame['rect']
        result[frame['key']] = (b''.join(pixels[row*width+x:row*width+x+w] for row in range(y,y+h)),(w,h))
    return result
