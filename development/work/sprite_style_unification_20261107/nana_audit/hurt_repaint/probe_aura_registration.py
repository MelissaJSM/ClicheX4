"""기수용 오라 조각의 강체 이동만으로 새 몸 외곽 여유를 비교한다."""
from pathlib import Path
import sys,json,itertools
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_cdt,label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def compose(a,ls,mask):
    im=a.rgba(ls[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 else 16))
    return im
def main():
    out=D/'aura_contact_probe_v2';out.mkdir(exist_ok=False)
    a=Archive((N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC').read_bytes())
    pb=(0,5,6,7,8);ls={k:np.array(Image.open(D/'joint_layers_probe_v1'/f'layer{k}_234.png'))for k in pb}
    union=np.logical_or.reduce([z>0 for z in ls.values()]);oldunion=np.logical_or.reduce([a.layer(234,k)[0]>0 for k in pb])
    nd=distance_transform_cdt(~union,metric='taxicab');od=distance_transform_cdt(~oldunion,metric='taxicab')
    records=[];rows=[]
    for n in(235,236):
        fx=np.array(Image.open(D/'effect_probe_v1'/f'effect_{n:03}_bank0.png'))
        # 각 그룹 안의 픽셀 간 위치/색은 그대로이며 전신 몸체는 바뀌지 않는다.
        # 실제 오라의 8연결 조각을 유지한다. 임의 행 절단/픽셀 삭제가 없다.
        labs,count=label(fx>0,np.ones((3,3)))
        groups={f'component_{k}':labs==k for k in range(1,count+1)}
        candidates={}
        for name,m in groups.items():
            yy,xx=np.nonzero(m);vv=fx[yy,xx];opts=[]
            for dy,dx in (itertools.product(range(-3,4),repeat=2) if np.any(m&union) else [(0,0)]):
                ty,tx=yy+dy,xx+dx
                if np.any(union[ty,tx]):continue
                delta=nd[ty,tx]-od[yy,xx]
                # 거리가 멀어지는 것을 벌점으로 두고 가장 작은 지역 이동을 택한다.
                score=float(1000*(abs(dx)+abs(dy))+np.abs(delta).sum()+2*np.maximum(delta-1,0).sum())
                opts.append((score,abs(dx)+abs(dy),dx,dy,yy,xx,vv))
            need(opts,f'{n}/{name} 3px 이내 무겹침 배치 없음')
            candidates[name]=sorted(opts,key=lambda q:q[:4])
        best=None
        names=list(groups)
        for picks in itertools.product(*(candidates[k][:8]for k in names)):
            new=np.zeros_like(fx);valid=True
            for p in picks:
                _,_,dx,dy,yy,xx,vv=p;ty,tx=yy+dy,xx+dx
                if np.any(new[ty,tx]):valid=False;break
                new[ty,tx]=vv
            if not valid:continue
            score=sum(p[0]for p in picks)
            if best is None or score<best[0]:best=(score,picks,new)
        need(best is not None,'구간간 중첩 없는 후보 필요');score,picks,new=best
        need(np.array_equal(np.bincount(new.flat,minlength=256),np.bincount(fx.flat,minlength=256)),'색/픽셀 개수')
        need(not np.any((new>0)&union),'새몸과 오라 중첩')
        links=[];movements=[]
        for name,p in zip(names,picks):
            _,_,dx,dy,yy,xx,vv=p
            movements.append({'region':name,'translation':[dx,dy],'pixels':len(xx),'original_bounds':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-160),int(yy.max()-160)]})
            links.extend({'world':[int(x+dx-160),int(y+dy-160)],'source_world':[int(x-160),int(y-160)],'index':int(v)}for y,x,v in zip(yy,xx,vv))
        Image.fromarray(new).save(out/f'effect_{n:03}_indices.png')
        oldls={k:z.copy()for k,z in ls.items()};oldls[0]=np.where(fx,fx,ls[0]).astype(np.uint8)
        newls={k:z.copy()for k,z in ls.items()};newls[0]=np.where(new,new,ls[0]).astype(np.uint8)
        rows.append((f'aura {n}',[('original accepted',a.composite(n)[0]),('new base, old aura',compose(a,oldls,0)),('new base, local aura',compose(a,newls,0)),('new Fourth, local aura',compose(a,newls,15))]))
        records.append({'ref':n,'source_effect_sha256':sha(fx.tobytes()),'registered_effect_sha256':sha(new.tobytes()),'old_count':int(np.count_nonzero(fx)),
                        'new_count':int(np.count_nonzero(new)),'movements':movements,'source_links':links,'before_body_overlap':int(((fx>0)&union).sum()),
                        'after_body_overlap':0,'max_distance':int(nd[new>0].max()),'new_body_unchanged':True})
    helper.grid(rows,out/'comparison.png',7)
    write(out/'manifest.json',{'frames':records,'scope':'기수용 나나오라의 실제 8연결 조각 중 새몸과 겹친 조각만 최소 강체이동. 연결 조각 분할/픽셀 삭제 없이 색/픽셀수 일대일 출처 보존. 새몸·원효과/판정·타이밍 불변. 미술 후보이며 미동결.','runtime_verified':False})
    print(json.dumps([{k:q[k]for k in('ref','movements','before_body_overlap','after_body_overlap','max_distance')}for q in records]))
if __name__=='__main__':main()
