"""90의 새 맨팔만 의미영역에 등록하고 다른 새픽셀은 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
POLY=[(-14,-14),(-11,-14),(-12,-12),(-12,-6),(-10,-4),(-10,-2),(-14,-3),(-17,-5),(-18,-9),(-17,-12),(-15,-13)]
def main():
    s=H/'ultimate_standing_followthrough_native01';q=H/'ultimate_standing90_arm_inspection01';d=H/'ultimate_standing_followthrough_native02';need(not d.exists(),'새 출력 필요');d.mkdir();a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());donor=np.array(Image.open(q/'donor_indices.png'));mm=Image.new('1',(384,384));ImageDraw.Draw(mm).polygon([(x+160,y+160)for x,y in POLY],fill=1);mask=np.array(mm,bool);guard=np.array(Image.open(H/'standing_fire_modules_probe02/090_gun_guard.png'))>0;mask&=~guard;Image.fromarray(mask.astype('uint8')*255).save(d/'090_arm_mask.png');rows=[]
    for form,pal,am in [('before',16,15),('after',0,0)]:
        pics=[]
        for n in(90,91):
            old=np.array(Image.open(s/f'{form}_{n:03}_indices.png'));new=old.copy()
            if form=='after'and n==90:new[mask]=donor[mask]
            need(np.array_equal(old[~mask],new[~mask]),'팔 밖 변경');need(np.array_equal(new[guard],old[guard]),'총 영역 변경')
            im=a.rgba(new,pal);Image.fromarray(new).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');pics.extend([(f'{n} 첫원화',a.rgba(old,pal)),(f'{n} 팔 정합',im)]);labs,_=label(new>0,np.ones((3,3)))
            rows.append({'ref':n,'form':form,'changed_pixels':int((new!=old).sum()),'alpha_added':int(((new>0)&(old==0)).sum()),'alpha_removed':int(((new==0)&(old>0)).sum()),'outside_arm_exact':True,'gun_guard_exact':True,'components':sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True),'metrics':metrics(im)})
        page(pics,a.composite(0,am)[0],d/f'{form}_comparison.png',cols=2,scale=6)
    write(d/'report.json',{'source_report_sha256':sha((s/'report.json').read_bytes()),'donor_report_sha256':sha((q/'report.json').read_bytes()),'donor_source_sha256':sha((H/'ultimate_standing90_arm01/generated.png').read_bytes()),'polygon':POLY,'gun_mask_source':'standing_fire_modules_probe02/090_gun_guard.png','rows':rows,'old_head_copied':False,'body_scale_changed':False,'common_parts_pending':True,'arc_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
