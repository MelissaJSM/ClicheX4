"""새 포스 하체의 자연스러운 실루엣에 새 기본 원화 다리별 재질을 등록."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,write,helper,need
from register_fourth_geometry_v2 import components,center
from register_fourth_geometry_v3 import assign
from scipy.ndimage import binary_dilation
from PIL import Image
import numpy as np
D=Path(__file__).parent
def retarget(base,source,eye):
    ex,ey=eye;yy,xx=np.indices(base.shape);wy=yy-160;start=ey+19
    hem_seed=np.isin(source,(13,15))&(wy>=ey+14)&(wy<=ey+24);hem=binary_dilation(hem_seed,iterations=1)&(source>0)
    fm=(source>0)&(wy>=start)&~hem&~np.isin(source,(7,8,9))
    bm=(base>0)&(wy>=start)&~hem&~np.isin(base,(7,8,9))
    feet=sorted(components(np.isin(source,(5,6))&(wy>=start)),key=lambda m:int(m.sum()),reverse=True)[:2];need(len(feet)>0,'Source feet count');feet=sorted(feet,key=lambda q:center(q)[0])
    srcs=assign(bm,feet);dsts=assign(fm,feet)
    target=base.copy();target[bm]=0;links=[];limbs=[]
    for limb,(src,dst)in enumerate(zip(srcs,dsts)):
        sy,sx=np.nonzero(src);dy,dx=np.nonzero(dst);valid_rows=np.unique(sy)
        for y in np.unique(dy):
            dr=np.flatnonzero(dst[y]);source_y=int(valid_rows[np.abs(valid_rows-y).argmin()]);sr=np.flatnonzero(src[source_y]);need(len(sr)>0,'Mapped row empty')
            for x in dr:
                k=round((x-dr[0])*(len(sr)-1)/max(1,dr[-1]-dr[0]));source_x=int(sr[k]);value=int(base[source_y,source_x]);target[y,x]=value;links.append([int(x),int(y),source_x,source_y,value,limb])
        limbs.append({'source_bbox':[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)],'target_bbox':[int(dx.min()),int(dy.min()),int(dx.max()+1),int(dy.max()+1)]})
    # Above the lower-leg seam, the new base still owns its authored skirt/skin;
    # fourth's authored dress overlays it. No source material recoloring.
    return target,links,limbs
def main():
    out=D/'common_lower_registered';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));reports=[]
    for page in range(4):
        rows=[]
        for n in range(1+page*8,9+page*8,2):
            p=next(q for q in plan['frames']if q['ref']==n);b=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'));f=np.array(Image.open(D/'fourth_body_scale'/f'run_{n:03}.png'));target,links,limbs=retarget(b,f,p['eye_world_original_registration']);full=np.where(f,f,target)
            Image.fromarray(target).save(out/f'run_{n:03}.png');Image.fromarray(full).save(out/f'fourth_{n:03}.png');rows.append((f'ref {n}',[('새 기본 원화',a.rgba(b)),('기본 원화 다리별 등록',a.rgba(target)),('포스 원화 발 유지',a.rgba(full,16))]));reports.append({'ref':n,'source_links':links,'limbs':limbs,'remaining_base_pixels':int(((target>0)&(f==0)).sum())})
        helper.grid(rows,out/f'comparison_{page+1}.png',6)
    write(out/'report.json',{'ready_to_apply':False,'method':'각 다리를 별도로 나눠 같은 행의 원화 외곽/재질을 포스 실루엣에 등록. 기존 도트/색채움 없음. 시험본.','frames':reports})
if __name__=='__main__':main()
