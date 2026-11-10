"""새7자세 공통머리/총열과 포스4부위 소유 분리 후보. 미정합 셀은 숨기지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from probe_standing_fire_modules import SOURCES
ARM={85:[(-13,-6),(-7,-5),(-5,1),(-6,7),(-11,9),(-13,4)],86:[(-12,-6),(-6,-5),(-5,1),(-6,7),(-11,9),(-13,4)],87:[(-12,-8),(-7,-8),(-4,-1),(-6,5),(-11,5)],89:[(-14,-14),(-8,-14),(-7,-7),(-7,-1),(-12,0),(-14,-7)],90:[(-18,-13),(-12,-15),(-5,-6),(-8,-2),(-14,-1)],91:[(-19,-6),(-13,-5),(-7,-3),(-3,-2),(-3,3),(-9,4),(-15,9),(-18,8)],92:[(-10,-3),(-5,-3),(-2,0),(-3,5),(-7,9),(-11,8)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main():
    d=H/'standing_fire_layers_probe01';need(not d.exists(),'Fresh output');d.mkdir();a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:32]],np.int32);remap=np.argmin(((rgb[:16,None]-rgb[None,17:32])**2).sum(2),axis=1)+1;rows=[]
    for n in(85,86,87,89,90,91,92):
        src=H/SOURCES[n];base=np.array(Image.open(src/f'base_{n:03}_indices.png'));fourth=np.array(Image.open(src/f'fourth_{n:03}_indices.png'));gun=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_indices.png'));guard=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png'))>0;base[guard]=gun[guard]
        front=poly(ARM[n]);deco=(x>=1)&(x<14)&(y>=-24)&(y<-5);common=(y<-5)&~front&~deco&~guard
        over=fourth.copy();over[common|guard]=0;missing=(base>0)&(over==0)&~common&~guard;edge=missing&np.isin(base,[2,15]);pending=missing&~edge;over[edge]=remap[base[edge]]
        owner=np.full(base.shape,6,np.uint8);owner[y>=13]=8;owner[(y>=10)&(x>=-9)&(x<5)]=8;owner[(x>=5)&(y>=-3)&(y<9)]=7;owner[(y<-5)&~front]=5;owner[front]=7
        layers={0:base,**{b:np.where(owner==b,over,0).astype('uint8')for b in(5,6,7,8)}}
        for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        for key,v in [('common_head',common),('front_arm',front),('gun_guard',guard),('outline_registration',edge),('unresolved_base_visible',pending)]:Image.fromarray(v.astype('uint8')*255).save(d/f'{n:03}_{key}_mask.png')
        Image.fromarray(owner).save(d/f'{n:03}_owner.png');a.rgba(base).save(d/f'base_{n:03}.png');compose(a,layers,15).save(d/f'fourth_{n:03}.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'source_directory':SOURCES[n],'common_head_opaque':int(((base>0)&common).sum()),'front_arm_polygon':ARM[n],'outline_registered':[[int(px)-160,int(py)-160,int(base[py,px]),int(over[py,px])]for py,px in zip(*np.nonzero(edge))],'unresolved_base_pixels':[[int(px)-160,int(py)-160,int(base[py,px])]for py,px in zip(*np.nonzero(pending))],'layer_hashes':{str(b):sha(v.tobytes())for b,v in layers.items()},'gun_RGBA_all16_exact':all(np.array_equal(np.array(compose(a,layers,m))[guard],np.array(a.rgba(gun))[guard])for m in range(16))})
    for form,mask in [('base',0),('fourth',15)]:
        for i,refs in enumerate(((85,86,87,89),(90,91,92))):
            pics=[]
            for n in refs:pics.extend([(f'{n} registered source',Image.open(H/SOURCES[n]/f'{form}_{n:03}.png')),(f'{n} common/owner probe',Image.open(d/f'{form}_{n:03}.png'))])
            page(pics,a.composite(0,mask)[0],d/f'{form}_comparison_{i:02}.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'gun_probe_sha256':sha((H/'standing_fire_modules_probe02/report.json').read_bytes()),'rows':rows,'scope':'새원화 공통머리와부분소유 첫후보. unresolved셀은 자동 채움하지 않고 명시. 아직 패킹/최종정합 아님.','old_coarse_head_copied':False,'arc_written':False,'partial_visual_review_pending':True,'unresolved_cells_total':sum(len(r['unresolved_base_pixels'])for r in rows)})
    print(json.dumps([{'ref':r['ref'],'edge':len(r['outline_registered']),'pending':r['unresolved_base_pixels']}for r in rows]))
if __name__=='__main__':main()
