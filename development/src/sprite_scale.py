"""고정된 기준 패치의 실제 인덱스 픽셀을 비교하는 동작 간 크기 검사."""


def validate_reference_views(frames, bounds, views, assignments, placements):
    """명시된 방향별 기준을 검증한다. 프레임이 임의로 기준을 생략할 수 없다."""
    keys={str(n) for n in frames}
    if set(assignments)!=keys or set(placements)!=keys or any(v not in views for v in assignments.values()):
        raise ValueError('Every frame needs a known reference view and placement')
    reports={}
    for name,(reference,size,roi) in views.items():
        subset={n:v for n,v in frames.items() if assignments[str(n)]==name}
        if subset:
            reports[name]=validate_fixed_reference(subset,bounds,reference,size,roi,
                                                  {str(n):placements[str(n)] for n in subset})
    return {'checked_frames':sorted(frames),'views':reports,'head_neck_pixels_exact_for_view':True,
            'full_anatomical_quality_automatically_proven':False}


def validate_fixed_reference(frames, bounds, reference, reference_size, roi, placements):
    """머리·목 패치의 확대/축소·누락을 거부한다. 자세별 전체 높이는 강제하지 않는다."""
    x0,y0,x1,y1=roi;rw,rh=reference_size
    if not 0<=x0<x1<=rw or not 0<=y0<y1<=rh or len(reference)!=rw*rh:
        raise ValueError('Invalid scale reference rectangle')
    if set(placements)!={str(n) for n in frames}:
        raise ValueError('Every motion frame needs a scale reference placement')
    width,height=x1-x0,y1-y0
    patch=b''.join(reference[y*rw+x0:y*rw+x1] for y in range(y0,y1))
    checked=[]
    for n,(pixels,size) in frames.items():
        w,h=size;position=placements[str(n)]
        if len(position)!=2 or any(type(v) is not int for v in position):
            raise ValueError('Scale reference position must use native integer pixels')
        x,y=position[0]-bounds[n][0],position[1]-bounds[n][1]
        if len(pixels)!=w*h or x<0 or y<0 or x+width>w or y+height>h:
            raise ValueError(f'Frame {n}: reference patch outside native canvas')
        actual=b''.join(pixels[row*w+x:row*w+x+width] for row in range(y,y+height))
        # Transparent corners belong to the canvas, not the anatomy. Cape fabric
        # may pass behind the head without erasing any approved foreground pixel.
        if any(expected and value!=expected for value,expected in zip(actual,patch)):
            raise ValueError(f'Frame {n}: head/neck scale or identity differs from approved native reference')
        checked.append(n)
    return {'reference_patch_size':[width,height],'checked_frames':sorted(checked),
            'head_neck_pixels_exact':True,'transparent_background_compared':False,'whole_pose_height_forced':False,
            'full_anatomical_quality_automatically_proven':False}
