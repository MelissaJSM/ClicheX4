"""국소 하체 좌표 대응 검토용. 새 원화 실제 색인만 옮기며 최종 적용하지 않는다."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES
from preview_restore import Archive,sha,digest,write,need,helper
from PIL import Image
from scipy.ndimage import label,binary_dilation,distance_transform_edt
import numpy as np
D=Path(__file__).parent
def spans(mask):
    xs=np.flatnonzero(mask)
    return [] if len(xs)==0 else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def retarget(source,base,eye):
    ex,ey=eye;yy,xx=np.indices(base.shape);wx=xx-160;wy=yy-160
    start=ey+19
    lower=(wy>=start)&(base>0)
    # Connected lower limbs only; rear pink strands are never stocking texture.
    lower&=~np.isin(base,(7,8,9))
    # Source skin and shoe islands plus their drawn one-pixel edge. Never use
    # a distant generic palette value or sample a veil as a leg material.
    seeds=(wy>=start-2)&np.isin(source,(10,11,12,13,5,6))
    seedparts,_=label(seeds,np.ones((3,3)))
    candidate=binary_dilation(seeds,iterations=1)&(source>0)&(wy>=start-2)
    candidate&=~np.isin(source,(7,8,9,15))
    hem_seed=np.isin(source,(13,15))&(wy>=ey+14)&(wy<=ey+24)
    hem=binary_dilation(hem_seed,iterations=1)&(source>0)
    dest=source.copy();dest[(wy>=start)&~hem]=0;links=[]
    for y in range(160+start,384):
        ds=spans(lower[y])
        if not ds:continue
        possible=[]
        for sy in range(max(160+start-2,y-3),min(384,y+4)):
            ss=spans(candidate[sy]);ss=[s for s in ss if len(s)>=2]
            if not ss:continue
            cost=abs(sy-y)*2+abs(len(ds)-len(ss))*5+sum(min(abs(float(d.mean()-s.mean()))for s in ss)for d in ds)*.25
            possible.append((cost,sy,ss))
        need(possible,f'No authored lower limb on row {y}')
        _,sy,ss=min(possible,key=lambda z:z[0])
        for i,dr in enumerate(ds):
            sr=ss[i] if len(ds)==len(ss) else min(ss,key=lambda s:abs(float(s.mean()-dr.mean())))
            for j,x in enumerate(dr):
                sx=int(sr[round(j*(len(sr)-1)/max(1,len(dr)-1))])
                if not hem[y,x]:dest[y,x]=source[sy,sx]
                links.append([int(x),int(y),sx,sy,int(source[sy,sx])])
    # Upper source remains the actual authored drawing. Retain same-pose base
    # only where no costume exists; report these residuals, never conceal them.
    remaining=(base>0)&(dest==0)
    return dest,remaining,links
def main():
    out=D/'fourth_geometry_probe_v1';out.mkdir(exist_ok=True)
    a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));report=[]
    for page,(_,refs)in enumerate(PAGES,1):
        rows=[]
        for n in refs:
            p=next(q for q in plan['frames']if q['ref']==n);src=np.array(Image.open(D/'fourth_registered_v1'/f'run_{n:03}.png'));base=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'))
            target,missing,links=retarget(src,base,p['eye_world_original_registration']);mixed=np.where(target,target,base)
            Image.fromarray(target).save(out/f'run_{n:03}.png')
            rows.append((f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 원화 등록',a.rgba(src,16)),('하체 좌표 대응 검토',a.rgba(mixed,16))]))
            report.append({'ref':n,'source_native_sha256':sha(src.tobytes()),'target_sha256':sha(target.tobytes()),'source_links':links,'remaining_base_pixels':int(missing.sum())})
        helper.grid(rows,out/f'comparison_{page}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'method':'검토용 행별 다리 좌표 대응. 새 원화 색인을 기록한 좌표에서만 취함. 명암/재질 손실 시 채택하지 않음.','frames':report})
    print(json.dumps({'refs':len(report),'remaining':[r['remaining_base_pixels']for r in report]}))
if __name__=='__main__':main()
