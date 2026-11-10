"""불투명 화소를 보존하며 기존 16x16 창의 표시 좌표만 찾는다."""
import functools
import numpy as np

def _milp_cover(a, edge, normal, left, top):
    """Optional exact set-cover solver; source pixels never enter the optimizer."""
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import coo_matrix
    except ImportError:
        return None
    yy,xx=np.nonzero(a);h,w=a.shape;n=len(xx);candidates=[]
    for kind in (0,1) if edge else (0,):
        unique={}
        for y in range(min(0,h-16),max(0,h-16)+1):
            for x in range(-1 if kind else min(0,w-16),max(0,w-16)+1):
                if kind and 0<=x<w and a[max(0,y):y+16,x].any():continue
                ids=np.flatnonzero((yy>=y)&(yy<y+16)&(xx>=x+kind)&(xx<x+16))
                if not len(ids):continue
                key=ids.tobytes()
                if key not in unique:unique[key]=(kind,x,y,ids)
        candidates.extend(unique.values())
    if not candidates:return None
    rows=[];cols=[]
    for j,(kind,x,y,ids) in enumerate(candidates):
        rows.extend(ids.tolist()+[n+kind]);cols.extend([j]*(len(ids)+1))
    matrix=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n+1+bool(edge),len(candidates))).tocsc()
    lower=np.r_[np.ones(n),0,([0] if edge else [])]
    upper=np.r_[np.full(n,np.inf),len(normal),([len(edge)] if edge else [])]
    result=milp(np.ones(len(candidates)),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=LinearConstraint(matrix,lower,upper),options={'time_limit':20,'mip_rel_gap':0.01})
    if result.x is None:return None
    selected=[q for q,v in zip(candidates,result.x) if v>.5]
    covered=np.zeros(n,bool)
    for q in selected:covered[q[3]]=True
    if not covered.all():return None
    locations={k:[(x,y) for kind,x,y,ids in selected if kind==k] for k in (0,1)}
    if len(locations[0])>len(normal) or len(locations[1])>len(edge):return None
    out=[]
    for kind,ps in ((0,normal),(1,edge)):
        positions=locations[kind]
        while len(positions)<len(ps):positions.append((w+1,0))
        for p,(x,y) in zip(ps,positions):
            if not -128<=x+left<=127 or not -128<=y+top<=127:return None
            out.append((p,x+left,y+top))
    return out

def fit_windows(parts, pixels, left, top, node_limit=60000):
    a=np.asarray(pixels)>0;h,w=a.shape
    if not a.any() or len({p['tile'] for p in parts})!=len(parts):return None
    edge=[p for p in parts if p['tile']%16==0];normal=[p for p in parts if p['tile']%16]
    if edge and any(p['flip_x'] for p in edge):
        if not all(p['flip_x'] for p in edge):return None
        mirrored=[dict(p,flip_x=False) if p['tile']%16==0 else p for p in parts]
        result=fit_windows(mirrored,a[:,::-1],0,0,node_limit)
        if result is None:return None
        original={p['tile']:p for p in parts}
        mapped=[(original[p['tile']],left+w-x-16,top+y) for p,x,y in result]
        return mapped if all(-128<=x<=127 and -128<=y<=127 for p,x,y in mapped) else None
    exact=_milp_cover(a,edge,normal,left,top)
    if exact is not None:return exact
    if len(edge)>1:return None
    coords=list(zip(*np.nonzero(a)));point_bits={(int(y),int(x)):1<<i for i,(y,x) in enumerate(coords)};full=(1<<len(coords))-1
    @functools.lru_cache(None)
    def rectangle(x,y,width):
        bits=0
        for yy in range(max(0,y),min(h,y+16)):
            for xx in range(max(0,x),min(w,x+width)):
                bits|=point_bits.get((yy,xx),0)
        return bits
    seen=set();nodes=0
    def solve(rem,count):
        nonlocal nodes
        nodes+=1
        if not rem:return []
        if count==0 or rem.bit_count()>count*256 or nodes>node_limit:return None
        key=(rem,count)
        if key in seen:return None
        seen.add(key);i=(rem&-rem).bit_length()-1;yy,xx=map(int,coords[i]);choices={}
        for y in range(yy-15,yy+1):
            for x in range(xx-15,xx+1):
                mask=rectangle(x,y,16)&rem
                if mask not in choices:choices[mask]=(x,y)
        ranked=sorted(choices.items(),key=lambda q:q[0].bit_count(),reverse=True)
        for mask,(x,y) in ranked[:32]:
            ans=solve(rem^mask,count-1)
            if ans is not None:return [(x,y),*ans]
        return None
    edge_options=[(0,None)]
    if edge:
        edge_options=[]
        for y in range(-15,h):
            for x in range(-1,w):
                # U0's first column must be transparent in the complete pose.
                if any(a[yy,x] for yy in range(max(0,y),min(h,y+16)) if 0<=x<w):continue
                bits=rectangle(x+1,y,15)
                if bits:edge_options.append((bits,(x,y)))
        edge_options=sorted(edge_options,key=lambda q:q[0].bit_count(),reverse=True)[:48]
    for mask,edge_xy in edge_options:
        result=solve(full^mask,len(normal))
        if result is None:continue
        occupied=result+([edge_xy] if edge_xy else []);empty=max(x+16 for x,y in occupied)+1
        while len(result)<len(normal):result.append((empty,16*(len(result)-len(occupied))))
        assignments=list(zip(normal,result))
        if edge:assignments.append((edge[0],edge_xy))
        out=[]
        for p,(x,y) in assignments:
            x+=left;y+=top
            if not -128<=x<=127 or not -128<=y<=127:return None
            out.append((p,x,y))
        return out
    return None
