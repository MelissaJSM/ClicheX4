"""builtin 국소 소매의 표본을 같은 좌표에 등록하고 나머지 새 그림을 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
POLYGONS={85:[(-12,-6),(-8,-6),(-8,-4),(-7,-2),(-7,4),(-9,7),(-11,6),(-12,1)],89:[(-13,-14),(-8,-14),(-7,-15),(-7,-12),(-8,-11),(-8,-6),(-7,-4),(-9,-2),(-11,-4),(-13,-8)]}
def main():
    d=H/'standing_fire_native02';need(not d.exists(),'Fresh local registration');d.mkdir()
    a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());src=H/'standing_fire_native01';don=H/'standing_fire_sleeves_inspection01';rows=[]
    for form,pal,mask in [('base',0,0),('fourth',16,15)]:
        pics=[]
        for n in(85,89):
            old=np.array(Image.open(src/f'{form}_{n:03}_indices.png'));out=old.copy()
            if form=='fourth':
                donor=np.array(Image.open(don/f'{n:03}_donor_indices.png'));roiim=Image.new('1',(384,384));ImageDraw.Draw(roiim).polygon([(x+160,y+160)for x,y in POLYGONS[n]],fill=1);roi=np.array(roiim,dtype=bool)
                use=roi&(old>0)&(donor>0);out[use]=donor[use]
                need(np.array_equal(out>0,old>0),'Silhouette changed');need(np.array_equal(out[~roi],old[~roi]),'Outside changed')
                Image.fromarray(roi.astype('uint8')*255).save(d/f'{n:03}_sleeve_region.png');Image.fromarray(use.astype('uint8')*255).save(d/f'{n:03}_donor_sample_mask.png');Image.fromarray((out!=old).astype('uint8')*255).save(d/f'{n:03}_changed_mask.png')
                rows.append({'ref':n,'source_palette':16,'world_polygon':POLYGONS[n],'sampled_pixels':int(use.sum()),'changed_pixels':int((out!=old).sum()),'unmatched_source_outline_kept':[[int(x)-160,int(y)-160,int(old[y,x])]for y,x in zip(*np.nonzero(roi&(old>0)&(donor==0)))],'alpha_exact':True,'outside_region_exact':True,'donor_indices_sha256':sha(donor.tobytes()),'result_indices_sha256':sha(out.tobytes())})
            Image.fromarray(out).save(d/f'{form}_{n:03}_indices.png');im=a.rgba(out,pal);im.save(d/f'{form}_{n:03}.png');pics.extend([(f'{n} original',a.composite(n,mask)[0]),(f'{n} new',im)])
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    page([(f'{n} first sleeve',Image.open(src/f'fourth_{n:03}.png'))for n in(85,89)]+[(f'{n} corrected sleeve',Image.open(d/f'fourth_{n:03}.png'))for n in(85,89)],a.composite(0,15)[0],d/'sleeve_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'source_native':{'path':(src/'report.json').relative_to(ROOT).as_posix(),'sha256':sha((src/'report.json').read_bytes())},'donor_report':{'path':(don/'report.json').relative_to(ROOT).as_posix(),'sha256':sha((don/'report.json').read_bytes())},'rows':rows,'basic_two_exact':True,'all_four_alpha_unchanged':True,'head_torso_buster_feet_outside_masks_exact':True,'full_body_resize':False,'old_pose_detail_copied':False,'arc_written':False,'muzzle_contacts_and_shared_layers_pending':True})
    print(json.dumps(rows))
if __name__=='__main__':main()
