"""새 회복81/83의 머리·맨다리만 두 의상 공통으로 등록하는 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from probe_ultimate_dash_common01 import poly
HEAD={81:[(-20,-26),(18,-26),(18,3),(13,3),(10,1),(7,-1),(2,-4),(-5,-5),(-10,-4),(-20,-4)],83:[(-20,-26),(18,-26),(18,5),(8,3),(4,-1),(1,-4),(-4,-5),(-9,-4),(-20,-4)]}
THIGHS={81:[[(-10,8),(-6,8),(-4,10),(-11,10)],[(3,9),(7,9),(8,10),(1,10)]],83:[[(-9,9),(-5,9),(-4,10),(-10,10)],[(-2,10),(3,9),(4,10)]]}

def main():
    o=H/'ultimate_dash_common_probe03';need(not o.exists(),'Fresh candidate');o.mkdir();src=H/'ultimate_dash_native03';a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8)
    y,x=np.indices((384,384));rows=[];pictures={'before':[],'after':[]}
    for ref in(81,83):
        before=np.array(Image.open(src/f'before_{ref:03}_indices.png'));fresh=np.array(Image.open(src/f'after_{ref:03}_indices.png'))
        head=poly(HEAD[ref]);legs=(y>=170)|poly(THIGHS[ref][0])|poly(THIGHS[ref][1]);common=head|legs
        after=fresh.copy();after[common]=lut[before][common];need(np.array_equal(after[~common],fresh[~common]),'Costume changed outside semantic mask')
        outside=(after>0)&(before==0);points=[[int(px-160),int(py-160),int(after[py,px])]for py,px in zip(*np.nonzero(outside))]
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            Image.fromarray(v).save(o/f'{form}_{ref:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{form}_{ref:03}.png');pictures[form].extend([(f'{ref} current {form}',a.composite(ref,mask)[0]),(f'{ref} new common {form}',im)])
        for name,v in(('head',head),('legs',legs),('common',common),('outside',outside)):Image.fromarray(v.astype(np.uint8)*255).save(o/f'{ref:03}_{name}_mask.png')
        rows.append({'ref':ref,'head_polygon':HEAD[ref],'legs_start_y':10,'thigh_polygons':THIGHS[ref],'common_opaque':int(np.count_nonzero(before[common])),'changed_after_common':int(np.count_nonzero(after!=fresh)),'outside_jacket_pixels':points,'sole_before':metrics(a.rgba(before,16))['bbox'][3]-1,'sole_after':metrics(a.rgba(after,0))['bbox'][3]-1,'old_art_reused':False})
    for form,mask in(('before',15),('after',0)):page(pictures[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'source_report_sha256':sha((src/'report.json').read_bytes()),'parent_sha256':sha(a.data),'palette_mapping':lut.tolist(),'rows':rows,'candidate_only':True,'arc_written':False,'visual_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
