"""새92의 단색 부츠를 같은좌표/실루엣의 새86 부츠 표본으로만 등록한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def main():
    s=H/'standing_fire_recovery_native01';d=H/'standing_fire_recovery_native02';need(not d.exists(),'Fresh output');a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());roi=np.zeros((384,384),bool);roi[176:184,144:160]=True
    old86=np.array(a.composite(86,0)[0]);old92=np.array(a.composite(92,0)[0]);need(np.array_equal(old86[roi],old92[roi]),'Old base boot pose differs')
    donor=np.array(Image.open(s/'fourth_086_indices.png'));source=np.array(Image.open(s/'fourth_092_indices.png'));need(np.array_equal(donor[roi]>0,source[roi]>0),'New boot silhouette differs');out=source.copy();out[roi]=donor[roi];need(np.array_equal(out>0,source>0),'Alpha changed');need(np.array_equal(out[~roi],source[~roi]),'Outside changed')
    d.mkdir()
    for form,pal,mask in [('base',0,0),('fourth',16,15)]:
        pics=[]
        for n in(86,87,92):
            idx=out if(form,n)==('fourth',92)else np.array(Image.open(s/f'{form}_{n:03}_indices.png'));Image.fromarray(idx).save(d/f'{form}_{n:03}_indices.png');im=a.rgba(idx,pal);im.save(d/f'{form}_{n:03}.png');pics.extend([(f'{n} old',a.composite(n,mask)[0]),(f'{n} new',im)])
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    Image.fromarray(roi.astype('uint8')*255).save(d/'092_boot_source_region.png');Image.fromarray((out!=source).astype('uint8')*255).save(d/'092_boot_changes.png');page([('86 new source',a.rgba(donor,16)),('92 first source',a.rgba(source,16)),('92 same-position boot',a.rgba(out,16))],a.composite(0,15)[0],d/'boot_comparison.png',cols=3,scale=6)
    write(d/'report.json',{'source_report_sha256':sha((s/'report.json').read_bytes()),'source_generated_sha256':'51071699e3240001d779aa6c9e762cb97b4ba20080f8a5300df0c5a075541efb','source_ref':86,'target_ref':92,'form':'fourth','same_position_world_region':[-16,16,0,24],'source_raw_indices_sha256':sha(donor.tobytes()),'before_indices_sha256':sha(source.tobytes()),'after_indices_sha256':sha(out.tobytes()),'changed_pixels':int((out!=source).sum()),'historical_base_boot_RGBA_exact':True,'historical_fourth_boot_RGBA_exact':False,'new_boot_alpha_exact':True,'outside_region_exact':True,'all_other_five_images_exact':True,'policy':'같은좌표/방향/실루엣인 새86 부츠 표본을 새92에 재사용. 원래포스 전체명암 동일성 주장이 아니며 옛단순부츠를 복사하지 않는다.','no_resize_translation_or_new_drawing':True,'arc_written':False,'final_partial_ownership_pending':True});print(d)
if __name__=='__main__':main()
