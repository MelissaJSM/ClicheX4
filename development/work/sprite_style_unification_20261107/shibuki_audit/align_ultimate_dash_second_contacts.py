"""새 여섯 대시 몸체의 원점 및 전후 공통층을 보존해 합친다."""
from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    out=H/'ultimate_dash_contacts03';need(not out.exists(),'Fresh candidate required');out.mkdir()
    a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes())
    need(sha(a.data)=='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7','Parent changed')
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
    first=H/'ultimate_dash_contacts02';second=H/'ultimate_dash_common_probe02'
    report=json.loads((second/'report.json').read_text('utf8'));rows=[];pictures={'before':[],'after':[]}
    for ref in(67,69,71,75,77,79):
        src=first if ref<75 else second
        before=np.array(Image.open(src/f'before_{ref:03}_indices.png'));after=np.array(Image.open(src/f'after_{ref:03}_indices.png'))
        points=[]
        if ref>=75:
            expected=next(r['outside_jacket_pixels']for r in report['rows']if r['ref']==ref)
            for y,x in zip(*np.nonzero((after>0)&(before==0))):
                val=int(after[y,x]);need(ref==77 and (x-160,y-160,val)==(-18,12,2),'Unreviewed contour point')
                need(np.array_equal(rgb[val],rgb[16+val]),'Contour palette mismatch');before[y,x]=val;points.append([int(x-160),int(y-160),val])
            need(points==expected,'Outside source mask changed')
        need(not np.any((after>0)&(before==0)),'After alpha escapes before')
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            rgba=a.rgba(v,pal);need(metrics(rgba)['bbox'][3]==23,'Sole y22 lost')
            Image.fromarray(v).save(out/f'{form}_{ref:03}_indices.png');rgba.save(out/f'{form}_{ref:03}.png')
            pictures[form].extend([(f'{ref} parent {form}',a.composite(ref,mask)[0]),(f'{ref} new {form}',rgba)])
        for kind in('head','legs','common'):shutil.copyfile(src/f'{ref:03}_{kind}_mask.png',out/f'{ref:03}_{kind}_mask.png')
        rows.append({'ref':ref,'source_report':(src/'report.json').relative_to(ROOT).as_posix(),'source_report_sha256':sha((src/'report.json').read_bytes()),'source_after_outline_added_to_before':points,'alpha_subset':True,'sole_y':22,'new_translation':[0,0],'rescaling':False,'old_body_reused':False})
    for form,mask in(('before',15),('after',0)):
        for start in(0,6):page(pictures[form][start:start+6],a.composite(0,mask)[0],out/f'{form}_comparison_{start//6:02}.png',cols=2,scale=5)
    write(out/'report.json',{'passed':True,'candidate_only':True,'parent_sha256':sha(a.data),'rows':rows,'palette_modified':False,'arc_written':False,'gameplay_verified':False,'scope':'새 몸체6개/두 의상12표시. 재킷 밖의 실제 새 맨손 외곽 한 점만 동일색으로 연결. 사격8개와 나머지4몸체 미완료.'})
    print(json.dumps({'out':str(out),'refs':[r['ref']for r in rows]}))
if __name__=='__main__':main()
