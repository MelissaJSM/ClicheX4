"""새 머릿결을 공통으로 쓰고 새 포스 장식만 소규모 파츠로 분리하는 미확정 후보.

은행/자원은 쓰지 않는다. 원화 몸체는 자동축소하지 않으며 기존 픽셀을 복사하지 않는다.
"""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from inspect_air_layers import arrays,REFS,P
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame
from native_pose_pack import need,sha,write

def polygon(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)

def head_region(n):
    # New hair/face only. Raised sleeves and hands use individual pose boundaries.
    if n in(33,35,45,47,49):
        points=[(-19,-28),(14,-28),(14,-6),(19,1),(15,6),(6,5),(3,-2),(-13,-3),(-15,-8)]
    elif n==37:points=[(-15,-27),(14,-27),(14,-6),(19,0),(15,5),(5,4),(1,-3),(-10,-4),(-13,-12)]
    elif n==39:points=[(-11,-24),(-3,-27),(4,-27),(5,-19),(5,-6),(14,-2),(15,3),(8,4),(2,-2),(-9,-3),(-12,-12)]
    elif n==41:points=[(-11,-24),(-4,-26),(5,-26),(6,-19),(6,-5),(16,0),(15,5),(7,4),(1,-2),(-10,-4),(-13,-12)]
    elif n==43:points=[(-14,-23),(-5,-27),(6,-27),(7,-20),(5,-8),(16,-1),(15,5),(6,4),(1,-3),(-12,-5),(-15,-12)]
    elif n==51:points=[(-18,-23),(14,-23),(14,-1),(18,5),(11,9),(4,7),(1,2),(-13,1)]
    else:points=[(-18,-24),(14,-24),(14,-2),(19,5),(12,8),(5,6),(1,1),(-13,0)]
    return polygon(points)

def main():
    o=H/'air_common_head_probe03';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    # Reusing a previously stored single-part record need not grow bank5.
    templates={records(a.c,5,n)[i:i+4]for n in range(237)for i in range(0,len(records(a.c,5,n)),4)}
    rows=[];pics=[]
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32)
    mapping={i:int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))+1 for i in range(1,16)}
    for n in sorted(REFS):
        base,full=arrays(n);common=head_region(n);raw=full.copy()
        faceboxes={33:(-9,-13,0,-4),35:(-9,-13,0,-3),37:(-9,-14,1,-4),39:(-8,-16,1,-5),41:(-7,-16,2,-5),43:(-9,-15,1,-5),45:(-10,-13,0,-3),47:(-9,-13,1,-3),49:(-9,-13,1,-3),51:(-10,-9,0,1),53:(-10,-10,0,0)}
        fx0,fy0,fx1,fy1=faceboxes[n];face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1)
        # Only actual face material, not red sleeve/collar fragments that happen
        # to fall within the rectangular face envelope, is shared.
        common&=np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13]))
        if n==39:arm=polygon([(3,-28),(10,-28),(10,-9),(5,-2),(-1,-4),(0,-8),(3,-14)])
        elif n==41:arm=polygon([(5,-29),(13,-29),(13,-8),(6,-2),(0,-4),(2,-9),(5,-15)])|polygon([(-17,-29),(-7,-29),(-6,-19),(-8,-11),(-13,-12)])
        elif n==43:arm=polygon([(11,-23),(17,-23),(17,-12),(3,-3),(-2,-6),(1,-10)])|polygon([(-20,-25),(-9,-25),(-10,-16),(-8,-10),(-12,-8),(-20,-15)])
        elif n==37:arm=polygon([(-20,-19),(-10,-19),(-8,-9),(-6,-4),(-11,-3),(-18,-9)])
        else:arm=np.zeros_like(common)
        common&=~arm
        # The new Fourth head ornament, excluding the exposed face, fits a
        # 16px native patch; the patch is not an old tile or resized figure.
        patch_top={33:-21,35:-21,37:-21,39:-24,41:-24,43:-23,45:-21,47:-21,49:-21,51:-17,53:-18}[n]
        decoration=common&(x>=2)&(x<18)&(y>=patch_top)&(y<patch_top+16)
        full[common]=0
        full[decoration]=raw[decoration]
        # Cover only the new base flower/outline not covered by the new hat.
        # This is a diagnostic material registration, listed pixel-by-pixel.
        edge=decoration&(base>0)&(full==0);marks=[]
        for py,px in zip(*np.nonzero(edge)):
            src=int(base[py,px]);dst=mapping[src]
            if src in(1,4,10,11):dst={1:2,4:11,10:10,11:11}[src]
            full[py,px]=dst;marks.append([int(px)-160,int(py)-160,src,dst])
        outside=(base>0)&(full==0)&~common
        clothing_marks=[]
        garment={1:2,4:11,10:10,11:11,12:9,13:9,15:1}
        for py,px in zip(*np.nonzero(outside)):
            src=int(base[py,px]);dst=garment.get(src,mapping[src]);full[py,px]=dst
            clothing_marks.append([int(px)-160,int(py)-160,src,dst])
        # Keep layer5 limited to the new ornament region, to show the exact
        # required bounds before any pinned-tile packing is attempted.
        head=np.where(decoration,full,0).astype(np.uint8);body=np.where(~decoration,full,0).astype(np.uint8)
        target=a.rgba(base);target.alpha_composite(a.rgba(body,16));target.alpha_composite(a.rgba(head,16))
        Image.fromarray(common.astype(np.uint8)*255).save(o/f'{n:03}_common_head_mask.png')
        Image.fromarray(head).save(o/f'{n:03}_head_indices.png');Image.fromarray(body).save(o/f'{n:03}_remaining_fourth_indices.png');target.save(o/f'{n:03}_preview.png')
        ys,xs=np.nonzero(head);bbox=[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)]
        compatible=[]
        for r in templates:
            flag,t,tx,ty=__import__('struct').unpack('<BBbb',r)
            if flag==0 and t not in(0,16) and tx<=bbox[0] and ty<=bbox[1] and tx+16>=bbox[2] and ty+16>=bbox[3]:compatible.append(r.hex())
        rows.append({'ref':n,'head_bbox_world':bbox,'existing_record_candidates':sorted(compatible),'new_source_edge_material_pixels':marks,
                     'clothing_alpha_edge_material_pixels':clothing_marks,
                     'new_base_head_source_pixels':int(np.count_nonzero(base[common&~decoration])),'old_head_pixels_used':0})
        pics.extend([(f'{n} new raw Fourth',a.rgba(raw,16)),(f'{n} common-head trial',target)])
    for start in range(0,len(pics),8):page(pics[start:start+8],a.composite(0,15)[0],o/f'comparison_{start//8:02}.png',cols=2,scale=4)
    write(o/'probe.json',{'candidate_only':True,'source_parent_sha256':sha(P.read_bytes()),'source_index_sha256':sha((H/'air_detail_source_index01.json').read_bytes()),'records':rows,
                       'body_partial_ownership_pending':True,'visual_review_pending':True,'resource_written':False})
    print(json.dumps([{'ref':r['ref'],'bbox':r['head_bbox_world'],'templates':len(r['existing_record_candidates']),'edge':len(r['new_source_edge_material_pixels'])}for r in rows]))
if __name__=='__main__':main()
