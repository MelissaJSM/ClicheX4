"""확인된 ePSXe 상태의 VRAM 업로드와 320×240 프레임버퍼 대조. 파일 수정 없음."""
import struct


def locate_vram(state, packed, tiles, upload_x=320):
    width = min(tiles,16)*8
    row = max(range(16),key=lambda y:len(set(packed[y*width:(y+1)*width])))
    signature=packed[row*width:(row+1)*width]
    starts=[]; cursor=0
    while True:
        hit=state.find(signature,cursor)
        if hit<0:break
        cursor=hit+1
        base=hit-row*2048-upload_x*2
        if base<0 or base+1048576>len(state):continue
        offset=0; valid=True
        for first in range(0,tiles,16):
            row_bytes=min(tiles-first,16)*8
            for y in range(16):
                pos=base+(first//16*16+y)*2048+upload_x*2
                if state[pos:pos+row_bytes]!=packed[offset:offset+row_bytes]:valid=False
                offset+=row_bytes
        if valid:starts.append(base)
    if len(starts)!=1:raise ValueError('VRAM upload match is not unique')
    return starts[0]


def framebuffer(state, vram, page_y):
    import numpy as np
    from PIL import Image
    words=np.ndarray((240,320),dtype='<u2',buffer=state,offset=vram+page_y*2048,strides=(2048,2))
    rgb=np.stack(((words&31)*255//31,((words>>5)&31)*255//31,((words>>10)&31)*255//31),axis=2).astype(np.uint8)
    return Image.fromarray(rgb)


def match_sprite(screen, sprite):
    import numpy as np
    scene=np.array(screen.convert('RGB'))
    image=np.array(sprite.convert('RGBA'))
    matches=[]
    for flipped in (False,True):
        pixels=image[:,::-1] if flipped else image
        ys,xs=np.nonzero(pixels[:,:,3])
        if not len(xs):continue
        # A dark outline pixel occurs thousands of times in a stage background.
        # Filter candidate origins with up to three distinct, sparse sprite
        # colors before the unchanged full opaque-pixel comparison.
        _,first,counts=np.unique(pixels[ys,xs,:3],axis=0,return_index=True,return_counts=True)
        anchors=first[np.argsort(counts,kind='stable')[:3]]
        a=anchors[0];sy,sx=int(ys[a]),int(xs[a])
        cy,cx=np.nonzero(np.all(scene==pixels[sy,sx,:3],axis=2));cy=cy-sy;cx=cx-sx
        keep=(cy>=0)&(cx>=0)&(cy+pixels.shape[0]<=scene.shape[0])&(cx+pixels.shape[1]<=scene.shape[1])
        cy,cx=cy[keep],cx[keep]
        for a in anchors[1:]:
            keep=np.all(scene[cy+ys[a],cx+xs[a]]==pixels[ys[a],xs[a],:3],axis=1)
            cy,cx=cy[keep],cx[keep]
        for y,x in zip(cy,cx):
            if np.array_equal(scene[y+ys,x+xs],pixels[ys,xs,:3]):
                matches.append({'x':int(x),'y':int(y),'flip_x':flipped,'opaque_pixels_equal':len(xs)})
    return matches
