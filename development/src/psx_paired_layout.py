"""공유 몸통과 일반/사격 팔을 기존 타일 수 안에서 조립한다."""
import numpy as np
from src.psx_tile_layout import pack_rectangles


def pack_variant_pair(raw,tile_count,run,shot,common_rects,run_rects,shot_rects,writable):
    """동일한 픽셀만 공유하고, 두 자세의 독립 조각은 서로 다른 사각형을 허용한다."""
    run=np.asarray(run);shot=np.asarray(shot)
    if run.ndim!=2 or run.shape!=shot.shape or min(run.shape)<16 or max(run.shape)>256 or any(a.dtype!=np.uint8 or a.max()>15 for a in (run,shot)):raise ValueError('Invalid variant pair')
    height,width=run.shape
    mask=np.zeros(run.shape,bool)
    for x,y in common_rects+run_rects+shot_rects:
        if x<0 or y<0 or x+16>width or y+16>height:raise ValueError('Variant rectangle outside canvas')
    for x,y in common_rects:mask[y:y+16,x:x+16]=True
    common=np.where(mask&(run==shot),run,0).astype(np.uint8)
    r=run.copy();s=shot.copy();r[common!=0]=0;s[common!=0]=0
    groups=[(common,common_rects),(r,run_rects),(s,shot_rects)]
    slots=[]
    for canvas,rects in groups:
        remaining=canvas.copy()
        for x,y in rects:
            tile=np.zeros_like(canvas);tile[y:y+16,x:x+16]=remaining[y:y+16,x:x+16];remaining[y:y+16,x:x+16]=0
            slots.append((tile,(x,y)))
        if np.any(remaining):raise ValueError('Uncovered variant pixels')
    if len(slots)>len(writable):raise ValueError('Not enough variant tiles')
    safe=sorted(t for t in writable if t%16!=0);edge=sorted(t for t in writable if t%16==0)
    ids=[None]*len(slots)
    if len(slots)>len(safe):
        if len(edge)!=1:raise ValueError('Unsupported multiple page edges')
        candidate=next((i for i,(canvas,(x,y)) in enumerate(slots) if not np.any(canvas[y:y+16,x])),None)
        if candidate is None:raise ValueError('No transparent page-edge column')
        ids[candidate]=edge[0]
    for i in range(len(ids)):
        if ids[i] is None:ids[i]=safe.pop(0)
    result=pack_rectangles(raw,tile_count,bytes(width*height),(width,height),[],[],writable)
    for (canvas,rect),t in zip(slots,ids):result=pack_rectangles(result,tile_count,canvas.tobytes(),(width,height),[rect],[t],{t})
    records=[(t,*rect) for (_,rect),t in zip(slots,ids)];c=len(common_rects);rlen=len(run_rects)
    blank=next((t for t in sorted(writable) if t not in ids),None)
    return result,records[:c]+records[c:c+rlen],records[:c]+records[c+rlen:],blank,shot.copy()


def pack_joint_pair(raw,tile_count,run,shot,common_rects,unique_rects,writable):
    """공통 그림 5조각과 각 자세의 독립 조각 2개처럼, 서로 다른 팔 분할을 지원한다."""
    run=np.asarray(run);shot=np.asarray(shot)
    if any(a.shape!=(80,96) or a.dtype!=np.uint8 or a.max()>15 for a in (run,shot)):
        raise ValueError('Invalid joint pair raster')
    common=run.copy()
    for x,y in unique_rects:common[y:y+16,x:x+16]=0
    outside=np.ones(run.shape,bool)
    for x,y in unique_rects:outside[y:y+16,x:x+16]=False
    if np.any(run[outside]!=shot[outside]):raise ValueError('Variants differ outside unique rectangles')
    safe=sorted(t for t in writable if t%16!=0);edge=sorted(t for t in writable if t%16==0)
    c=len(common_rects);k=len(unique_rects)
    if len(edge)!=1 or len(safe)<c+2*k-1:raise ValueError('Insufficient joint pair tiles')
    common_ids=safe[:c];run_ids=[edge[0]]+safe[c:c+k-1];shot_ids=safe[c+k-1:c+2*k-1]
    result=pack_rectangles(raw,tile_count,common.tobytes(),(96,80),common_rects,common_ids,writable)
    rp=[(t,*r) for t,r in zip(common_ids,common_rects)];sp=list(rp)
    for pic,ids,records in ((run,run_ids,rp),(shot,shot_ids,sp)):
        unique=pic.copy();unique[outside]=0
        result=pack_rectangles(result,tile_count,unique.tobytes(),(96,80),unique_rects,ids,set(ids))
        records.extend((t,*r) for t,r in zip(ids,unique_rects))
    blank=next((t for t in sorted(writable) if t not in common_ids+run_ids+shot_ids),None)
    return result,rp,sp,blank,shot.copy()


def pack_pair(raw,tile_count,run,common,shot_body,gun,common_rects,arm_rect,gun_rect,writable,share_identical=False):
    arrays=[np.asarray(a) for a in (run,common,shot_body,gun)]
    if any(a.shape!=(80,96) for a in arrays):raise ValueError('Pair requires 96x80 indexed canvases')
    if any(a.dtype!=np.uint8 or a.max()>15 for a in arrays):raise ValueError('Invalid indexed pair')
    run,common,shot_body,gun=[a.copy() for a in arrays]
    c=len(common_rects);safe=sorted(t for t in writable if t%16!=0)
    if len(safe)<c+2:raise ValueError('Insufficient safe body/arm tiles')
    common_ids=safe[:c];run_id,shot_id=safe[c:c+2]
    remaining=sorted(set(writable)-set(common_ids)-{run_id,shot_id})
    if not remaining:raise ValueError('No cannon tile')
    gun_id=remaining[0];blank=remaining[1] if len(remaining)>1 else None
    ax,ay=arm_rect;arm=np.zeros_like(run);arm[ay:ay+16,ax:ax+16]=run[ay:ay+16,ax:ax+16]
    if np.any(common[ay:ay+16,ax:ax+16]):raise ValueError('Shared body must leave the arm window clear')
    restored=common.copy();restored[arm!=0]=arm[arm!=0]
    if not np.array_equal(restored,run):raise ValueError('Run body/arm reconstruction failed')
    # Identical pixels inside overlapping shared rectangles need only one owner.
    # This changes storage, while preserving both complete displayed targets.
    covered=np.zeros_like(run,dtype=bool)
    for x,y in common_rects:covered[y:y+16,x:x+16]=True
    shared=covered&(arm!=0)&(arm==shot_body)&share_identical
    common[shared]=arm[shared];arm[shared]=0;shot_body[shared]=0
    result=pack_rectangles(raw,tile_count,common.tobytes(),(96,80),common_rects,common_ids,writable)
    for canvas,rect,tile in ((arm,arm_rect,run_id),(shot_body,arm_rect,shot_id),(gun,gun_rect,gun_id)):
        result=pack_rectangles(result,tile_count,canvas.tobytes(),(96,80),[rect],[tile],{tile})
    common_parts=[(tile,*r) for tile,r in zip(common_ids,common_rects)]
    run_parts=common_parts+[(run_id,*arm_rect)]
    shot_parts=common_parts+[(shot_id,*arm_rect),(gun_id,*gun_rect)]
    target=common.copy();target[shot_body!=0]=shot_body[shot_body!=0];target[gun!=0]=gun[gun!=0]
    return result,run_parts,shot_parts,blank,target
