"""다리 중심선을 따라 정합하여 수평 종아리/신발 재질 혼합을 피한다."""
from pathlib import Path
import sys,json,heapq
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES
from preview_restore import Archive,sha,write,need,helper
from register_fourth_geometry_v2 import components,center
from register_fourth_geometry_v3 import assign
from scipy.ndimage import binary_dilation,distance_transform_edt
from PIL import Image
import numpy as np
D=Path(__file__).parent
NEIGHBORS=((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1))
def centerline(mask,foot):
    y,x=np.nonzero(mask);top=int(y.min());candidates=np.where(y==top)[0];rootx=round(float(x[candidates].mean()));k=min(candidates,key=lambda k:abs(x[k]-rootx));root=(int(x[k]),int(y[k]))
    fc=center(foot);near=(x-fc[0])**2+(y-fc[1])**2<64
    k=int(np.argmax(np.where(near,np.sqrt((x-root[0])**2+(y-root[1])**2)-.6*np.sqrt((x-fc[0])**2+(y-fc[1])**2),-1e5)));tip=(int(x[k]),int(y[k]))
    clearance=distance_transform_edt(mask);cost={root:0};previous={};heap=[(0,*root)]
    while heap:
        value,cx,cy=heapq.heappop(heap)
        if value!=cost[cx,cy]:continue
        if(cx,cy)==tip:break
        for dy,dx in NEIGHBORS:
            nx,ny=cx+dx,cy+dy
            if not(0<=nx<384 and 0<=ny<384 and mask[ny,nx]):continue
            v=value+(1.414 if dx and dy else 1)*(1+3/max(clearance[ny,nx],.7))
            if v<cost.get((nx,ny),1e9):cost[nx,ny]=v;previous[nx,ny]=(cx,cy);heapq.heappush(heap,(v,nx,ny))
    need(tip in cost,'Disconnected leg centerline');points=[tip]
    while points[-1]!=root:points.append(previous[points[-1]])
    points=np.array(points[::-1],float)
    need(len(points)>=3,'Short limb path')
    smooth=points.copy()
    for k in range(1,len(points)-1):smooth[k]=points[k-1:k+2].mean(0)
    return smooth
def uv(mask,path):
    y,x=np.nonzero(mask);pixels=np.stack((x,y),axis=1).astype(float)
    a,b=path[:-1],path[1:];vector=b-a;length=np.linalg.norm(vector,axis=1);length=np.maximum(length,.001);starts=np.r_[0,np.cumsum(length)[:-1]];total=length.sum()
    rel=pixels[:,None,:]-a[None,:,:];u=np.clip((rel*vector).sum(2)/(length**2),0,1);near=a[None,:,:]+u[:,:,None]*vector
    distance=((pixels[:,None,:]-near)**2).sum(2);seg=distance.argmin(1);i=np.arange(len(x));offset=pixels-near[i,seg]
    along=(starts[seg]+u[i,seg]*length[seg])/total
    lateral=(vector[seg,0]*offset[:,1]-vector[seg,1]*offset[:,0])/length[seg]
    normal=np.empty_like(lateral)
    for i,t in enumerate(along):
        local=np.abs(along-t)<=max(.06,1.1/total);lo,hi=lateral[local].min(),lateral[local].max();normal[i]=(lateral[i]-lo)/max(hi-lo,.001)
    return x,y,along,normal,total
def retarget(source,base,eye):
    ex,ey=eye;yy,xx=np.indices(base.shape);wy=yy-160;start=ey+19
    hem_seed=np.isin(source,(13,15))&(wy>=ey+14)&(wy<=ey+24);hem=binary_dilation(hem_seed,iterations=1)&(source>0)
    sm=(source>0)&(wy>=start)&~hem&~np.isin(source,(7,8,9));bm=(base>0)&(wy>=start)&~np.isin(base,(7,8,9))
    feet=sorted(components(np.isin(source,(5,6))&(wy>=start)),key=lambda m:int(m.sum()),reverse=True)[:2];need(len(feet)==2,'Source feet count');feet=sorted(feet,key=lambda q:center(q)[0])
    srcs=assign(sm,feet);dsts=assign(bm,feet);target=source.copy();target[(wy>=start)&~hem]=0;links=[];limbs=[]
    for limb,(src,dst,foot)in enumerate(zip(srcs,dsts,feet)):
        # Small disconnected outline islands are excluded from the source UV;
        # target all pixels remain assigned. No unrelated-material fallback.
        cs=components(src);src=max(cs,key=lambda m:int(np.count_nonzero(m&foot))*1000+int(m.sum()))
        cs=components(dst);dstmain=max(cs,key=lambda m:int(m.sum()))
        sp,dp=centerline(src,foot),centerline(dstmain,foot)
        sx,sy,st,sq,sl=uv(src,sp);dx,dy,dt,dq,dl=uv(dst,dp)
        for x,y,t,q in zip(dx,dy,dt,dq):
            if hem[y,x]:continue
            score=((st-t)*max(sl,dl))**2+((sq-q)*2.2)**2;k=int(score.argmin());value=int(source[sy[k],sx[k]])
            target[y,x]=value;links.append([int(x),int(y),int(sx[k]),int(sy[k]),value,limb])
        limbs.append({'source_centerline':sp.tolist(),'target_centerline':dp.tolist(),'source_length':sl,'target_length':dl})
    return target,links,limbs
def main():
    out=D/'fourth_geometry_v4';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));report=[]
    for page,(_,refs)in enumerate(PAGES,1):
        rows=[]
        for n in refs:
            p=next(q for q in plan['frames']if q['ref']==n);src=np.array(Image.open(D/'fourth_registered_v1'/f'run_{n:03}.png'));base=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'))
            target,links,limbs=retarget(src,base,p['eye_world_original_registration']);mixed=np.where(target,target,base);Image.fromarray(target).save(out/f'run_{n:03}.png')
            rows.append((f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 원화 등록',a.rgba(src,16)),('중심선 정합 검토',a.rgba(mixed,16))]));report.append({'ref':n,'source_native_sha256':sha(src.tobytes()),'target_sha256':sha(target.tobytes()),'source_links':links,'limbs':limbs})
        helper.grid(rows,out/f'comparison_{page}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'method':'다리별 중심선 길이/측면 UV 대응. 모든 색은 같은 다리 새 원화좌표에서 샘플. 미술 검토본.','frames':report});print(json.dumps({'refs':len(report)}))
if __name__=='__main__':main()
