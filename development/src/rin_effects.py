"""린 팔레트에 맞는 도착 섬광. 원래 시간표·순수 빛 데이터는 별도 보존한다."""
from src.psx_beam_in import materialize,derive_beam_frames,validate_contacts
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_ice import flash_from_recovery

def arrival_flash(base,bounds,size,target_bounds,phase):
    if phase not in (247,248):raise ValueError('Rin arrival flashes are 247/248 only')
    pixels,sz=materialize(base,bounds,size,target_bounds,phase)
    return bytes(11 if v==15 else 10 if v==12 else v for v in pixels),sz

def derive_arrival(gfx,parts,base):
    derived=derive_beam_frames(gfx,parts,base,dynamic=True)
    return {n:(bytes(11 if v==15 else 10 if v==12 else v for v in pixels),size) for n,(pixels,size) in derived.items()}

def validate_arrival(gfx,parts,frames,bounds,idle,idle_bounds):
    if set(frames)!=set(range(247,254)):raise ValueError('All seven arrival frames required')
    if len({frames[n][0] for n in range(249,254)})!=5:raise ValueError('Five distinct arrival body keys required')
    for n,expected in derive_arrival(gfx,parts,frames[249]).items():
        if frames[n]!=expected:raise ValueError('Arrival flash differs from Rin landing silhouette')
    contacts=validate_contacts({n:frames[n] for n in range(249,254)},bounds,idle,idle_bounds)
    return {'flash_fill_index':11,'flash_outline_index':10,'cyan_eye_index_not_used_as_white':True,'contacts':contacts}


def departure_flash(base,bounds,size,target_bounds,phase):
    pixels,(w,h)=base
    if phase not in (7,8) or len(pixels)!=w*h or any(v>15 for v in pixels):raise ValueError('Invalid Rin departure source')
    body={(i%w+bounds[0],i//w+bounds[1]):v for i,v in enumerate(pixels) if v}
    if not body:raise ValueError('Empty Rin departure source')
    image={};radius=1 if phase==7 else 2
    for x,y in body:
        for dx in range(-radius,radius+1):
            for dy in range(-radius,radius+1):
                if abs(dx)+abs(dy)<=radius:image[x+dx,y+dy]=11 if phase==7 else 10
    pale=(0,10,10,10,11,11,10,11,11,11,10,10,11,10,11,11)
    image.update({xy:v if phase==7 else pale[v] for xy,v in body.items()})
    out=bytearray(size[0]*size[1])
    for (x,y),v in image.items():
        if not target_bounds[0]<=x<target_bounds[2] or not target_bounds[1]<=y<target_bounds[3]:raise ValueError('Rin departure glow escaped canvas')
        out[(y-target_bounds[1])*size[0]+x-target_bounds[0]]=v
    return bytes(out),size


def derive_departure(gfx,parts,base):
    bank=graphics_bank(gfx,1)
    def native(n):
        f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        return compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))
    _,size,bounds,_=native(3)
    if tuple(base[1])!=size:raise ValueError('Rin departure body dimensions differ')
    return {n:departure_flash(base,bounds,native(n)[1],native(n)[2],n) for n in (7,8)}


def validate_departure(gfx,parts,frames):
    if set(frames)!=set(range(9)):raise ValueError('Rin victory needs seven keys and two flashes')
    for n,expected in derive_departure(gfx,parts,frames[3]).items():
        if frames[n]!=expected:raise ValueError('Rin departure flash differs from new body')
    return {'body_frames':list(range(9)),'flash_source':3,'flash7_retains_cyan_eye':True,'flash_outline_indices':[11,10],'pure_effects_preserved':list(range(9,14))}


def ice_flash(frame):
    pixels,size=flash_from_recovery(*frame)
    return bytes(11 if v==15 else 10 if v==12 else v for v in pixels),size


def validate_ice_flash(gfx,parts,frames):
    from src.rin_spin import world_frame
    bank=graphics_bank(gfx,1);worlds={}
    for n in (87,88):
        f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;b=compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))[2];worlds[n]=world_frame(frames[n],b)
    expected,_=ice_flash((worlds[87].tobytes(),(192,192)))
    if expected!=worlds[88].tobytes():raise ValueError('Rin ice flash differs from recovery body')
    return {'source':87,'flash':88,'fill_index':10,'outline_index':11,'world_silhouette_equal':True}
