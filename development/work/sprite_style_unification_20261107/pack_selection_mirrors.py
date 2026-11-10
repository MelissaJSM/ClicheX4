"""Exact tile flip reuse inside the original target-owned UI allocation."""
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels,write_tile

def flip(pixels, bits):
    return bytes(pixels[(15-y if bits&0x80 else y)*16+(15-x if bits&0x40 else x)]
                 for y in range(16) for x in range(16))

def repack(texture, original_parts, positioned, bank, targets, overrides):
    count=composition_frame(original_parts,bank,0)['bank_frame_count']
    owned={p['page']*256+p['tile'] for n in targets for p in composition_frame(original_parts,bank,n)['parts']}
    reserved=set(range(len(texture)//128))-owned
    reserved|={p['page']*256+p['tile'] for n in range(count) if n not in targets for p in composition_frame(original_parts,bank,n)['parts']}
    free=[t for t in range(len(texture)//128) if t not in reserved]
    def safe(px,t):return (t%16!=0 or not any(px[::16])) and (t%256>=16 or not any(px[:16]))
    choices={};allocated=set();pattern_count=0
    def add(px,t):
        for bits in (0,0x40,0x80,0xc0):choices.setdefault(flip(px,bits),(t,bits))
    for t in sorted(reserved):
        px=tile_pixels(texture,t)
        if safe(px,t):add(px,t)
    nt,np=bytearray(texture),bytearray(positioned);demands={};flipped=[]
    for n,(data,size) in sorted(targets.items()):
        c=local_composition(composition_frame(positioned,bank,n));_,expected,bounds,coverage=compose_static(texture,c)
        assert size==expected and len(data)==size[0]*size[1]
        assert all(v<=15 and (not v or covered) for v,covered in zip(data,coverage))
        owners=[-1]*len(data)
        for j,p in enumerate(c['parts']):
            for y in range(16):
                for x in range(16):owners[(p['y']-bounds[1]+y)*size[0]+p['x']-bounds[0]+x]=j
        for j,p in enumerate(c['parts']):
            px=bytearray(256)
            for y in range(16):
                for x in range(16):
                    dx=p['x']-bounds[0]+(15-x if p['flip_x'] else x)
                    dy=p['y']-bounds[1]+(15-y if p['flip_y'] else y);i=dy*size[0]+dx
                    px[y*16+x]=data[i] if owners[i]==j else 0
            pixels=bytes(px)
            if pixels not in choices:
                candidates=[(bits,flip(pixels,bits)) for bits in (0,0x40,0x80,0xc0)]
                match=next(((t,bits,q) for t in free for bits,q in candidates if safe(q,t)),None)
                if match is None:raise ValueError('Target-owned selection allocation still exceeded')
                t,bits,q=match;free.remove(t);write_tile(nt,t,q);add(q,t);allocated.add(t);pattern_count+=1
            tile,bits=choices[pixels]
            flags=((p['flags']^bits)&~3)|(tile//256)
            if n in overrides:flags=(flags&~12)|(overrides[n]<<2)
            value=bytes((flags,tile%256));off=p['record_offset']
            assert off not in demands or demands[off]==value
            demands[off]=value;np[off:off+2]=value
            if bits:flipped.append({'frame':n,'record_offset':off,'flip_xor':bits,'tile':tile})
    nt,np=bytes(nt),bytes(np)
    for n in range(count):
        actual=compose_static(nt,local_composition(composition_frame(np,bank,n)))[:2]
        expected=targets.get(n,compose_static(texture,local_composition(composition_frame(original_parts,bank,n)))[:2])
        assert actual==expected,f'UI render differs:{n}'
    assert all(tile_pixels(nt,t)==tile_pixels(texture,t)for t in reserved)
    return nt,np,{'original_owned_tiles':len(owned),'reserved_tiles_exact':len(reserved),'new_patterns':pattern_count,'new_slots_used':len(allocated),'free_owned_slots':len(free),'part_flip_reuses':flipped,'all_target_and_non_target_pixels_exact':True,'uv_zero_edges_guarded':True,'original_part_counts_preserved':True}
