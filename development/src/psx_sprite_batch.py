"""기존 파츠 배치의 공유 픽셀 제약을 지키는 원본 크기 편집 보조."""
import numpy as np

def inherited_recolored_part(before,after,old_part,new_part):
    """원래 경계 파츠를 그대로 사용한 색상 교체인지 확인한다."""
    if old_part!=new_part or len(before)!=len(after):return False
    a=np.frombuffer(bytes(before),np.uint8);b=np.frombuffer(bytes(after),np.uint8)
    if not np.array_equal(a==0,b==0):return False
    return all(len(np.unique(b[a==color]))==1 for color in np.unique(a))
from src.psx_player import indexed_atlas,compose_indices

def canvas_from_parts(raw,count,comp,size=(160,160),origin=(80,80)):
    pix,wh,bounds,_=compose_indices(raw,count,comp,allowed_cluts={0,2})
    image=np.frombuffer(pix,np.uint8).reshape(wh[1],wh[0]);out=np.zeros((size[1],size[0]),np.uint8)
    yy,xx=np.nonzero(image);xx=xx+bounds[0]+origin[0];yy=yy+bounds[1]+origin[1]
    if len(xx) and (xx.min()<0 or yy.min()<0 or xx.max()>=size[0] or yy.max()>=size[1]):raise ValueError('Visible pixels outside canvas')
    sy,sx=np.nonzero(image);out[yy,xx]=image[sy,sx]
    return out

def recolor_tiles(raw,count,tiles,mapping):
    if len(mapping)!=16 or mapping[0]!=0 or any(type(v)is not int or not 0<=v<16 for v in mapping) or any(v==0 for v in mapping[1:]):raise ValueError('Invalid opaque-preserving color map')
    if any(type(t)is not int or not 0<=t<count for t in tiles):raise ValueError('Invalid recolor tile')
    atlas,locations,_=indexed_atlas(raw,count);out=bytearray(raw)
    for t in tiles:
        for y in range(16):
            for x in range(16):
                i=(t//16*16+y)*256+t%16*16+x;off,shift=locations[i];out[off]=(out[off]&~(15<<shift))|(mapping[atlas[i]]<<shift)
    return bytes(out)

def pack_original_layout(raw,count,target,comp,writable,origin=(80,80)):
    """여러 위치에 쓰는 타일 픽셀은 모든 표시 위치가 일치할 때만 기록한다."""
    if target.ndim!=2 or target.dtype!=np.uint8 or target.max()>15:raise ValueError('Invalid target')
    atlas,locations,_=indexed_atlas(raw,count);out=bytearray(raw);uses={t:[] for t in writable}
    if any(not 0<=t<count for t in writable):raise ValueError('Invalid writable set')
    for q in comp['parts']:
        if q['tile'] in writable:uses[q['tile']].append(q)
    for t in writable:
        if not uses[t]:raise ValueError('Unreferenced writable tile')
        for y in range(16):
            for x in range(16):
                values=set()
                for q in uses[t]:
                    px=origin[0]+q['x']+(15-x if q['flip_x'] else x);py=origin[1]+q['y']+(15-y if q['flip_y'] else y)
                    if not 0<=px<target.shape[1] or not 0<=py<target.shape[0]:raise ValueError('Part outside canvas')
                    values.add(int(target[py,px]))
                value=next(iter(values)) if len(values)==1 else 0
                off,shift=locations[(t//16*16+y)*256+t%16*16+x];out[off]=(out[off]&~(15<<shift))|(value<<shift)
    if not np.array_equal(canvas_from_parts(out,count,comp,(target.shape[1],target.shape[0]),origin)%16,target):raise ValueError('Original layout cannot encode target exactly')
    return bytes(out)
