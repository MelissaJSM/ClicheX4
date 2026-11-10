"""수용 공중34 케이싱을 손/소매 없이 분리하고 11총구에서 실제 일치 여부 조사."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from inspect_air_layers import P
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
def shift(a,dx,dy):
    v=np.zeros_like(a);yy,xx=np.nonzero(a);v[yy+dy,xx+dx]=a[yy,xx];return v
def muzzle(a):
    yy,xx=np.nonzero(a==4);mx=int(xx.min());return mx,int(yy[xx==mx].min())
def main():
    o=H/'air_barrel_guard02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());master=a.layer(34)[0];xx0,yy0=muzzle(master);yy,xx=np.indices(master.shape)
    # The native casing is purple, its own dark outline and two red muzzle
    # texels. Skin(D), sleeve cyan(6)/white(9) and red cuff(1) are excluded.
    region=(xx>=xx0-1)&(xx<=xx0+9)&(yy>=yy0-2)&(yy<=yy0+4)
    pixels=region&(np.isin(master,[2,5,8,14,15])|((master==4)&(xx==xx0)))
    barrel=np.where(pixels,master,0).astype(np.uint8);guard=np.zeros_like(pixels)
    for y in np.flatnonzero(pixels.any(1)):
        cols=np.flatnonzero(pixels[y]);guard[y,xx0-1:cols.max()+1]=True
    need(not np.any(barrel[~guard]),'Incomplete casing guard');need(set(np.unique(barrel))<={0,2,4,5,8,14,15},'Old sleeve material included')
    Image.fromarray(barrel).save(o/'master_034_indices.png');Image.fromarray(guard.astype(np.uint8)*255).save(o/'master_034_mask.png')
    rows=[];pics=[]
    for n in range(34,55,2):
        old=a.layer(n)[0];mx,my=muzzle(old);dx,dy=mx-xx0,my-yy0;gun=shift(barrel,dx,dy);mask=shift(guard.astype(np.uint8),dx,dy).astype(bool)
        diff=mask&(old!=gun);rows.append({'shot_ref':n,'body_ref':n-1,'actual_muzzle_red_top_world':[mx-160,my-160],'source_master_ref':34,'translation':[dx,dy],
          'master_index_sha256':sha(barrel.tobytes()),'casing_index_sha256':sha(gun.tobytes()),'mask_sha256':sha(mask.tobytes()),'opaque_pixels':int(np.count_nonzero(gun)),
          'existing_source_casing_diff_pixels':[[int(x)-160,int(y)-160,int(old[y,x]),int(gun[y,x])]for y,x in zip(*np.nonzero(diff))],
          'source_base_fourth_same_on_casing':bool(np.array_equal(np.array(a.composite(n,0)[0])[mask],np.array(a.composite(n,15)[0])[mask]))})
        Image.fromarray(gun).save(o/f'{n:03}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(o/f'{n:03}_mask.png');a.rgba(gun).save(o/f'{n:03}.png')
        isolated=np.where(mask,old,0).astype(np.uint8);pics.extend([(f'{n} old casing window',a.rgba(isolated)),(f'{n} exact shared casing',a.rgba(gun))])
    for k in range(0,len(pics),8):page(pics[k:k+8],a.composite(0,0)[0],o/f'comparison_{k//8:02}.png',cols=2,scale=5)
    write(o/'guard.json',{'source_arc_sha256':sha(P.read_bytes()),'existing_accepted_source_ref':34,'rows':rows,'old_skin_or_sleeve_reused':False,
          'all_muzzle_red_pixels_exact':True,'new_muzzle_position_invented':False,'not_generated':True,'resource_written':False,
          'shape_change_only_where_original_old_sleeve_occludes_casing':'차이좌표를 기록하고 후속 수용/수정 근거로 별도 검토. 지금 게임에는 적용하지 않음.'})
    print(json.dumps([(r['shot_ref'],len(r['existing_source_casing_diff_pixels']))for r in rows]))
if __name__=='__main__':main()
