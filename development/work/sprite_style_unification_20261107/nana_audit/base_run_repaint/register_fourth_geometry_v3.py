"""두 다리를 분리하고 발끝까지 각 원화 좌표계를 유지한 국소 정합."""
from pathlib import Path
import sys,json,heapq
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES
from preview_restore import Archive,sha,write,need,helper
from register_fourth_geometry_v2 import components,center
from scipy.ndimage import binary_dilation
from PIL import Image
import numpy as np
D=Path(__file__).parent
def assign(mask,seeds):
    ys,xs=np.nonzero(mask);dist=np.full(mask.shape,np.inf);owner=np.full(mask.shape,-1,np.int8);heap=[]
    for k,seed in enumerate(seeds):
        hits=mask&seed
        if not hits.any():
            point=center(seed);j=int(((xs-point[0])**2+(ys-point[1])**2).argmin());hits=np.zeros_like(mask);hits[ys[j],xs[j]]=True
        y,x=np.nonzero(hits)
        for y,x in zip(y,x):dist[y,x]=0;owner[y,x]=k;heapq.heappush(heap,(0,int(y),int(x),k))
    while heap:
        score,y,x,k=heapq.heappop(heap)
        if score!=dist[y,x]:continue
        for dy,dx in((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            ny,nx=y+dy,x+dx;v=score+(1.414 if dx and dy else 1)
            if 0<=ny<384 and 0<=nx<384 and mask[ny,nx] and v<dist[ny,nx]:dist[ny,nx]=v;owner[ny,nx]=k;heapq.heappush(heap,(v,ny,nx,k))
    for y,x in np.argwhere(mask&(owner<0)):
        owner[y,x]=int(np.argmin([np.sum((np.array([x,y])-center(seed))**2)for seed in seeds]))
    return [mask&(owner==k)for k in range(len(seeds))]
def retarget(source,base,eye):
    ex,ey=eye;yy,xx=np.indices(base.shape);wy=yy-160;start=ey+19
    hem_seed=np.isin(source,(13,15))&(wy>=ey+14)&(wy<=ey+24)
    hem=binary_dilation(hem_seed,iterations=1)&(source>0)
    sm=(source>0)&(wy>=start)&~hem&~np.isin(source,(7,8,9))
    bm=(base>0)&(wy>=start)&~np.isin(base,(7,8,9))
    feet=sorted(components(np.isin(source,(5,6))&(wy>=start)),key=lambda m:int(m.sum()),reverse=True)[:2]
    need(len(feet)==2,'Source feet count');feet=sorted(feet,key=lambda q:center(q)[0])
    srcs=assign(sm,feet);dsts=assign(bm,feet)
    target=source.copy();target[(wy>=start)&~hem]=0;links=[];limbs=[]
    for limb,(src,dst)in enumerate(zip(srcs,dsts)):
        sy,sx=np.nonzero(src);dy,dx=np.nonzero(dst);s0,s1=int(sy.min()),int(sy.max());d0,d1=int(dy.min()),int(dy.max())
        valid_rows=np.unique(sy)
        for y in range(d0,d1+1):
            dr=np.flatnonzero(dst[y]);
            if not len(dr):continue
            source_y=round(s0+(y-d0)*(s1-s0)/max(1,d1-d0));source_y=int(valid_rows[np.abs(valid_rows-source_y).argmin()])
            sr=np.flatnonzero(src[source_y]);need(len(sr)>0,'Mapped row empty')
            for k,x in enumerate(dr):
                source_x=int(sr[round(k*(len(sr)-1)/max(1,len(dr)-1))])
                if hem[y,x]:continue
                value=int(source[source_y,source_x]);target[y,x]=value;links.append([int(x),y,source_x,source_y,value,limb])
        limbs.append({'source_bbox':[int(sx.min()),s0,int(sx.max()+1),s1+1],'target_bbox':[int(dx.min()),d0,int(dx.max()+1),d1+1],'source_sole_row':s1,'target_sole_row':d1})
    return target,links,limbs
def main():
    out=D/'fourth_geometry_v3';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));report=[]
    for page,(_,refs)in enumerate(PAGES,1):
        rows=[]
        for n in refs:
            p=next(q for q in plan['frames']if q['ref']==n);src=np.array(Image.open(D/'fourth_registered_v1'/f'run_{n:03}.png'));base=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'))
            target,links,limbs=retarget(src,base,p['eye_world_original_registration']);mixed=np.where(target,target,base)
            Image.fromarray(target).save(out/f'run_{n:03}.png')
            rows.append((f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 원화 등록',a.rgba(src,16)),('독립 다리 좌표계',a.rgba(mixed,16))]))
            report.append({'ref':n,'source_native_sha256':sha(src.tobytes()),'target_sha256':sha(target.tobytes()),'source_links':links,'limbs':limbs,'remaining_base_pixels':int(((base>0)&(target==0)).sum())})
        helper.grid(rows,out/f'comparison_{page}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'method':'각 다리를 발에서 geodesic 분리, 그 다리 원화의 전 길이(밑창 포함)를 목표 다리에 대응. 다른 발/의상 색 참조 금지. 미술검토본.','frames':report})
    print(json.dumps({'refs':len(report)}))
if __name__=='__main__':main()
