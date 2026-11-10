"""새 대시10몸체 후보를 합친다. 93소매의 실제 원화 외곽2셀을 보존."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    out=H/'ultimate_dash_contacts05';need(not out.exists(),'Fresh candidate');out.mkdir();previous=H/'ultimate_dash_contacts04';src=H/'ultimate_dash_common_probe04';a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());meta=json.loads((previous/'report.json').read_text('utf8'));newmeta=json.loads((src/'report.json').read_text('utf8'));need(meta['parent_sha256']==newmeta['parent_sha256']==sha(a.data),'Parent changed');rows=list(meta['rows'])
    for row in rows:
        n=row['ref']
        for form in('before','after'):
            for suffix in('.png','_indices.png'):shutil.copyfile(previous/f'{form}_{n:03}{suffix}',out/f'{form}_{n:03}{suffix}')
        for kind in('head','legs','common'):shutil.copyfile(previous/f'{n:03}_{kind}_mask.png',out/f'{n:03}_{kind}_mask.png')
    source=H/'ultimate_dash_inputs01/page04/generated.png';need(sha(source.read_bytes())=='8276860eddc45ba5e398e2251b27b2a105b2e8dfd146a26972db908223a04634','Source changed');raw=np.array(Image.open(source).convert('RGBA'));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.int32)
    for n in(93,94):
        before=np.array(Image.open(src/f'before_{n:03}_indices.png'));after=np.array(Image.open(src/f'after_{n:03}_indices.png'));outside=[(int(x-160),int(y-160),int(after[y,x]))for y,x in zip(*np.nonzero((after>0)&(before==0)))];need(outside==([(-15,-4,11),(-14,-3,4)]if n==93 else []),'Unreviewed outside');edges=[]
        for(x,y,_),expected_count in zip(outside,(22,16)):
            cell=raw[(y+36)*8:(y+37)*8,(x+32)*8:(x+33)*8];opaque=cell[:,:,3]>=128;need(int(opaque.sum())==expected_count,'Source edge coverage changed');q=1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2);vals,cnt=np.unique(q[opaque],return_counts=True);idx=int(vals[cnt.argmax()]);need(idx==15,'Original generated jacket contour changed');before[y+160,x+160]=idx;edges.append({'world':[x,y],'source_cell':[int((x+32)*8),int((y+36)*8),8,8],'opaque_samples':expected_count,'total_samples':64,'selected_source_mode_index':idx,'source_histogram':dict(zip(map(str,vals),map(int,cnt)))})
        need(not np.any((after>0)&(before==0)),'Alpha subset failed')
        for form,v,pal in(('before',before,16),('after',after,0)):
            rgba=a.rgba(v,pal);need(metrics(rgba)['bbox'][3]-1==(19 if n==93 else 24),'Foot coordinate changed');Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');rgba.save(out/f'{form}_{n:03}.png')
        for kind in('head','legs','common'):shutil.copyfile(src/f'{n:03}_{kind}_mask.png',out/f'{n:03}_{kind}_mask.png')
        nr=next(r for r in newmeta['rows']if r['ref']==n);rows.append({'ref':n,'source_report':(src/'report.json').relative_to(ROOT).as_posix(),'source_report_sha256':sha((src/'report.json').read_bytes()),'source_jacket_contour_sampling':edges,'source_after_outline_added_to_before':[],'alpha_subset':True,'sole_y':nr['sole_y'],'new_translation':nr['whole_new_pose_translation'],'rescaling':False,'old_body_reused':False})
    for form,mask in(('before',15),('after',0)):
        pics=[(f'{r["ref"]} new {form}',Image.open(out/f'{form}_{r["ref"]:03}.png').convert('RGBA'))for r in rows]
        for start in(0,5):page(pics[start:start+5],a.composite(0,mask)[0],out/f'{form}_all_{start//5:02}.png',cols=3,scale=4)
        pics=[]
        for n in(93,94):pics.extend([(f'{n} parent {form}',a.composite(n,mask)[0]),(f'{n} new {form}',Image.open(out/f'{form}_{n:03}.png').convert('RGBA'))])
        page(pics,a.composite(0,mask)[0],out/f'{form}_new_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'passed':True,'candidate_only':True,'parent_sha256':sha(a.data),'previous_report_sha256':sha((previous/'report.json').read_bytes()),'rows':rows,'refs':sorted(r['ref']for r in rows),'palette_modified':False,'arc_written':False,'gameplay_verified':False,'source_jacket_edge_policy':'93 source jacket edge: two native cells use the modal opaque source color, with 22/64 and 16/64 actual samples. No old-art or uniform skin fill.','scope':'새몸체10/두의상20 후보. 기존8몸체 불변. 93 맨팔 국소교정·94 전체신규자세1px 접점이동. 사격16표시와 최종패킹 미완료.'});print(json.dumps({'refs':len(rows),'source_edge_samples':[22,16],'out':str(out)}))
if __name__=='__main__':main()
