"""새 원화와 수용 기본형의 손끝/발 최하단을 의미구역 안에서 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page,metrics
SOURCES={**{n:'ultimate_ladder_native03'for n in(143,144,146)},**{n:'ultimate_ladder_native_page02'for n in(149,151,153)},**{n:'ultimate_ladder_native_page03'for n in(154,183)}}
ROIS={143:{'front_hand':(-19,-9,-8,1)},144:{'upper_hand':(-17,-22,-8,-10),'lower_hand':(9,-15,19,-2)},146:{'upper_hand':(-16,-32,-3,-20),'lower_hand':(7,-16,19,-1)},149:{'upper_hand':(-4,-32,6,-21),'front_hand':(-19,-13,-5,2)},151:{'upper_hand':(-15,-32,-2,-19),'lower_hand':(7,-16,18,-1)},153:{'left_hand':(-19,-16,-7,-1),'right_hand':(7,-16,19,-1)},154:{'front_hand':(-12,5,-1,13)},183:{}}

def box(v,rect):
    x0,y0,x1,y1=rect;region=np.zeros_like(v,bool);region[y0+160:y1+160,x0+160:x1+160]=True;yy,xx=np.nonzero(region&np.isin(v,[12,13]))
    return None if not len(xx)else[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]

def main():
    out=H/'ultimate_ladder_contacts_audit01';need(not out.exists(),'Fresh audit');out.mkdir();bp=H/'prepared_base_run01/PL00_U.ARC';up=H/'prepared_ultimate_dash01/PL02_U.ARC';base=Archive(bp.read_bytes());ult=Archive(up.read_bytes());rows=[]
    for n,folder in SOURCES.items():
        target=base.layer(n)[0];targets={name:box(target,rect)for name,rect in ROIS[n].items()};pics=[(f'{n} accepted pose contacts',base.composite(n,0)[0])]
        for form,mask,pal in(('before',15,16),('after',0,0)):
            v=np.array(Image.open(H/f'{folder}/{form}_{n:03}_indices.png'));points={name:box(v,rect)for name,rect in ROIS[n].items()};im=ult.rgba(v,pal);vis=im.copy();dr=ImageDraw.Draw(vis)
            for name,rect in ROIS[n].items():
                dr.rectangle(tuple(c+160 for c in rect),outline=(250,200,30,255))
            vis.save(out/f'{form}_{n:03}_joint_regions.png');pics.append((f'{n} {form} new joints',im));old=ult.composite(n,mask)[0]
            rows.append({'ref':n,'form':form,'source':folder,'hand_rois':ROIS[n],'accepted_pose_hand_boxes':targets,'new_hand_boxes':points,'accepted_pose_lowest_y':metrics(base.composite(n,0)[0])['bbox'][3]-1,'current_ultimate_lowest_y':metrics(old)['bbox'][3]-1,'new_lowest_y':metrics(im)['bbox'][3]-1,'measurement_limit':'구역 내 피부 주색12/13의 범위이며 음영/윤곽 전체나 판정의 자동 증명은 아님. 접점 이동은 원그림과 함께 판단.'})
        page(pics,ult.composite(0,15)[0],out/f'{n:03}_comparison.png',cols=3,scale=5)
    write(out/'report.json',{'source_archives':{bp.relative_to(ROOT).as_posix():sha(bp.read_bytes()),up.relative_to(ROOT).as_posix():sha(up.read_bytes())},'rows':rows,'needs_local_rework_review':True,'arc_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
