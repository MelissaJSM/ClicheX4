"""새 어깨 고정 사격팔을 원 총구와 같은 원점에 등록한다."""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation,map_coordinates
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper,digest
from review_all_bodies import source as body_source

SPANS={50:{-8:(-19,-17),-7:(-19,-13),-6:(-19,-5),-5:(-16,-3),-4:(-14,-3),-3:(-9,-3)},
       52:{-5:(-19,-18),-4:(-19,-15),-3:(-19,-12),-2:(-18,-9),-1:(-16,-5),0:(-13,-3),1:(-10,-3),2:(-6,-4)}}
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'landing_reach_joint_v1';need(not out.exists(),'Fresh output');out.mkdir()
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];reports=[]
    for n in (50,52):
        body=np.array(Image.open(body_source(n-1)/f'base_{n-1:03}.png'));src=np.array(Image.open(D/'landing_reach_registered_v1'/f'base_{n:03}.png'));gun=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'))
        mask=np.zeros_like(body,bool)
        for py,(x0,x1) in SPANS[n].items():mask[py+160,x0+160:x1+161]=True
        arm=np.where(mask,src,0).astype(np.uint8);original_arm=arm.copy();angle=10 if n==50 else 0;pivot=(-3,-4)if n==50 else None
        if angle:
            # A rigid rotation about the authored shoulder, not independent
            # stretching or a copied old sleeve. Inverse-map source indices.
            c=math.cos(math.radians(angle));s=math.sin(math.radians(angle));u=x-pivot[0];v=y-pivot[1]
            sx=c*u+s*v+pivot[0]+160;sy=-s*u+c*v+pivot[1]+160
            arm=map_coordinates(arm,[sy,sx],order=0,mode='constant',cval=0).astype(np.uint8)
        q=next(q for q in p['frames']if q['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']]
        head=(x>=ex-2)&(y<=ey+5);remove=(x<=ex+1)&(y>=ey+4)&(y<ey+14)&~head;rest=body.copy();rest[remove]=0
        target=np.where(arm,arm,rest).astype(np.uint8)
        gy,gx=np.nonzero(gun);window=(xx>=gx.min())&(xx<=gx.min()+7)&(yy>=gy.min())&(yy<=gy.max());target[window]=gun[window]
        allowed=remove|(arm>0)|window;need(np.array_equal(target[~allowed],body[~allowed]),'Unrelated body');need(np.array_equal(target[window],gun[window]),'Gun')
        _,count=label(target>0,np.ones((3,3)));contacts=int(np.count_nonzero(binary_dilation(arm>0,np.ones((3,3)))&(rest>0)))
        for name,idx in [('merged',target),('new_sleeve',arm),('source_sleeve',original_arm),('remaining_body',rest)]:Image.fromarray(idx).save(out/f'{name}_{n:03}.png');a.rgba(idx).save(out/f'{name}_{n:03}_rgba.png')
        rows.append((f'landing shot{n}',[('기존',a.composite(n)[0]),('새 몸체',a.rgba(body)),('새로 뻗은 팔 원화',a.rgba(src)),('새 팔/원 총 접점',a.rgba(target))]))
        reports.append({'ref':n,'source_mask_spans':SPANS[n],'source_mask_sha256':sha(mask.tobytes()),'source_art_sha256':digest(D/'landing_reach_generated_v1/generated.png'),'rigid_rotation_deg':angle,'shoulder_pivot':pivot,'scale_or_horizontal_stretch':False,'gun_window_exact':True,'non_arm_region_exact':True,'alpha_components_8':count,'sleeve_body_contact_pixels':contacts,'native_packed':False})
    helper.grid(rows,out/'comparison.png',8);write(out/'manifest.json',{'frames':reports,'source_arc_sha256':sha(a.data),'native_packed':False,'runtime_verified':False});print(json.dumps(reports))
if __name__=='__main__':main()
