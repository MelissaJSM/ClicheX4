"""두 국소 새팔 donor만 의미영역 등록하고 나머지 새85/89를 보호한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
POLYS={85:[(-13,-5),(-8,-5),(-8,-4),(-6,-4),(-6,-2),(-4,-2),(-4,3),(-10,3),(-13,-1)],89:[(-15,-14),(-9,-14),(-9,-11),(-8,-11),(-8,-4),(-7,-4),(-7,-2),(-12,-2),(-15,-5)]}
def main():
    d=H/'ultimate_standing_fire_native02';need(not d.exists(),'새 등록 폴더 필요');d.mkdir();src=H/'ultimate_standing_fire_native01';a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32)
    g=H/'ultimate_standing89_arm02/generated.png';need(sha(g.read_bytes())=='b18e50a71215d82349346b48ccc76bc04b92d2cdb433c1b0d362ce9916dbf572','89원화 변경');im=Image.open(g).convert('RGBA');need(im.size==(1254,1254),'89원화 전체캔버스');sample=np.array(im.resize((96,96),Image.Resampling.NEAREST));q=(1+((sample[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');q[sample[:,:,3]<128]=0;new89=np.zeros((384,384),np.uint8);new89[112:208,112:208]=q;Image.fromarray(new89).save(d/'089_donor_indices.png');a.rgba(new89).save(d/'089_donor.png');rows=[]
    for form,pal,mask in [('before',16,15),('after',0,0)]:
        pics=[]
        for n in(85,89):
            old=np.array(Image.open(src/f'{form}_{n:03}_indices.png'));out=old.copy()
            if form=='after':
                donor=np.array(Image.open(H/'ultimate_standing_fire_sleeves_inspection01/085_donor_indices.png'))if n==85 else new89
                ri=Image.new('1',(384,384));ImageDraw.Draw(ri).polygon([(x+160,y+160)for x,y in POLYS[n]],fill=1);roi=np.array(ri,bool);out[roi]=donor[roi];need(np.array_equal(out[~roi],old[~roi]),'다른 새부위 변경')
                before=np.array(Image.open(src/f'before_{n:03}_indices.png'));outside=(out>0)&(before==0);Image.fromarray(roi.astype('uint8')*255).save(d/f'{n:03}_arm_source_mask.png');Image.fromarray((out!=old).astype('uint8')*255).save(d/f'{n:03}_arm_changed_mask.png');rows.append({'ref':n,'world_polygon':POLYS[n],'source_donor_sha256':sha(donor.tobytes()),'changed_pixels':int((out!=old).sum()),'new_alpha':int(((out>0)&(old==0)).sum()),'removed_alpha':int(((out==0)&(old>0)).sum()),'outside_new_before_pixels':[[int(x)-160,int(y)-160,int(out[y,x])]for y,x in zip(*np.nonzero(outside))],'outside_region_exact':True,'wholebody_translation':[0,0],'wholebody_resize':False})
            Image.fromarray(out).save(d/f'{form}_{n:03}_indices.png');rgba=a.rgba(out,pal);rgba.save(d/f'{form}_{n:03}.png');pics.extend([(f'{n} previous source',Image.open(src/f'{form}_{n:03}.png')),(f'{n} registered local arm',rgba)])
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=6)
    page([(f'{n} before',Image.open(d/f'before_{n:03}.png'))for n in(85,89)]+[(f'{n} after',Image.open(d/f'after_{n:03}.png'))for n in(85,89)],a.composite(0,0)[0],d/'pair_comparison.png',cols=2,scale=6)
    write(d/'report.json',{'parent_sha256':sha(a.data),'source_report_sha256':sha((src/'report.json').read_bytes()),'donor85_report_sha256':sha((H/'ultimate_standing_fire_sleeves_inspection01/report.json').read_bytes()),'donor89_receipt_sha256':sha((H/'ultimate_standing89_arm02/generation_receipt.json').read_bytes()),'rows':rows,'both_before_sources_exact':True,'all_after_outside_arm_exact':True,'front_joint_and_common_body_validation_pending':True,'canonical_buster_registration_pending':True,'arc_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
