"""신규 사다리 원화의 머리/몸/팔/다리 소유를 분리하는 검토용 후보.

이미지 생성 원화의 픽셀은 유지한다. 기본형만 밖으로 남는 작은 외곽은
같은 부위의 포스 재질로 등록한다. 아직 접점 보완/사격 원화가 남아 있다.
"""
from pathlib import Path
import sys,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write

KEYS=(143,144,146,149,151,153,154,183)
SOURCES={143:'ladder_page01_detail02',144:'ladder_page01_detail02',146:'ladder_page01_detail02',149:'ladder_contacts_registered01',151:'ladder_contacts_registered01',153:'ladder_contacts_registered01',154:'ladder_native_page03',183:'ladder_native_page03'}
HEAD={
143:[(-17,-23),(9,-23),(18,-10),(18,2),(9,2),(6,-3),(-7,-2),(-14,1),(-17,-7)],
144:[(-9,-26),(11,-26),(15,-15),(11,-4),(4,-1),(-8,-5),(-11,-15)],
146:[(-8,-24),(12,-24),(14,-12),(8,-4),(-7,-4),(-11,-13)],
149:[(-15,-25),(8,-25),(15,-12),(16,-3),(9,1),(4,-4),(-7,-4),(-14,-10)],
151:[(-8,-24),(12,-24),(14,-11),(8,-3),(-7,-2),(-11,-12)],
153:[(-11,-28),(12,-28),(15,-17),(9,-8),(-9,-8),(-13,-17)],
154:[(-18,-16),(4,-16),(15,-4),(15,6),(5,5),(-6,4),(-15,1),(-18,-8)],
183:[(-11,-7),(11,-7),(14,4),(10,11),(-9,11),(-13,4)]}
ARMS={
143:[[(-18,-6),(-10,-7),(-2,-1),(-2,9),(-10,13),(-18,7)],[(4,-1),(11,-1),(14,5),(10,10),(3,8)]],
144:[[(-17,-20),(-8,-20),(-7,-6),(-4,0),(-8,7),(-16,3)],[(9,-10),(17,-10),(17,7),(10,11),(7,4)]],
146:[[(-14,-32),(-3,-32),(-4,-17),(-5,-6),(-9,3),(-15,0)],[(7,-14),(17,-14),(18,4),(12,9),(7,3)]],
149:[[(-4,-32),(8,-32),(10,-18),(4,-16),(1,-22)], [(-16,-9),(-7,-10),(0,-3),(0,7),(-8,9),(-15,3)]],
151:[[(-16,-31),(-3,-31),(-5,-14),(-8,-6),(-16,-9)],[(8,-14),(18,-14),(18,2),(12,8),(6,3)]],
153:[[(-16,-14),(-8,-13),(-6,-5),(-10,-2),(-17,-5)],[(8,-14),(17,-14),(18,-4),(10,-2),(6,-6)]],
154:[[(-12,-2),(-5,-2),(2,3),(3,10),(-2,14),(-12,7)],[(2,-2),(10,0),(14,8),(9,12),(3,7)]],
183:[[(-17,4),(-9,4),(-7,12),(-8,19),(-15,18)],[(8,4),(18,4),(18,18),(10,20),(7,12)]]}
LEGS={
143:[[(-11,7),(-2,5),(5,15),(7,25),(-4,26),(-7,17),(-13,15)]],
144:[[(-10,4),(-3,4),(1,8),(-4,15),(-9,16)],[(-1,14),(6,14),(6,25),(-2,25)]],
146:[[(0,5),(7,5),(6,13),(1,14),(-1,10)],[(-9,14),(0,14),(0,25),(-8,25),(-10,21)]],
149:[[(-10,4),(-2,4),(3,13),(5,24),(-3,25),(-4,16),(-12,13)]],
151:[[(-3,6),(4,6),(4,23),(-3,24),(-5,17),(-4,12)]],
153:[[(-10,-3),(-3,-2),(0,4),(-4,6),(-8,4)],[(1,0),(9,1),(10,13),(2,14),(-1,7)]],
154:[[(-9,10),(0,8),(8,15),(8,26),(-3,26),(-5,18),(-11,16)]],
183:[[(-7,16),(-1,16),(1,21),(-1,27),(-7,27)],[(2,21),(8,21),(11,31),(1,31),(-1,26)]]}

def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160) for x,y in points],fill=1)
    return np.array(im,bool)

def owner(ref):
    v=np.full((384,384),6,np.uint8)
    for p in LEGS[ref]:v[poly(p)]=8
    for p in ARMS[ref]:v[poly(p)]=7
    # Head is placed last where hair falls in front of the shoulder. Raised
    # palm/cuff regions outside its polygon retain Arm ownership.
    v[poly(HEAD[ref])]=5
    if ref==143:v[poly(ARMS[ref][0])]=7
    if ref==149:
        # The sleeve rises BEHIND the right hair ornament. A rectangular head
        # region would incorrectly assign that entire raised sleeve to Head.
        base=source(ref,'base');yy,xx=np.indices(base.shape);x=xx-160;y=yy-160
        region=(x>=0)&(x<=10)&(y>=-30)&(y<=-14)
        hair=region&np.isin(base,[2,5,8,10,11,14])
        arm=region&np.isin(base,[3,6,9,12,13])
        v[region]=np.where(distance_transform_edt(~hair)[region]<=distance_transform_edt(~arm)[region],5,7)
    return v

def source(ref,form):
    return np.array(Image.open(H/SOURCES[ref]/f'{form}_{ref:03}_indices.png'))

def make(a,ref):
    base=source(ref,'base');raw=source(ref,'fourth');full=raw.copy();own=owner(ref)
    rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)] for w in a.words[:32]],np.int32)
    nearest={i:int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))+1 for i in range(1,16)}
    garment={1:2,4:11,10:10,11:11,12:9,13:9,15:1}
    changes=[]
    for y,x in zip(*np.nonzero((base>0)&(full==0))):
        src=int(base[y,x]);part=int(own[y,x]);dst=nearest[src]
        if part!=5 and src in garment:dst=garment[src]
        elif part==5 and src in(1,4,10,11):dst={1:2,4:11,10:10,11:11}[src]
        full[y,x]=dst;changes.append([int(x)-160,int(y)-160,src,dst,part])
    layers={0:base,**{b:np.where(own==b,full,0).astype(np.uint8) for b in(5,6,7,8)}}
    return layers,own,{'ref':ref,'source':SOURCES[ref],'original_new_fourth_pixels_exact':bool(np.array_equal(raw[raw>0],full[raw>0])),'edge_material_registration':changes,'base_outside_after':int(np.count_nonzero((base>0)&(full==0)))}

def compose(a,layers,mask):
    out=a.rgba(layers[0])
    for bit,b in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:out.alpha_composite(a.rgba(layers[b],16))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve();need(out.is_relative_to(H)and not out.exists(),'New own output required')
    data=(H/'prepared_wall_front01/PL00_U.ARC').read_bytes();need(sha(data)=='db508292c2746b5c4a12e60e9cf28f5ebe558e7998788c3d1d5440a4f8fd481a','Parent changed');a=Archive(data);out.mkdir();proof=[]
    colors={5:(204,120,225),6:(80,160,230),7:(235,150,80),8:(100,210,140)}
    for n in KEYS:
        layers,own,row=make(a,n);proof.append(row)
        for b,v in layers.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(own).save(out/f'{n:03}_owner.png')
        vis=np.zeros((384,384,4),np.uint8)
        for b,color in colors.items():vis[(own==b)&(layers[0]>0)]=(*color,255)
        Image.fromarray(vis).save(out/f'{n:03}_owner_visual.png')
        compose(a,layers,15).save(out/f'fourth_{n:03}.png');a.rgba(layers[0]).save(out/f'base_{n:03}.png')
        page([(f'{n} mask {m:X}',compose(a,layers,m)) for m in range(16)],a.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
    page([(f'{n} owner',Image.open(out/f'{n:03}_owner_visual.png')) for n in KEYS],a.composite(0,0)[0],out/'ownership.png',cols=4,scale=4)
    write(out/'registration.json',{'parent_sha256':sha(data),'rows':proof,'candidate_only':True,'contact_correction_pending':[149,151,153],'shot_art_pending':[150,155],'old_body_head_overwrite':False,'whole_body_rescale':False,'not_packed':True,'runtime_verified':False})
    print([(r['ref'],len(r['edge_material_registration'])) for r in proof])

if __name__=='__main__':main()
