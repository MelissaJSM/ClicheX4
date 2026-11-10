"""새 공통 머리/다리와 네 개의 원화 외곽점,69 전신1px접지 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
    o=H/'ultimate_dash_contacts02';need(not o.exists(),'Fresh contacts');o.mkdir();src=H/'ultimate_dash_common_probe01';a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);meta=json.loads((src/'report.json').read_text('utf8'));rows=[];pics={'before':[],'after':[]}
    for n in(67,69,71):
        before=np.array(Image.open(src/f'before_{n:03}_indices.png'));after=np.array(Image.open(src/f'after_{n:03}_indices.png'));expected=next(r['outside_jacket_pixels']for r in meta['rows']if r['ref']==n);points=[]
        for y,x in zip(*np.nonzero((after>0)&(before==0))):
            val=int(after[y,x]);need(val in(2,8),'Only reviewed source contour tones allowed');need(np.array_equal(rgb[val],rgb[16+val]),'Source contour color differs between palettes');before[y,x]=val;points.append([int(x-160),int(y-160),val])
        need(points==expected,'Outside mask changed');need(not np.any((after>0)&(before==0)),'After escapes jacket');dy=1 if n==69 else 0
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            aligned=np.roll(v,dy,axis=0);need(np.array_equal(np.roll(aligned,-dy,axis=0),v),'Translation loss');Image.fromarray(aligned).save(o/f'{form}_{n:03}_indices.png');rgba=a.rgba(aligned,pal);rgba.save(o/f'{form}_{n:03}.png');need(metrics(rgba)['bbox'][3]==metrics(a.composite(n,mask)[0])['bbox'][3],'Foot height differs');pics[form].extend([(f'{n} old {form}',a.composite(n,mask)[0]),(f'{n} new {form} contacts',rgba)])
        for name in('head','legs','common'):
            im=np.array(Image.open(src/f'{n:03}_{name}_mask.png'));Image.fromarray(np.roll(im,dy,axis=0)).save(o/f'{n:03}_{name}_mask.png')
        rows.append({'ref':n,'new_after_source_outline_added_to_jacket':points,'whole_new_body_translation':[0,dy],'common_source_head_legs':True,'new_sole_y':22,'new_native_identity':'새 첫페이지 원화만 사용. 구형 머리/몸/다리 재사용 없음.','exact_translation_inverse':True,'body_scaling':False,'after_alpha_subset':True,'source_common_report_sha256':sha((src/'report.json').read_bytes())})
    for form,mask in(('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'passed':True,'candidate_only':True,'source_report_sha256':sha((src/'report.json').read_bytes()),'rows':rows,'specific_outline_pixels':sum(len(r['new_after_source_outline_added_to_jacket'])for r in rows),'old_art_reused':0,'palette_bytes_modified':False,'resource_written':False,'shot_arms_pending':True,'other7body_keys_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
