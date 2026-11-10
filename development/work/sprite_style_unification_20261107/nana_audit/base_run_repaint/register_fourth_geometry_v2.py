"""포스 피부/신발을 서로 다른 출처 영역으로 등록하는 미술 검토본."""
from pathlib import Path
import sys,json,heapq
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES
from preview_restore import Archive,sha,write,need,helper
from PIL import Image
from scipy.ndimage import label,binary_dilation
import numpy as np
D=Path(__file__).parent
def spans(mask):
    xs=np.flatnonzero(mask);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def components(mask):
    ls,count=label(mask,np.ones((3,3)))
    return [(ls==k)for k in range(1,count+1)]
def center(mask):
    y,x=np.nonzero(mask);return np.array([x.mean(),y.mean()])
def bounded_distance(mask,point,budget=5):
    sx,sy=point;dist={(sy,sx):0};heap=[(0,sy,sx)]
    while heap:
        score,y,x=heapq.heappop(heap)
        if score!=dist[y,x]:continue
        for dy,dx in((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            ny,nx=y+dy,x+dx;value=score+(1.414 if dx and dy else 1)
            if value<=budget and 0<=ny<384 and 0<=nx<384 and mask[ny,nx] and value<dist.get((ny,nx),1000):dist[ny,nx]=value;heapq.heappush(heap,(value,ny,nx))
    out=np.zeros_like(mask)
    for y,x in dist:out[y,x]=True
    return out
def retarget(source,base,eye):
    ex,ey=eye;yy,xx=np.indices(base.shape);wx,wy=xx-160,yy-160;start=ey+19
    lower=(wy>=start)&(base>0)&~np.isin(base,(7,8,9))
    hem_seed=np.isin(source,(13,15))&(wy>=ey+14)&(wy<=ey+24)
    hem=binary_dilation(hem_seed,iterations=1)&(source>0)
    skinseed=np.isin(source,(10,11,12,13))&(wy>=start-2)&~hem
    skin=binary_dilation(skinseed,iterations=1)&(source>0)&np.isin(source,(1,2,10,11,12,13))
    dest=source.copy();dest[(wy>=start)&~hem]=0;links=[]
    srcfeet=components(np.isin(source,(5,6))&(wy>=start))
    dstmarkers=components(np.isin(base,(5,6))&(wy>=start))
    # Ignore tiny red cloth flecks by pairing each marker with a local foot tip.
    srcfeet=sorted(srcfeet,key=lambda q:int(q.sum()),reverse=True)[:2]
    need(len(srcfeet)==2,'Two authored shoes required')
    srcfeet=sorted(srcfeet,key=lambda q:center(q)[0])
    shoemasks=[];shoeproof=[]
    for foot in srcfeet:
        mid=center(foot);area=lower&((xx-mid[0])**2+(yy-mid[1])**2<=7**2)
        py,px=np.nonzero(area);score=np.sqrt((px-(160+ex+6))**2+(py-(160+ey+18))**2)-.6*np.sqrt((px-mid[0])**2+(py-mid[1])**2)
        sourcearea=binary_dilation(foot,iterations=1)&(source>0)&~np.isin(source,(10,11,12,13,15))
        sy,sx=np.nonzero(sourcearea);sb=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)]
        k=int(score.argmax());tip=(int(px[k]),int(py[k]))
        if sb[2]-sb[0]>=sb[3]-sb[1]:shoe=area&(yy>=int(py.max())-3)
        elif mid[0]>=160+ex+6:shoe=area&(xx>=int(px.max())-3)
        else:shoe=area&(xx<=int(px.min())+3)
        shoemasks.append(shoe);dy,dx=np.nonzero(shoe)
        db=[int(dx.min()),int(dy.min()),int(dx.max()+1),int(dy.max()+1)]
        # Entire shoe raster, including sole, is sampled in two dimensions.
        # No leg scanline can ever sample this region.
        for y,x in zip(dy,dx):
            u=min(sb[2]-1,sb[0]+int((x-db[0]+.5)*(sb[2]-sb[0])/(db[2]-db[0])))
            v=min(sb[3]-1,sb[1]+int((y-db[1]+.5)*(sb[3]-sb[1])/(db[3]-db[1])))
            if not sourcearea[v,u]:
                k=int(((sx-u)**2+(sy-v)**2).argmin());u,v=int(sx[k]),int(sy[k])
            dest[y,x]=source[v,u];links.append([int(x),int(y),u,v,int(source[v,u]),'shoe'])
        shoeproof.append({'target_tip':tip,'source_box':sb,'target_box':db,'source_palette':sorted(map(int,np.unique(source[sourcearea]))),'target_palette':sorted(map(int,np.unique(dest[shoe])))})
    shoeunion=np.logical_or.reduce(shoemasks)
    for y in range(160+start,384):
        ds=spans(lower[y]&~shoeunion[y]&~hem[y])
        if not ds:continue
        for dr in ds:
            options=[]
            for sy in range(max(160+start-3,y-7),min(384,y+8)):
                for sr in spans(skin[sy]):
                    if not np.any(np.isin(source[sy,sr],(10,11,12,13))):continue
                    cost=abs(sy-y)*1.5+abs(float(dr.mean()-sr.mean()))*.4
                    options.append((cost,sy,sr))
            need(options,'Authored skin missing')
            _,sy,sr=min(options,key=lambda q:q[0])
            for j,x in enumerate(dr):
                sx=int(sr[round(j*(len(sr)-1)/max(1,len(dr)-1))]);dest[y,x]=source[sy,sx]
                links.append([int(x),int(y),sx,sy,int(source[sy,sx]),'skin'])
    return dest,(base>0)&(dest==0),links,shoeproof
def main():
    out=D/'fourth_geometry_v2';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));report=[]
    for page,(_,refs)in enumerate(PAGES,1):
        rows=[]
        for n in refs:
            p=next(q for q in plan['frames']if q['ref']==n);src=np.array(Image.open(D/'fourth_registered_v1'/f'run_{n:03}.png'));base=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'))
            target,miss,links,shoes=retarget(src,base,p['eye_world_original_registration']);mixed=np.where(target,target,base)
            Image.fromarray(target).save(out/f'run_{n:03}.png')
            rows.append((f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 원화 등록',a.rgba(src,16)),('피부/신발 출처 분리',a.rgba(mixed,16))]))
            report.append({'ref':n,'source_native_sha256':sha(src.tobytes()),'target_sha256':sha(target.tobytes()),'source_links':links,'shoes':shoes,'remaining_base_pixels':int(miss.sum())})
        helper.grid(rows,out/f'comparison_{page}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'method':'신발2D·피부행별 국소 원화 좌표 대응. 재질 영역이 교차하지 않으며 새 원화 색인/좌표를 기록. 미술 검토 전 적용하지 않음.','frames':report})
    print(json.dumps({'refs':len(report)}))
if __name__=='__main__':main()
