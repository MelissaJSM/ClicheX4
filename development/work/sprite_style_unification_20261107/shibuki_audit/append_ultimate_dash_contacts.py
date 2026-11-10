"""검토한 새 공통층을 누적 후보에 추가한다. 그림 확대/옛 몸체 복사 없음."""
from pathlib import Path
import sys,json,argparse,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
REVIEWED_POINTS={81:[],83:[[5,9,15]]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--previous',required=True);p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--refs',nargs='+',type=int,required=True);z=p.parse_args()
    out=(H/z.out).resolve();need(out.is_relative_to(H.resolve())and not out.exists(),'Fresh own destination');out.mkdir()
    previous=H/z.previous;src=H/z.source;before_report=json.loads((previous/'report.json').read_text('utf8'));new_report=json.loads((src/'report.json').read_text('utf8'))
    a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());need(sha(a.data)==before_report['parent_sha256']==new_report['parent_sha256'],'Parent mismatch')
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);rows=list(before_report['rows']);existing=[r['ref']for r in rows];need(not set(existing)&set(z.refs),'Repeated refs')
    for ref in existing:
        for form in('before','after'):
            for suffix in('.png','_indices.png'):shutil.copyfile(previous/f'{form}_{ref:03}{suffix}',out/f'{form}_{ref:03}{suffix}')
        for name in('head','legs','common'):shutil.copyfile(previous/f'{ref:03}_{name}_mask.png',out/f'{ref:03}_{name}_mask.png')
    for ref in z.refs:
        before=np.array(Image.open(src/f'before_{ref:03}_indices.png'));after=np.array(Image.open(src/f'after_{ref:03}_indices.png'));points=[]
        expected=next(r['outside_jacket_pixels']for r in new_report['rows']if r['ref']==ref)
        need(expected==REVIEWED_POINTS[ref],'Unreviewed source outline')
        for y,x in zip(*np.nonzero((after>0)&(before==0))):
            val=int(after[y,x]);need(np.array_equal(rgb[val],rgb[16+val]),'Palette color mismatch');before[y,x]=val;points.append([int(x-160),int(y-160),val])
        need(points==expected,'Outside changed');need(not np.any((after>0)&(before==0)),'Alpha mismatch')
        for form,v,pal in(('before',before,16),('after',after,0)):
            rgba=a.rgba(v,pal);need(metrics(rgba)['bbox'][3]==23,'Unexpected sole y');Image.fromarray(v).save(out/f'{form}_{ref:03}_indices.png');rgba.save(out/f'{form}_{ref:03}.png')
        for name in('head','legs','common'):shutil.copyfile(src/f'{ref:03}_{name}_mask.png',out/f'{ref:03}_{name}_mask.png')
        rows.append({'ref':ref,'source_report':(src/'report.json').relative_to(ROOT).as_posix(),'source_report_sha256':sha((src/'report.json').read_bytes()),'source_after_outline_added_to_before':points,'alpha_subset':True,'sole_y':22,'new_translation':[0,0],'rescaling':False,'old_body_reused':False})
    for form,mask in(('before',15),('after',0)):
        pics=[]
        for ref in z.refs:pics.extend([(f'{ref} parent {form}',a.composite(ref,mask)[0]),(f'{ref} new {form}',Image.open(out/f'{form}_{ref:03}.png').convert('RGBA'))])
        page(pics,a.composite(0,mask)[0],out/f'{form}_new_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'passed':True,'candidate_only':True,'parent_sha256':sha(a.data),'previous_report_sha256':sha((previous/'report.json').read_bytes()),'rows':rows,'palette_modified':False,'arc_written':False,'gameplay_verified':False,'scope':'새 공통 머리·다리와 두 의상 누적 후보. 이전 정합 픽셀 그대로 유지. 최종 패킹/총구/부분층 검사는 후속.'});print(json.dumps({'refs':[r['ref']for r in rows],'out':str(out)}))
if __name__=='__main__':main()
