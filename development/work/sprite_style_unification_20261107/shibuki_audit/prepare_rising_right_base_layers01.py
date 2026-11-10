"""새 오른손103/104만 파츠로 분리. 구형 몸체/머리/효과 픽셀을 복사하지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose,polygon
from native_pose_pack import need,sha,write
HEADS={103:[(-16,-22),(3,-22),(3,-14),(10,-13),(12,-5),(9,6),(7,15),(1,16),(1,12),(-3,10),(-4,5),(-11,3),(-16,-5)],104:[(-16,-26),(2,-26),(2,-18),(7,-16),(11,-11),(13,8),(8,16),(5,15),(4,10),(0,8),(-2,1),(-11,-3),(-16,-7)]}
FACE={103:(-11,-7,1,1),104:(-11,-11,1,-4)}
DECOS={103:[(3,-14),(9,-14),(12,-10),(12,-4),(10,-3),(8,-6),(4,-7),(2,-11)],104:[(1,-18),(8,-18),(11,-14),(10,-7),(6,-8),(5,-11),(1,-12)]}
def main():
    out=H/'rising_right_base_layers01';need(not out.exists(),'Fresh output');out.mkdir();a=Archive((H/'prepared_rising_fire_base02/PL00_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut={i:1+int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))for i in range(1,16)}
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics=[]
    for n in(103,104):
        d=H/'rising_right_hand_native04';base=np.array(Image.open(d/f'base_{n}_indices.png'));full=np.array(Image.open(d/f'fourth_{n}_indices.png'));raw=full.copy()
        head=polygon(HEADS[n]);fx0,fy0,fx1,fy1=FACE[n];face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1)
        common=head&(np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13])))
        deco=polygon(DECOS[n]);common&=~deco;full[common]=0
        # Fixed new source contours may differ by one native pixel between the
        # two costume drawings; record each retained base texel and its genuine
        # Fourth material mapping instead of erasing base with transparency.
        missing=(base>0)&(full==0)&~common;marks=[]
        mat={1:2,4:11,10:10,11:11,12:9,13:9,15:1}
        for py,px in zip(*np.nonzero(missing)):
            src=int(base[py,px]);dst=mat.get(src,lut[src])
            if py-160>=10 and src in(2,3,5,6,8,9,14):dst={2:2,3:3,5:5,6:3,8:4,9:5,14:5}[src]
            full[py,px]=dst;marks.append([int(px)-160,int(py)-160,src,dst])
        owner=np.full(base.shape,6,np.uint8)
        owner[(y>=11)&(x<=6)]=8
        if n==103:
            arms=polygon([(2,-5),(9,-5),(10,3),(8,9),(1,7),(0,2)])|polygon([(-14,0),(-8,0),(-7,7),(-10,11),(-16,9)])
        else:
            arms=polygon([(1,-33),(10,-33),(12,-19),(9,-13),(2,-13),(2,-20)])|polygon([(-16,-5),(-9,-5),(-9,0),(-7,4),(-7,9),(-15,10),(-17,5)])
        owner[arms]=7;owner[deco]=5
        layers={0:base,**{b:np.where(owner==b,full,0).astype(np.uint8)for b in(5,6,7,8)}}
        target=compose(a,layers,15)
        for b,v in layers.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(common.astype(np.uint8)*255).save(out/f'{n:03}_common_mask.png');Image.fromarray(owner).save(out/f'{n:03}_owner.png')
        a.rgba(base).save(out/f'{n}_base.png');target.save(out/f'{n}_fourth.png')
        pics.extend([(f'{n} new Fourth source',a.rgba(raw,16)),(f'{n} shared new hair + Fourth parts',target)])
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],out/f'{n}_partial.png',cols=4,scale=4)
        rows.append({'ref':n,'new_common_pixels':int(np.count_nonzero(base[common])),'contour_material_mapping':marks,'layer_pixels':{str(b):int(np.count_nonzero(v))for b,v in layers.items()},'old_body_copied':False,'head_polygon':HEADS[n],'ornament_polygon':DECOS[n]})
    page(pics,a.composite(0,15)[0],out/'comparison.png',cols=2,scale=5)
    write(out/'report.json',{'candidate_only':True,'rows':rows,'source_parent_sha256':sha(a.data),'native_palette_and_coordinates_unchanged':True,'resource_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
