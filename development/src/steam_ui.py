"""Verified static UI atlas/page conversion for the X4 Steam resources."""
import struct

from .steam_player import unpack_indices


def stage_texture(tex, original_packed, new_packed):
    """PS1 256-wide pages are arranged eight per row in the PC stage TEX."""
    if len(tex)<20 or tex[:4]!=b'TEX\0' or tex[13]!=0x12:
        raise ValueError('Expected indexed stage TEX')
    dims=struct.unpack_from('<I',tex,8)[0]
    width,height,mips=(dims>>6)&8191,dims>>19,dims&63
    start=struct.unpack_from('<I',tex,16)[0]
    if width!=2048 or height!=2048 or mips!=1 or start!=20 or len(tex)!=start+width*height:
        raise ValueError('Unverified stage TEX geometry')
    if len(original_packed)!=len(new_packed) or len(new_packed)%2048:
        raise ValueError('Stage atlas size changed or incomplete tile rows')
    old,new=unpack_indices(original_packed),unpack_indices(new_packed)
    if len(old)>width*height:
        raise ValueError('Stage atlas exceeds TEX')
    result=bytearray(tex)
    for y in range(len(old)//256):
        page,row=divmod(y,256)
        pos=start+(page//8*256+row)*width+page%8*256
        source=y*256
        if tex[pos:pos+256]!=old[source:source+256]:
            raise ValueError('Original stage page mismatch')
        result[pos:pos+256]=new[source:source+256]
    return bytes(result)


def pat_frames(pat):
    """Read the Steam PAT3 structure, independently of PS1 bank offsets."""
    if len(pat)<12 or pat[:8]!=b'PAT\0'+struct.pack('<I',3):
        raise ValueError('Expected PAT3')
    nb=struct.unpack_from('<I',pat,8)[0]
    if not 0<nb<=256:raise ValueError('PAT bank count')
    pos=12;counts=[]
    for _ in range(nb):
        if pos+4>len(pat):raise ValueError('Truncated PAT counts')
        nf=struct.unpack_from('<I',pat,pos)[0];pos+=4
        if not 0<nf<=4096 or pos+nf*4>len(pat):raise ValueError('PAT frame count')
        counts.append(list(struct.unpack_from('<'+'I'*nf,pat,pos)));pos+=nf*4
    headers=[]
    for values in counts:
        if pos+len(values)*4>len(pat):raise ValueError('Truncated PAT headers')
        headers.append([struct.unpack_from('<HH',pat,pos+i*4) for i in range(len(values))])
        pos+=len(values)*4
    banks=[]
    for values,entries in zip(counts,headers):
        bank=[];cumulative=len(values)
        for expected,(n,location) in zip(values,entries):
            if n!=expected or location!=cumulative or pos+n*4>len(pat):
                raise ValueError('Invalid PAT quad table')
            bank.append(pat[pos:pos+n*4]);pos+=n*4;cumulative+=n
        banks.append(bank)
    if pos!=len(pat):raise ValueError('Unexpected PAT tail')
    return banks
