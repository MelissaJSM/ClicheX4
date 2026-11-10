"""PS1 indexed player graphics -> verified Steam TEX/COF layout, no resampling."""
import struct
from .psx_player import graphics_bank, decode_stream, indexed_atlas


def tex_geometry(tex):
    if tex[:4]!=b'TEX\0' or len(tex)<20 or tex[13]!=0x12:raise ValueError('Expected indexed TEX')
    dims=struct.unpack_from('<I',tex,8)[0]
    w,h,mip=(dims>>6)&8191,dims>>19,dims&63
    start=struct.unpack_from('<I',tex,16)[0]
    if w!=256 or mip!=1 or start!=20 or len(tex)!=start+w*h:raise ValueError('Unverified TEX geometry')
    return w,h,start


def dynamic_texture(tex,cof,graphics,bank_id,*,allow_count_expansion=False,allow_npot_height=False):
    width,old_height,tex_start=tex_geometry(tex)
    if cof[:4]!=b'COF\0' or struct.unpack_from('<I',cof,4)[0]!=2:raise ValueError('Expected COF v2')
    cp=17+cof[16]
    if cp+4+256*4!=len(cof):raise ValueError('Unverified COF table')
    old_count=struct.unpack_from('<I',cof,cp)[0]
    bank=graphics_bank(graphics,bank_id,allow_bank_aliases=True)
    count=len(bank['frames'])
    if old_count!=count and not allow_count_expansion:raise ValueError('Unresolved COF/frame mapping')
    if not 0<count<=256:raise ValueError('COF reference count exceeds fixed table')
    blocks={};ys=[];height=0;frames=[]
    for frame in bank['frames']:
        packed=decode_stream(graphics,frame['offset'],frame['limit'],frame['tile_count']*128).data
        key=(frame['tile_count'],packed)
        if key not in blocks:
            pixels,_,rows=indexed_atlas(packed,frame['tile_count'])
            blocks[key]=(height,pixels)
            height+=rows
        ys.append(blocks[key][0]);frames.append((frame,key))
    new_height=old_height
    while new_height<height:new_height*=2
    if new_height>4096:
        if not allow_npot_height:raise ValueError('Texture expansion exceeds currently verified 4096 height')
        new_height=(height+255)//256*256
        if new_height>7936:raise ValueError('TEX height field overflow')
    pixels=bytearray(width*new_height)
    for y,block in blocks.values():pixels[y*width:y*width+len(block)]=block
    new_tex=bytearray(tex[:tex_start])+pixels
    dims=struct.unpack_from('<I',new_tex,8)[0]
    struct.pack_into('<I',new_tex,8,(dims&0x7ffff)|(new_height<<19))
    new_cof=bytearray(cof)
    struct.pack_into('<I',new_cof,cp,count)
    struct.pack_into('<256I',new_cof,cp+4,*(ys+list(struct.unpack_from('<256I',cof,cp+4))[count:]))
    # Every referenced atlas must reproduce the source indices exactly after serialization.
    for (frame,key),y in zip(frames,ys):
        expected=blocks[key][1]
        if bytes(new_tex[tex_start+y*width:tex_start+y*width+len(expected)])!=expected:
            raise ValueError('TEX read-back mismatch')
    return bytes(new_tex),bytes(new_cof),{'bank':bank_id,'references':count,'old_cof_count':old_count,'unique_blocks':len(blocks),
                                         'old_height':old_height,'new_height':new_height,'used_rows':height,
                                         'index_roundtrip_exact':True}


def unpack_indices(packed):
    return bytes(v for b in packed for v in (b&15,b>>4))


def static_texture(tex,original_packed,new_packed):
    _,_,start=tex_geometry(tex)
    old=unpack_indices(original_packed);new=unpack_indices(new_packed)
    if len(old)!=len(new) or tex[start:start+len(old)]!=old:
        raise ValueError('Static atlas does not match original PS1 layout')
    return tex[:start]+new+tex[start+len(new):]
