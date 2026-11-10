"""교정된 맨팔93와94에서 새 머리·다리 공통화 및 공중 기준점을 확인."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from probe_ultimate_dash_common01 import poly
HEAD={93:[(-20,-27),(16,-27),(16,1),(10,1),(5,-3),(0,-5),(-2,-4),(-5,-4),(-7,-5),(-10,-5),(-11,-8),(-13,-11),(-20,-12)],94:[(-22,-20),(18,-20),(18,8),(12,8),(9,5),(3,3),(-2,3),(-6,4),(-10,3),(-13,1),(-22,1)]}
THIGHS={93:[[(-10,5),(-7,5),(-3,7),(-2,9),(-10,9)]],94:[[(-9,13),(-5,13),(-3,15),(-9,15)],[(3,13),(7,13),(8,15),(1,15)]]}
def main():
    o=H/'ultimate_dash_common_probe04';need(not o.exists(),'Fresh candidate');o.mkdir();src=H/'ultimate_dash_native04';a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());pose=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);y,x=np.indices((384,384));rows=[];pics={'before':[],'after':[]}
    for ref in(93,94):
        before=np.array(Image.open(src/f'before_{ref:03}_indices.png'));after_path=H/'ultimate_dash93_barearm_native02/after_indices.png'if ref==93 else src/f'after_{ref:03}_indices.png';fresh=np.array(Image.open(after_path));head=poly(HEAD[ref]);legs=y>=160+(8 if ref==93 else 14)
        for points in THIGHS[ref]:legs|=poly(points)
        common=head|legs
        if ref==93:
            arm=np.array(Image.open(H/'ultimate_dash93_barearm_native02/arm_mask.png'))>0;common&=~arm;head&=~arm;legs&=~arm
        after=fresh.copy();after[common]=lut[before][common];need(np.array_equal(after[~common],fresh[~common]),'Costume changed outside mask')
        outside=(after>0)&(before==0);points=[[int(px-160),int(py-160),int(after[py,px])]for py,px in zip(*np.nonzero(outside))];dy=1 if ref==94 else 0
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            aligned=np.roll(v,dy,axis=0);need(np.array_equal(np.roll(aligned,-dy,axis=0),v),'Lost translation');Image.fromarray(aligned).save(o/f'{form}_{ref:03}_indices.png');im=a.rgba(aligned,pal);im.save(o/f'{form}_{ref:03}.png');need(metrics(im)['bbox'][3]==metrics(pose.composite(ref,0)[0])['bbox'][3],'Pose sole differs');pics[form].extend([(f'{ref} parent {form}',a.composite(ref,mask)[0]),(f'{ref} new common {form}',im)])
        for name,v in(('head',head),('legs',legs),('common',common),('outside',outside)):Image.fromarray(np.roll(v,dy,axis=0).astype(np.uint8)*255).save(o/f'{ref:03}_{name}_mask.png')
        rows.append({'ref':ref,'head_polygon':HEAD[ref],'thigh_polygons':THIGHS[ref],'common_pixels':int(np.count_nonzero(before[common])),'changed_after_common':int(np.count_nonzero(after!=fresh)),'outside_jacket_pixels_untranslated':points,'outside_jacket_pixels':[[xx,yy+dy,v]for xx,yy,v in points],'whole_new_pose_translation':[0,dy],'sole_y':metrics(pose.composite(ref,0)[0])['bbox'][3]-1,'new_after_source':after_path.relative_to(ROOT).as_posix(),'new_after_source_sha256':sha(after_path.read_bytes()),'old_art_reused':False})
    for form,mask in(('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'parent_sha256':sha(a.data),'source_report_sha256':sha((src/'report.json').read_bytes()),'palette_mapping':lut.tolist(),'rows':rows,'candidate_only':True,'arc_written':False,'visual_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
