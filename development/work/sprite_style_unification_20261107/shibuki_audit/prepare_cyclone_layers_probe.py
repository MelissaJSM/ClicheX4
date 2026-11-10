"""98의 새 기본/포스 원화를 의미별 파츠로 분리하는 비패킹 후보."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from prepare_lowhp_final import compose

def main():
    o=H/'double_cyclone_layers_probe01';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive((H/'prepared_air01/PL00_U.ARC').read_bytes());d=H/'double_cyclone_native01'
    base=np.array(Image.open(d/'base_098_indices.png'));full=np.array(Image.open(d/'fourth_098_indices.png'));raw=full.copy();yy,xx=np.indices(base.shape);x=xx-160;y=yy-160
    # Only the newly generated head/face is common. The new navy/gold ornament
    # replaces the new basic red ornament in its own Head part, not Body/Arm.
    common=(x>=-16)&(x<15)&(y>=-24)&(y<-3)
    common|=(x>=4)&(x<13)&(y>=-3)&(y<1)&np.isin(base,[0,2,5,8,14,15])
    decoration=(x>=0)&(x<14)&(y>=-18)&(y<-3)
    common&=np.isin(base,[0,2,5,8,14,15])|((x>=-10)&(x<3)&(y>=-14)&(y<-3)&np.isin(base,[7,10,11,12,13]))|decoration
    full[common]=0;full[decoration]=raw[decoration]
    # Native overlays cannot erase opaque base pixels. Each uncovered contour
    # is explicitly recolored as the corresponding new costume material.
    missing=(base>0)&(full==0)&~(common&~decoration);edge=[]
    ink={1:2,2:1,4:11,5:6,6:3,7:10,8:4,9:5,10:10,11:11,12:9,13:9,14:5,15:1}
    for py,px in zip(*np.nonzero(missing)):
        src=int(base[py,px]);dst=ink[src]
        if y[py,px]>=9 and src in(3,5,6,8,9,14):dst=3
        full[py,px]=dst;edge.append([int(x[py,px]),int(y[py,px]),src,dst])
    owner=np.full(base.shape,6,np.uint8);owner[(y>=9)&((x<-6)|(x>4))]=8;owner[(y>=-10)&(y<10)&((x<-10)|(x>9))]=7;owner[decoration]=5
    layers={0:base};layers.update({b:np.where(owner==b,full,0).astype(np.uint8)for b in(5,6,7,8)})
    target=compose(a,layers,15);target.save(o/'full.png');a.rgba(base).save(o/'base.png')
    for b,v in layers.items():Image.fromarray(v).save(o/f'098_bank{b}_indices.png')
    Image.fromarray(common.astype(np.uint8)*255).save(o/'common_head_mask.png');Image.fromarray(owner).save(o/'ownership.png')
    page([('generated full',a.rgba(raw,16)),('new shared head / parts',target),('Head only',compose(a,layers,1)),('body arms legs',compose(a,layers,14))],a.composite(0,15)[0],o/'comparison.png',cols=2,scale=5)
    page([(f'mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],o/'partial.png',cols=4,scale=4)
    write(o/'report.json',{'candidate_only':True,'parent_arc_sha256':sha(a.data),'new_base_source_exact':True,'old_head_pixels_copied':0,'new_base_shared_head_pixels':int(np.count_nonzero(base[common&~decoration])),'source_boundary_material_pixels':edge,'edge_count':len(edge),'part_pixels':{str(b):int(np.count_nonzero(v))for b,v in layers.items()},'contact_registration_pending':True,'full_alpha_subset_requirement_satisfied':bool(np.all((base==0)|(full>0)|(common&~decoration))),'resource_written':False})
    print(json.dumps({'edge_count':len(edge),'pixels':{str(b):int(np.count_nonzero(v))for b,v in layers.items()}}))
if __name__=='__main__':main()
