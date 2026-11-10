"""새 탑승4키의 머리/손 공통부와 기본·포스 부분층 첫 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
SOURCES={162:'chaser_base_native01',166:'chaser_base_native01',170:'chaser_base_native02',174:'chaser_base_native02'}
HEAD_CUT={162:-3,166:1,170:-1,174:1}
HAND={162:[(-10,-1),(-5,-1),(-5,2),(-10,2)],166:[(-10,2),(-5,2),(-5,4),(-10,4)],170:[(-10,2),(-5,2),(-5,5),(-10,5)],174:[(-10,1),(-6,1),(-6,6),(-10,6)]}
ARM={162:[(-10,-2),(-3,-2),(2,2),(2,8),(-4,9),(-8,6)],166:[(-10,1),(-2,1),(4,5),(4,10),(-3,10),(-9,6)],170:[(-11,1),(-3,0),(3,4),(2,10),(-5,11),(-9,7)],174:[(-11,0),(-5,0),(-3,6),(-4,12),(-10,12)]}
DECO={162:[(3,-19),(13,-19),(13,-7),(5,-7)],166:[(2,-16),(13,-16),(13,-4),(5,-4)],170:[(3,-18),(14,-18),(14,-6),(5,-6)],174:[(3,-17),(12,-17),(12,-4),(5,-4)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(160+x,160+y)for x,y in points],fill=1);return np.array(im,bool)
def main():
    d=H/'chaser_layers_probe01';need(not d.exists(),'새 후보 필요');d.mkdir()
    a=Archive((H/'prepared_standing_fire_base01/PL00_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:32]],np.int32)
    remap=1+np.argmin(((rgb[:16,None]-rgb[None,17:32])**2).sum(2),axis=1);rows=[]
    for n,src in SOURCES.items():
        base=np.array(Image.open(H/src/f'base_{n:03}_indices.png'));fourth=np.array(Image.open(H/src/f'fourth_{n:03}_indices.png'))
        head=(y<HEAD_CUT[n])&~poly(DECO[n]);hand=poly(HAND[n]);common=head|hand;front=poly(ARM[n])
        over=fourth.copy();over[common]=0
        missing=(base>0)&(over==0)&~common
        # 기존 옛 도트가 아니라 지금 새 기본형의 보라 외곽만 새 포스 팔레트로 맞춘다.
        outline=missing&np.isin(base,[2,15]);over[outline]=remap[base[outline]];pending=missing&~outline
        owner=np.full(base.shape,6,np.uint8);owner[y>=(12 if n==174 else 9)]=8
        owner[(y<HEAD_CUT[n])|poly(DECO[n])]=5;owner[front]=7
        # 뒤쪽 머리카락은 head 소유이며 팔의 피부 손은 공통 원화에서 유지한다.
        braid=(x>=7)&(y>=HEAD_CUT[n])&(y<(8 if n!=174 else 10));owner[braid]=5
        layers={0:base,**{b:np.where(owner==b,over,0).astype('uint8')for b in(5,6,7,8)}}
        for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        for k,v in [('common',common),('head',head),('hand',hand),('front_arm',front),('outline',outline),('unresolved',pending)]:Image.fromarray(v.astype('uint8')*255).save(d/f'{n:03}_{k}_mask.png')
        Image.fromarray(owner).save(d/f'{n:03}_owner.png');a.rgba(base).save(d/f'base_{n:03}.png');compose(a,layers,15).save(d/f'fourth_{n:03}.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'source_directory':src,'common_new_head_opaque':int((head&(base>0)).sum()),'common_new_hand_opaque':int((hand&(base>0)).sum()),
            'outline_registration':[[int(px)-160,int(py)-160,int(base[py,px]),int(over[py,px])]for py,px in zip(*np.nonzero(outline))],
            'unresolved_base_cells':[[int(px)-160,int(py)-160,int(base[py,px])]for py,px in zip(*np.nonzero(pending))],
            'layer_hashes':{str(b):sha(z.tobytes())for b,z in layers.items()}})
    for form,mask in [('base',0),('fourth',15)]:
        for i,refs in enumerate(((162,166),(170,174))):
            pics=[]
            for n in refs:pics.extend([(f'{n} generated',Image.open(H/SOURCES[n]/f'{form}_{n:03}.png')),(f'{n} common ownership',Image.open(d/f'{form}_{n:03}.png'))])
            page(pics,a.composite(0,mask)[0],d/f'{form}_comparison_{i:02}.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'rows':rows,'pending_cells':sum(len(r['unresolved_base_cells'])for r in rows),
        'policy':'새 기본형 원화 머리와 손을 같은 자세의 공통부로 사용. 옛 머리/몸체 복사 없음. 의상 부분층은 새 포스 원화. 아직 미정합 셀은 숨기거나 자동 채우지 않음.',
        'body_resized':False,'arc_written':False,'partial_review_pending':True,'hand_contact_exact_claimed':False})
    print(json.dumps([{'ref':r['ref'],'pending':r['unresolved_base_cells'],'outline':len(r['outline_registration'])}for r in rows]))
if __name__=='__main__':main()
