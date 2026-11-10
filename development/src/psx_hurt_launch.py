"""Bank0 launch hurt: retain original CLUT selectors and derive every flash.

PNG indices encode clut*16+nibble (zero remains transparent). This is an
editing representation, not an increase in the game's per-part 4bpp depth.
"""
from src.psx_player import composition_frame, compose_indices, graphics_bank, decode_stream, indexed_atlas
from src.psx_frame_edit import edit_frame_indices, frame_coverage
from src.psx_hurt import flash_from_body

LAUNCH_FRAMES=frozenset(range(139,146))
MULTI_FRAMES=frozenset((140,141,143,145))
LIGHT_MAP=bytes((0,3,6,7,8,7,12,12,14,11,12,12,15,12,15,15))

def compose_launch(packed,tiles,composition):
    if composition['bank']!=0 or composition['frame'] not in LAUNCH_FRAMES:
        return compose_indices(packed,tiles,composition)
    return compose_indices(packed,tiles,composition,allowed_cluts={0,2})

def local_layer(comp,parts):
    return {**comp,'parts':[{**p,'clut':0,'flags':p['flags']&~12} for p in parts]}

def geometry_equal(a,b):
    return [{k:v for k,v in p.items() if k!='record_offset'} for p in a]==[{k:v for k,v in p.items() if k!='record_offset'} for p in b]

def shared_body(packed,tiles,comps,base_number,base):
    body=comps[base_number];count=len(body['parts'])
    if count != (10 if base_number==139 else 11) or any(p['clut'] for p in body['parts']):
        raise ValueError('Unexpected launch body geometry')
    body_sources={s for v in frame_coverage(packed,tiles,body)[0] for s in v}
    for n,c in comps.items():
        if n==base_number:continue
        if not geometry_equal(body['parts'],c['parts'][:count]) or any(p['clut']!=2 for p in c['parts'][count:]):
            raise ValueError('Launch overlay no longer shares the verified body')
        layer=local_layer(c,c['parts'][count:])
        sources={s for v in frame_coverage(packed,tiles,layer)[0] for s in v}
        if sources&body_sources:raise ValueError('Launch body aliases effect pixels')
    return edit_frame_indices(packed,tiles,body,*base)

def place_world(base,bounds,target_size,target_bounds,mapping=None):
    data,size=base;out=bytearray(target_size[0]*target_size[1])
    for i,v in enumerate(data):
        if not v:continue
        x=i%size[0]+bounds[0]-target_bounds[0];y=i//size[0]+bounds[1]-target_bounds[1]
        if not 0<=x<target_size[0] or not 0<=y<target_size[1]:raise ValueError('Launch body escaped canvas')
        out[y*target_size[0]+x]=mapping[v] if mapping else v
    return bytes(out),target_size

def derive_launch(gfx,parts,base,*,light_mapping=LIGHT_MAP,flash_fill=12,flash_outline=15):
    if len(light_mapping)!=16 or light_mapping[0]!=0 or any(not 1<=v<16 for v in light_mapping[1:]):raise ValueError('Invalid light palette mapping')
    bank=graphics_bank(gfx,0);raws={};comps={}
    for n in LAUNCH_FRAMES:
        f=bank['frames'][n];raws[n]=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        comps[n]=composition_frame(parts,0,n)
    for family in ((139,140,141),(144,145)):
        if len({(bank['frames'][n]['offset'],bank['frames'][n]['tile_count']) for n in family})!=1:
            raise ValueError('Launch stream sharing changed')
    f=bank['frames'][139];edited=shared_body(raws[139],f['tile_count'],{n:comps[n] for n in (139,140,141)},139,base)
    streams={139:edited};frames={n:compose_launch(edited,f['tile_count'],comps[n])[:2] for n in (139,140,141)}
    bounds=compose_launch(edited,f['tile_count'],comps[139])[2]
    for n in (142,143,144):
        f=bank['frames'][n];comp=comps[n]
        if n==143 and any(p['clut']!=2 for p in comp['parts']):raise ValueError('Launch flash CLUT changed')
        local=local_layer(comp,comp['parts']);_,size,b,_=compose_indices(raws[n],f['tile_count'],local)
        if n==142:picture=flash_from_body(base,bounds,size,b,fill_index=flash_fill,outline_index=flash_outline)
        elif n==144:picture=place_world(base,bounds,size,b,light_mapping)
        else:
            # The original CLUT2 silhouette uses 15 for the body, 5..9 for arcs.
            silhouette=place_world(base,bounds,size,b,bytes([0]+[15]*15))
            data=bytearray(silhouette[0]);w,h=size
            for y in range(h):
                for x in range(w):
                    i=y*w+x
                    if data[i] and any(not (0<=x+dx<w and 0<=y+dy<h) or not silhouette[0][(y+dy)*w+x+dx] for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))):data[i]=5
            picture=(bytes(data),size)
        if n==144:
            value=shared_body(raws[n],f['tile_count'],{k:comps[k] for k in (144,145)},144,picture)
            # Replace the body-shaped original aura with a ring around Riko.
            overlay=local_layer(comps[145],comps[145]['parts'][11:])
            _,os,ob,_=compose_indices(value,f['tile_count'],overlay)
            mask=place_world(base,bounds,os,ob)[0];ring=bytearray(len(mask));ow,oh=os
            for y in range(oh):
                for x in range(ow):
                    i=y*ow+x
                    if mask[i]:continue
                    distance=min((abs(dx)+abs(dy) for dy in range(-2,3) for dx in range(-2,3) if 0<=x+dx<ow and 0<=y+dy<oh and mask[(y+dy)*ow+x+dx]),default=99)
                    if distance<=2:ring[i]=5 if distance==1 else 6
            value=edit_frame_indices(value,f['tile_count'],overlay,bytes(ring),os)
        else:
            try:value=edit_frame_indices(raws[n],f['tile_count'],local,*picture)
            except ValueError as exc:raise ValueError(f'Launch frame {n}: {exc}') from exc
        streams[n]=value;frames[n]=compose_launch(value,f['tile_count'],comp)[:2]
        if n==144:frames[145]=compose_launch(value,f['tile_count'],comps[145])[:2]
    for n,value in streams.items():
        tiles=bank['frames'][n]['tile_count'];before,locations,height=indexed_atlas(raws[n],tiles)
        after=indexed_atlas(value,tiles)[0]
        if any(after[y*256] and after[y*256]!=before[y*256] for y in range(height)):
            raise ValueError(f'New opaque reflected U=0 edge in launch stream {n}')
    return frames,streams

def validate_launch(gfx,parts,frames):
    if not LAUNCH_FRAMES<=frames.keys():raise ValueError('All seven launch references are required')
    expected,streams=derive_launch(gfx,parts,frames[139])
    if any(frames[n]!=expected[n] for n in LAUNCH_FRAMES):raise ValueError('Launch derivative differs from body/effect specification')
    return streams,{'frames':sorted(LAUNCH_FRAMES),'base_frame':139,'clut_selectors_preserved':True,
        'effects_derived_from_riko_body':True,'light_mapping':list(LIGHT_MAP),'clut2_indices_encoded_above_32':True}
