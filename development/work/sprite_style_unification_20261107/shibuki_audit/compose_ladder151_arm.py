"""151의 새 낮은 팔/가림 경계만 두 번째 국소 원화로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from audit_ultimate_ladder_contacts import box
POLYGON=[(8,-15),(18,-15),(18,7),(8,7),(7,4),(5,2),(5,-3),(6,-6),(7,-8),(8,-10)]
def main():
    out=H/'ultimate_ladder151_arm_composed01';need(not out.exists(),'Fresh output');out.mkdir()
    olddir=H/'ultimate_ladder_native_page02';newdir=H/'ultimate_ladder151_arm_native02';a=Archive((H/'prepared_ultimate_dash01/PL02_U.ARC').read_bytes());b=Archive((H/'prepared_base_run01/PL00_U.ARC').read_bytes())
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in POLYGON],fill=1);allowed=np.array(im,bool);rows=[];pics=[]
    for form,pal,mask in [('before',16,15),('after',0,0)]:
        old=np.array(Image.open(olddir/f'{form}_151_indices.png'));donor=np.array(Image.open(newdir/f'{form}_151_indices.png'));v=old.copy();v[allowed]=donor[allowed]
        need(np.array_equal(old[~allowed],v[~allowed]),'Nonlocal changed');Image.fromarray(v).save(out/f'{form}_151_indices.png');rgba=a.rgba(v,pal);rgba.save(out/f'{form}_151.png');Image.fromarray((v!=old).astype('uint8')*255).save(out/f'{form}_151_changed.png')
        pics.extend([(form+' accepted joint',b.composite(151,0)[0]),(form+' first low arm',a.rgba(old,pal)),(form+' local arm correction',rgba)])
        target=b.layer(151)[0];roi=np.zeros_like(v,bool);roi[145:153,167:179]=True;overlap=np.isin(target,[12,13])&np.isin(v,[12,13])&roi
        rows.append({'form':form,'changed_pixels':int(np.count_nonzero(v!=old)),'nonlocal_exact':True,'new_hand_region_bbox':box(v,(7,-16,18,-1)),'accepted_hand_region_bbox':box(target,(7,-16,18,-1)),'flesh_hand_contact_overlap_pixels':int(overlap.sum()),'full_hand_bbox_exact':False,'alignment_note':'첫 원화의6px 낮은 손과 달리 원 손 피부 좌표와 중첩한다. 새 주먹 모양의 전체 외곽·피부상자는 원본과 다르며 이것을 동일이라고 주장하지 않는다.'})
    Image.fromarray(allowed.astype('uint8')*255).save(out/'allowed_region.png');page(pics,a.composite(0,15)[0],out/'comparison.png',cols=3,scale=6)
    write(out/'report.json',{'source_native':olddir.relative_to(ROOT).as_posix(),'source_native_sha256':{f.name:sha(f.read_bytes())for f in olddir.glob('*151_indices.png')},'donor_native_sha256':{f.name:sha(f.read_bytes())for f in newdir.glob('*151_indices.png')},'donor_generation_sha256':'7b6af94e0c3170ae86a2048857d3fac1e08620e1ac2bb3fca0948e1ed067ba0e','polygon':POLYGON,'rows':rows,'whole_body_translated':False,'new_pixels_only':True,'old_coarse_pixels_reused':False,'palette_unchanged':True,'arc_written':False,'common_and_sole_registration_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
