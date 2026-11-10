"""US Zero arrival: Riko body and deterministic materialization flashes.

Only bank0 bitmap references 247..253 change; beam-only 53..60 stay intact.
"""
from src.psx_player import graphics_bank, decode_stream, composition_frame, compose_indices

BEAM_BODY_FRAMES = frozenset(range(247,254))
BEAM_DERIVED_FRAMES = frozenset(range(247,251))
BEAM_KEY_FRAMES = frozenset((251,252,253))
BEAM_PURE_EFFECT_FRAMES = frozenset(range(53,61))

# All entries retain transparent index0. Color indices belong to the approved
# Riko normal palette, not Zero's original red/yellow palette.
PALE = (0,12,12,12,15,15,12,15,15,15,12,12,15,12,15,15)
BRIGHT = (0,2,12,12,8,12,12,12,14,15,12,12,15,12,15,15)

def materialize(base, bounds, size, target_bounds, phase):
    pixels, base_size = base
    if phase not in BEAM_DERIVED_FRAMES or len(pixels) != base_size[0]*base_size[1]:
        raise ValueError('Unsupported arrival phase or body dimensions')
    body={(i%base_size[0]+bounds[0],i//base_size[0]+bounds[1]):v for i,v in enumerate(pixels) if v}
    if not body or any(v>15 for v in body.values()):raise ValueError('Expected indexed arrival body')
    image={}
    if phase in (247,248):
        radius=2 if phase==247 else 0
        for x,y in body:
            for dx in range(-radius,radius+1):
                for dy in range(-radius,radius+1):
                    if abs(dx)+abs(dy)<=radius:image[x+dx,y+dy]=12 if phase==247 else 15
        image.update({xy:15 for xy in body})
    else:
        lookup=PALE if phase==249 else BRIGHT
        image={xy:lookup[v] for xy,v in body.items()}
    out=bytearray(size[0]*size[1])
    for (x,y),v in image.items():
        if not target_bounds[0]<=x<target_bounds[2] or not target_bounds[1]<=y<target_bounds[3]:
            raise ValueError('Arrival glow escaped original canvas')
        out[(y-target_bounds[1])*size[0]+x-target_bounds[0]]=v
    return bytes(out),size

def derive_beam_frames(gfx,parts,base,*,dynamic=False):
    bank=graphics_bank(gfx,0)
    def native(n):
        f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        return compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))
    _,size,bounds,_=native(249 if dynamic else 251)
    if tuple(base[1])!=size:raise ValueError('Arrival base dimensions changed')
    return {n:materialize(base,bounds,native(n)[1],native(n)[2],n) for n in ((247,248) if dynamic else BEAM_DERIVED_FRAMES)}

def validate_beam_frames(gfx,parts,frames,*,dynamic=False):
    if not BEAM_BODY_FRAMES<=frames.keys():raise ValueError('Arrival needs body, flashes and idle transition')
    if dynamic and len({frames[n][0] for n in range(249,254)})!=5:
        raise ValueError('Dynamic arrival needs five distinct colored body poses')
    base_number=249 if dynamic else 251
    derived=derive_beam_frames(gfx,parts,frames[base_number],dynamic=dynamic)
    for n,expected in derived.items():
        if frames[n]!=expected:raise ValueError(f'Arrival phase {n} differs from the Riko body')
    return {'frames':sorted(BEAM_BODY_FRAMES),'derived_from':base_number,'derived_frames':sorted(derived),
            'original_zero_silhouette_reused':False,'pure_beam_effects_edited':False}

def foot_contacts(frame,bounds):
    """Measure the two boot contacts, excluding cape width from registration."""
    pixels,(width,height)=frame
    occupied=[i for i,v in enumerate(pixels) if v]
    if not occupied or len(pixels)!=width*height:raise ValueError('Invalid stance image')
    floor=max(i//width for i in occupied)
    columns=sorted({i%width for i in occupied if i//width>=floor-2})
    groups=[]
    for x in columns:
        if not groups or x>groups[-1][-1]+1:groups.append([])
        groups[-1].append(x)
    if len(groups)!=2:raise ValueError('Stance requires two distinct boot contacts')
    contacts=[(g[0]+g[-1])/2+bounds[0] for g in groups]
    return {'foot_x':contacts,'center_x':sum(contacts)/2,'floor_y':floor+bounds[1]}

def validate_contacts(frames,bounds,reference,reference_bounds):
    target=foot_contacts(reference,reference_bounds);reports={}
    for n,frame in frames.items():
        actual=foot_contacts(frame,bounds[n]);error=actual['center_x']-target['center_x']
        if abs(error)>.5:raise ValueError(f'Arrival {n}: foot center slides away from idle')
        if actual['floor_y']!=target['floor_y']:raise ValueError(f'Arrival {n}: foot baseline differs from idle')
        reports[str(n)]={**actual,'center_error':error}
    return {'idle':target,'frames':reports,'tolerance_native_pixels':.5,
            'foot_span_forced_equal':False,'full_anatomical_quality_automatically_proven':False}
