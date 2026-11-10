"""후반 벽의 새 머리/손/발을 공유하고 새 민소매 의상과 팔만 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from register_ultimate_lowhp_pilot import move

B=H/'ultimate_wall_raised_native01';A=H/'ultimate_wall_page02_after_native01';O=H/'ultimate_wall_page02_shared01'
LUT=np.array([0,15,2,3,2,5,6,7,8,9,10,11,12,13,14,15],np.uint8)

def main():
    need(not O.exists(),'Fresh output required');O.mkdir()
    arc=Archive((H/'prepared_ultimate_lowhp01/PL02_U.ARC').read_bytes());rows=[];targets={}
    for n in (61,63,65):
        before=np.array(Image.open(B/f'{n:03}_indices.png'));source=np.array(Image.open(A/f'{n:03}_indices.png'));after=move(source,0,-1)
        polygon=[(-11,-10),(-3,-10),(-1,-6),(3,-7),(7,-12),(10,-23),(10,-32),(21,-32),(23,-16),(16,-8),(13,-1),(16,5),(10,8),(1,8),(-7,7),(-11,1)]
        pm=Image.new('1',(384,384));ImageDraw.Draw(pm).polygon([(x+160,y+160)for x,y in polygon],fill=1);mask=np.array(pm,bool)
        head=np.array(Image.open(B/f'{n:03}_head_mask.png'))>0;hand=np.array(Image.open(B/f'{n:03}_hand_mask.png'))>0
        protected=head|hand;protected[167:]=True
        mask &= ~protected
        target=LUT[before].copy();target[mask]=after[mask];targets[n]=target
        outside=(target>0)&(before==0)
        for label,q in [('indices',target),('body_mask',mask.astype(np.uint8)*255),('common_mask',protected.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)]:Image.fromarray(q).save(O/f'{n:03}_{label}.png')
        arc.rgba(target).save(O/f'{n:03}.png')
        yy,xx=np.nonzero(outside)
        rows.append({'ref':n,'new_after_local_translation':[0,-1],'after_outside_before':int(outside.sum()),'outside_world_pixels':[[int(x-160),int(y-160),int(target[y,x])]for y,x in zip(yy,xx)],'new_common_head_hand_legs_exact':bool(np.array_equal(target[protected],LUT[before][protected])),'new_common_pixels':int(np.count_nonzero(before[~mask])),'new_after_arm_torso_pixels':int(np.count_nonzero(target[mask])),'old_head_body_pixels_used':0,'metrics':metrics(arc.rgba(target))})
    page([(f'{n} new jacket',arc.rgba(np.array(Image.open(B/f'{n:03}_indices.png')),16))for n in targets]+[(f'{n} new shared after',arc.rgba(q))for n,q in targets.items()],arc.composite(0,0)[0],O/'comparison.png',cols=3,scale=6)
    write(O/'registration.json',{'rows':rows,'new_after_source_sha256':sha((H/'ultimate_wall_page02_after01/generated.png').read_bytes()),'palette_lut':LUT.tolist(),'candidate_only':True,'packed':False,'reason':'새 재킷의 머리·손·다리를 보존하고 의상과 팔만 새 민소매 원화에서 같은 기준점으로 등록한다.','runtime_verified':False})
    print(rows)

if __name__=='__main__':main()
