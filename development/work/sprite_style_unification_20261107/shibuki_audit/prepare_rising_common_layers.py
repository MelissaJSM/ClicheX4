"""라이징파이어 새 원화만을 공통 머리/장식/의상 파츠로 등록하는 후보.

수용 대기나 구형 몸체를 복사하지 않는다. 겹침 외곽의 재질 대응은 좌표별 기록한다.
"""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from native_pose_pack import need,sha,write
REFS=(100,101,102,103,104,231)
def polygon(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def arrays(n):
    d=H/f'rising_fire_native{1 if n<103 else 2:02}'
    if n==104:d=H/'rising104_arm_native02'
    return [np.array(Image.open(d/f'{s}_{n:03}_indices.png'))for s in('base','fourth')]
HEADS={
100:[(-17,-19),(18,-19),(18,7),(16,16),(8,17),(4,10),(-2,7),(-10,7),(-10,3),(-17,1)],
101:[(-12,-29),(17,-29),(17,-3),(15,6),(8,8),(2,-3),(-10,-3),(-12,-9),(-14,-12)],
102:[(-10,-27),(18,-27),(18,-2),(15,11),(8,11),(3,1),(-9,1),(-11,-5)],
103:[(-10,-23),(16,-23),(16,2),(12,12),(6,12),(2,2),(-10,2),(-12,-6)],
104:[(-10,-27),(18,-27),(18,-1),(15,10),(8,12),(3,-1),(-10,-1),(-12,-7)],
231:[(-11,-25),(18,-25),(18,-2),(19,7),(14,13),(7,12),(2,1),(-10,1),(-12,-7)]}
FACE={100:(-9,0,1,7),101:(-10,-13,0,-3),102:(-10,-9,1,1),103:(-10,-9,0,2),104:(-10,-14,0,-2),231:(-10,-10,1,1)}
DECO={100:(2,-10),101:(2,-23),102:(3,-18),103:(2,-14),104:(2,-22),231:(3,-19)}
def main():
    out=H/'rising_common_layers01';need(not out.exists(),'Fresh output required');out.mkdir()
    a=Archive((H/'prepared_double_cyclone_base01/PL00_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
    lut={i:int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))+1 for i in range(1,16)}
    material={1:2,4:11,10:10,11:11,12:9,13:9,15:1};rows=[];pics=[]
    for n in REFS:
        base,full=arrays(n);raw=full.copy();shape=HEADS[n];common=polygon(shape);fx0,fy0,fx1,fy1=FACE[n]
        face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1)
        common&=np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13]))
        dx,dy=DECO[n];deco=(x>=dx)&(x<dx+16)&(y>=dy)&(y<dy+16)
        # The complete new red ornament must belong to Head, including red
        # pixels excluded from the hair-only color predicate.
        common|=deco
        full[common]=0;full[deco]=raw[deco]
        missing=(base>0)&(full==0)&~(common&~deco);marks=[]
        for py,px in zip(*np.nonzero(missing)):
            src=int(base[py,px]);dst=material.get(src,lut[src])
            # Clothing contour below the skirt becomes dark boot fabric;
            # white socks must never remain in a full Fourth composition.
            if py-160>=12 and src in(2,3,5,6,8,9,14):dst={2:2,3:3,5:5,6:3,8:4,9:5,14:5}[src]
            full[py,px]=dst;marks.append([int(px)-160,int(py)-160,src,dst])
        owner=np.full(base.shape,6,np.uint8)
        owner[y>={100:16,101:12,102:12,103:11,104:12,231:12}[n]]=8
        if n in(101,102):owner[(x<=-6)&(y>=7)&(y<=17)]=8
        owner[(x<=-10)&(y<8)]=7
        if n==100:owner[(x<=-10)&(y>=2)&(y<17)]=7
        owner[(x>=7)&(y>={100:8,101:0,102:2,103:2,104:1,231:1}[n])&(y<14)]=7
        owner[deco]=5
        layers={0:base};layers.update({b:np.where(owner==b,full,0).astype(np.uint8)for b in(5,6,7,8)})
        need(not np.any((base>0)&(full==0)&~common),'Uncovered base material')
        for b,v in layers.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(common.astype(np.uint8)*255).save(out/f'{n:03}_common_mask.png');Image.fromarray(owner).save(out/f'{n:03}_owner.png')
        target=compose(a,layers,15);target.save(out/f'{n:03}_fourth.png');a.rgba(base).save(out/f'{n:03}_base.png')
        pics.extend([(f'{n} generated Fourth',a.rgba(raw,16)),(f'{n} new shared head + parts',target)])
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],out/f'{n:03}_partial.png',cols=4,scale=4)
        rows.append({'ref':n,'common_head_polygon':shape,'face_rect':FACE[n],'decoration_rect':[dx,dy,dx+16,dy+16],'new_common_head_pixels':int(np.count_nonzero(base[common&~deco])),'contour_material_registration':marks,'contour_pixels':len(marks),'part_pixels':{str(b):int(np.count_nonzero(v))for b,v in layers.items()},'old_body_copied':0})
    for i in range(0,len(pics),4):page(pics[i:i+4],a.composite(0,15)[0],out/f'comparison_{i//4:02}.png',cols=2,scale=5)
    write(out/'report.json',{'candidate_only':True,'resource_written':False,'rows':rows,'after_pack_independent_pending':True})
    print(json.dumps([{k:r[k]for k in('ref','contour_pixels','part_pixels')}for r in rows]))
if __name__=='__main__':main()
