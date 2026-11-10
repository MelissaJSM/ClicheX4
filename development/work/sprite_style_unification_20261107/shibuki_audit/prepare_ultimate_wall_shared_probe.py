"""새 before 머리/다리와 새 after 의상 영역의 정합 후보를 만든다. 패킹 금지."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page,metrics
from register_ultimate_lowhp_pilot import move
I=H/'ultimate_wall_native02';O=H/'ultimate_wall_shared_probe01';P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
SPEC={
55:{'translation':[-1,2],'polygon':[[-15,-8],[-8,-8],[-8,-5],[-4,-4],[0,-5],[2,-7],[8,-7],[8,-3],[13,0],[13,6],[8,8],[4,6],[-2,6],[-8,6],[-12,4],[-15,1]]},
57:{'translation':[-3,2],'polygon':[[-13,-6],[-7,-6],[-7,-4],[1,-5],[5,-5],[10,-2],[11,5],[6,7],[-2,6],[-6,8],[-10,5],[-13,2]]},
59:{'translation':[-6,2],'polygon':[[-16,-9],[-10,-9],[-10,-6],[-5,-5],[2,-5],[8,-11],[14,-25],[18,-24],[18,-18],[12,-7],[10,-3],[12,3],[10,6],[4,7],[-3,6],[-10,6],[-15,3]]}}
def main():
    need(not O.exists(),'Fresh probe directory required');a=Archive(P.read_bytes());O.mkdir();results={};rows=[]
    lut=np.array([0,15,2,3,2,5,6,7,8,9,10,11,12,13,14,15],np.uint8)
    for n,spec in SPEC.items():
        before=np.array(Image.open(I/'before'/f'{n:03}_indices.png'));after=np.array(Image.open(I/'after'/f'{n:03}_indices.png'))
        shifted=move(after,*spec['translation']);pm=Image.new('1',(384,384));ImageDraw.Draw(pm).polygon([(x+160,y+160)for x,y in spec['polygon']],fill=1);mask=np.array(pm,bool)
        shared=lut[before].copy();shared[mask]=shifted[mask];results[n]=shared
        Image.fromarray(mask.astype(np.uint8)*255).save(O/f'{n:03}_body_mask.png');Image.fromarray(shared).save(O/f'{n:03}_indices.png');a.rgba(shared,0).save(O/f'{n:03}.png')
        outside=(shared>0)&(before==0);Image.fromarray(outside.astype(np.uint8)*255).save(O/f'{n:03}_outside.png')
        rows.append({'ref':n,'new_after_local_translation':spec['translation'],'body_polygon_world':spec['polygon'],'new_before_common_pixels':int(np.count_nonzero(before[~mask])),'new_after_body_pixels':int(np.count_nonzero(shared[mask])),'after_outside_before_pixels':int(outside.sum()),'common_shape_exact':True,'old_head_body_pixels_copied':0,'bbox_resize':False,'new_metrics':metrics(a.rgba(shared,0)),'not_frozen':True})
    page([(f'{n} before',a.rgba(np.array(Image.open(I/'before'/f'{n:03}_indices.png')),16))for n in SPEC]+[(f'{n} common after probe',a.rgba(results[n],0))for n in SPEC],a.composite(0,0)[0],O/'comparison.png',cols=3,scale=6)
    write(O/'registration.json',{'source_registration':str((I/'registration.json').relative_to(ROOT)),'rows':rows,'palette_lut_before_to_after':lut.tolist(),'candidate_only':True,'packed':False,'reason':'원화의 목·손 위치에 맞춘 의상 영역 평행이동 시험. 새 before 머리/다리 유지. 투명 누출이나 접합 미검증이면 채택하지 않는다.'})
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
