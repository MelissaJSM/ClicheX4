"""새 공중 여섯 몸체를 전신 평행이동만으로 원래 발바닥 높이에 등록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
def main():
    out=H/'ultimate_air_contacts01';need(not out.exists(),'Fresh candidate only');out.mkdir();a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes());source=H/'ultimate_air_common_probe03';rows=[]
    for form,mask,pal in(('before',15,16),('after',0,0)):
        pics=[]
        for n in(33,35,37,39,41,43):
            v=np.array(Image.open(source/f'{form}_{n:03}_indices.png'));old=a.composite(n,mask)[0];oldbottom=metrics(old)['bbox'][3];newbottom=metrics(a.rgba(v,pal))['bbox'][3];dy=oldbottom-newbottom;need(dy in(0,1),'Unexpected pose anchoring change');new=np.roll(v,dy,axis=0);need(np.count_nonzero(new)==np.count_nonzero(v),'Translation clipped source');need(np.array_equal(np.roll(new,-dy,axis=0),v),'Source geometry changed');im=a.rgba(new,pal);Image.fromarray(new).save(out/f'{form}_{n:03}_indices.png');im.save(out/f'{form}_{n:03}.png');need(metrics(im)['bbox'][3]==oldbottom,'Foot height mismatch');pics.extend([(f'{n} previous world origin',old),(f'{n} new foot-registered',im)]);rows.append({'form':form,'ref':n,'source_native_sha256':sha(v.tobytes()),'after_native_sha256':sha(new.tobytes()),'whole_new_body_translation':[0,dy],'source_geometry_and_indices_exact_under_translation':True,'old_pixels_copied':0,'old':metrics(old),'new':metrics(im),'foot_bottom_exact':True,'nonshooting_hand_position_role':'새 포즈의 손은 몸 전체와 같은 0/1px 이동. 원래 손의 개별 픽셀 좌표 완전동일은 주장하지 않으며 최종 사격 총구는 별도 엄수한다.'})
        for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,mask)[0],out/f'{form}_comparison_{i//6:02}.png',cols=2,scale=5)
    for n in(33,35,37,39,41,43):
        b=np.array(Image.open(out/f'before_{n:03}_indices.png'));c=np.array(Image.open(out/f'after_{n:03}_indices.png'));need(not np.any((c>0)&(b==0)),'Post-translation common alpha mismatch')
    write(out/'report.json',{'passed':True,'candidate_only':True,'source':'ultimate_air_common_probe03','source_report_sha256':sha((source/'report.json').read_bytes()),'parent_sha256':sha(a.data),'rows':rows,'whole_body_scaling':False,'local_limb_scaling':False,'source_to_foot_reference_only':True,'shot_arms_pending':True,'actual_gameplay_test':False,'arc_written':False});print(json.dumps([{'form':r['form'],'ref':r['ref'],'shift':r['whole_new_body_translation']}for r in rows]))
if __name__=='__main__':main()
