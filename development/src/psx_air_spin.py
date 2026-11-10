"""US Zero animation100: fixed native head rotations, without changing game transforms."""
BODY=frozenset((132,160,161,163,165,167,169,171,173,175))
EFFECTS=frozenset((133,162,164,166,168,170,172,174,176))
ROTATING=tuple(range(161,176,2))
SCOPE='wall_saber_and_air_spin_bank1_v1'
SIZED_SCOPE='wall_saber_and_air_spin_native_scale_v2'
JUMP_SIZED_SCOPE='wall_saber_and_air_spin_jump_scale_v3'


def head_views(reference, reference_size, roi, registration):
    import numpy as np
    from PIL import Image
    x0,y0,x1,y1=roi
    head=np.frombuffer(reference,np.uint8).reshape(reference_size[1],reference_size[0])[y0:y1,x0:x1]
    if head.shape!=(19,23):raise ValueError('Spin requires the approved 23x19 native reference')
    if set(registration)!={'base_head_world','lead_head_world','rotation_degrees','pivot_world'}:
        raise ValueError('Incomplete spin registration')
    if (registration['rotation_degrees']!=[i*45 for i in range(8)] or
            registration['pivot_world'] not in ([0,0],[0,.5],[.5,0],[.5,.5])):
        raise ValueError('Unsupported spin rotation sequence/pivot')
    if set(registration['lead_head_world'])!={'132','160'}:raise ValueError('Missing spin lead pose')
    positions=[registration['base_head_world'],*registration['lead_head_world'].values()]
    if any(len(p)!=2 or any(type(v) is not int or not -48<=v<=48 for v in p) for p in positions):
        raise ValueError('Invalid spin reference placement')
    base=np.zeros((192,192),np.uint8);x,y=registration['base_head_world'];base[96+y:115+y,96+x:119+x]=head
    views={}
    for n in sorted(BODY):
        if n in ROTATING:
            cx,cy=registration['pivot_world']
            canvas=np.array(Image.fromarray(base).rotate(ROTATING.index(n)*45,Image.Resampling.NEAREST,center=(96+cx,96+cy)))
        else:
            canvas=np.zeros_like(base);x,y=registration['lead_head_world'][str(n)];canvas[96+y:115+y,96+x:119+x]=head
        yy,xx=np.nonzero(canvas);x,y=int(xx.min()),int(yy.min());right,bottom=int(xx.max())+1,int(yy.max())+1
        patch=canvas[y:bottom,x:right];views[n]=(patch.tobytes(),(right-x,bottom-y),(x-96,y-96))
    return views


def validate_heads(frames,bounds,reference,reference_size,roi,registration):
    from src.sprite_scale import validate_fixed_reference
    if set(frames)!=BODY:raise ValueError('Incomplete spin body')
    views=head_views(reference,reference_size,roi,registration);checks={}
    for n,(pixels,size,position) in views.items():
        checks[str(n)]=validate_fixed_reference({n:frames[n]},bounds,pixels,size,(0,0,*size),{str(n):list(position)})
    return {'frames':checks,'rotation_scale':1,'head_rectangles':{str(n):[*p,*s] for n,(_,s,p) in views.items()},
            'pivot_world':registration['pivot_world'],'angle_step_degrees':45,'anatomical_quality_automatically_proven':False}


def validate_body_mass(frames,views,reference_body_pixels,ratio_bounds=(.9,1.2)):
    """Art regression heuristic, not a proof of anatomy: compare body area after excluding the head."""
    if not 0<ratio_bounds[0]<=ratio_bounds[1] or reference_body_pixels<=0:raise ValueError('Invalid body size reference')
    report={}
    for n in ROTATING:
        data,size=frames[n]
        if len(data)!=size[0]*size[1]:raise ValueError('Invalid body frame dimensions')
        area=sum(v!=0 for v in frames[n][0])-sum(v!=0 for v in views[n][0]);ratio=area/reference_body_pixels
        if not ratio_bounds[0]<=ratio<=ratio_bounds[1]:raise ValueError(f'Frame {n}: body mass shrunk or enlarged independently of head')
        report[str(n)]={'body_pixels':area,'reference_body_pixels':reference_body_pixels,'ratio':ratio}
    return {'frames':report,'ratio_bounds':list(ratio_bounds),'heuristic_only':True,'anatomical_quality_automatically_proven':False}
