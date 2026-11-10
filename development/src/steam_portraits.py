"""Lossless static portrait packing, independent of the PS1 shared-tile layout."""
import struct
from .steam_arc import pat_from_ps1
from .steam_ui import pat_frames
from .steam_player import tex_geometry

def encode_banks(banks):
    blocks=[]
    for frames in banks:
        loc=len(frames);headers=bytearray()
        for frame in frames:
            if len(frame)%4 or loc+len(frame)//4>65535:raise ValueError('Invalid quad count')
            headers.extend(struct.pack('<HH',len(frame)//4,loc));loc+=len(frame)//4
        blocks.append(bytes(headers)+b''.join(frames))
    offsets=[];off=4*len(blocks)
    for block in blocks:offsets.append(off);off+=len(block)
    result=pat_from_ps1(struct.pack('<'+'I'*len(offsets),*offsets)+b''.join(blocks))
    if pat_frames(result)!=banks:raise ValueError('PAT readback mismatch')
    return result

def tile(pixels,index):
    x=index%16*16;y=index//16*16
    rows=[pixels[(y+r)*256+x:(y+r)*256+x+16] for r in range(16)]
    if any(len(r)!=16 for r in rows):raise ValueError('Quad outside source texture')
    return b''.join(rows)

def pack(tex,frames,pixels):
    tex_geometry(tex);patterns={};newframes=[]
    for frame in frames:
        out=bytearray()
        for flags,t,x,y in struct.iter_unpack('<BBbb',frame):
            px=tile(pixels,(flags&3)*256+t)
            if px not in patterns:patterns[px]=len(patterns)
            k=patterns[px]
            if k>=1024:raise ValueError('Static PAT page capacity exceeded')
            out.extend(struct.pack('<BBbb',(flags&~3)|(k//256),k%256,x,y))
        newframes.append(bytes(out))
    height=16
    while height<((len(patterns)+15)//16)*16:height*=2
    result=bytearray(tex[:20])+bytearray(256*height)
    struct.pack_into('<I',result,8,1|(256<<6)|(height<<19))
    for px,k in patterns.items():
        x=k%16*16;y=k//16*16
        for r in range(16):result[20+(y+r)*256+x:20+(y+r)*256+x+16]=px[r*16:r*16+16]
    for old,new in zip(frames,newframes):
        for a,b in zip(struct.iter_unpack('<BBbb',old),struct.iter_unpack('<BBbb',new)):
            if (a[0]&~3,a[2:])!=(b[0]&~3,b[2:]) or tile(pixels,(a[0]&3)*256+a[1])!=tile(result[20:],(b[0]&3)*256+b[1]):
                raise ValueError('Portrait pixel/geometry/CLUT/flip mismatch')
    return bytes(result),newframes
