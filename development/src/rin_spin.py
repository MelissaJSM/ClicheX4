"""린 회전 베기의 같은 중심·동일 배율 회전과 기존 연결 자세를 검사한다."""
import numpy as np
from PIL import Image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_air_spin import BODY,ROTATING


def world_frame(frame,bounds):
    data,(w,h)=frame
    if len(data)!=w*h or bounds[2]-bounds[0]!=w or bounds[3]-bounds[1]!=h:raise ValueError('Spin frame dimensions differ')
    if min(bounds)<-96 or max(bounds)>96:raise ValueError('Spin frame outside audit canvas')
    out=np.zeros((192,192),np.uint8);out[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]]=np.frombuffer(data,np.uint8).reshape(h,w)
    return out


def validate_rotation(frames,bounds):
    if not set(ROTATING)<=frames.keys():raise ValueError('Eight spin phases required')
    base=world_frame(frames[161],bounds[161]);area=int(np.count_nonzero(base));result={}
    for i,n in enumerate(ROTATING):
        expected=np.array(Image.fromarray(base).rotate(i*45,Image.Resampling.NEAREST,center=(96,96)));actual=world_frame(frames[n],bounds[n])
        if not np.array_equal(expected,actual):raise ValueError(f'Spin {n} changed scale, rotation center or pixels')
        result[str(n)]={'degrees':i*45,'opaque_pixels':int(np.count_nonzero(actual)),'ratio_to_base':int(np.count_nonzero(actual))/area}
    return result


def validate_spin(gfx,parts,frames):
    if set(frames)!=BODY:raise ValueError('Complete spin body required')
    def native(n,bi,pi):
        f=graphics_bank(gfx,bi)['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        return compose_indices(raw,f['tile_count'],composition_frame(parts,pi,n))
    bounds={n:native(n,1,5)[2] for n in frames};rotations=validate_rotation(frames,bounds)
    for n,source in ((132,229),(160,213)):
        data,size,b,_=native(source,0,0)
        if not np.array_equal(world_frame(frames[n],bounds[n]),world_frame((data,size),b)):raise ValueError('Spin lead or recovery differs from existing air pose')
    reference=sum(bool(v) for v in native(21,0,0)[0]);area=sum(bool(v) for v in frames[161][0]);ratio=area/reference
    if not .85<=ratio<=1.15:raise ValueError('Spin body mass differs too much from current jump')
    return {'rotation_pivot':[0,0],'rotation_scale':1,'frames':rotations,'base_to_jump_area_ratio':ratio,'anatomical_quality_automatically_proven':False,'lead_recovery_world_pixels_preserved':True}
