"""공중11키의 새 전후 몸체를 원래 발 높이에 등록한다. 사격팔/자원은 아직 미완성."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
REFS=(33,35,37,39,41,43,45,47,49,51,53)
def main():
    out=H/'ultimate_air_contacts02';need(not out.exists(),'Fresh output');out.mkdir();parent=H/'prepared_rising_right_ultimate01/PL02_U.ARC';a=Archive(parent.read_bytes());need(sha(a.data)=='d636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d','Current parent changed');rows=[]
    for form,mask,pal in(('before',15,16),('after',0,0)):
        pics=[]
        for n in REFS:
            folder='ultimate_air_contacts01'if n<45 else'ultimate_air_common_probe05';filename=f'{form}_{n:03}_indices.png'if n<45 else f'{form}_{n}_indices.png';source=H/folder/filename;v=np.array(Image.open(source));delta=1 if n==47 else 0
            if delta:v=np.roll(v,delta,axis=0)
            old=a.composite(n,mask)[0];now=a.rgba(v,pal);oldy=int(np.nonzero(np.array(old)[:,:,3])[0].max()-160);newy=int(np.nonzero(v)[0].max()-160);need(oldy==newy,f'Wrong sole y{form}/{n}')
            Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');now.save(out/f'{form}_{n:03}.png');pics.extend([(f'{n} current',old),(f'{n} registered new {form}',now)])
            rows.append({'form':form,'ref':n,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source.read_bytes()),'additional_whole_pose_translation':[0,delta],'foot_y_before':oldy,'foot_y_after':newy,'new_metrics':metrics(now),'shot_pair':n+1,'shot_arm_pending':True,'nonshot_backarm_joint_review_pending':n in(51,53),'body_segment_scaling':False})
        for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,mask)[0],out/f'{form}_comparison_{i//6:02}.png',cols=2,scale=5)
    subsets=[]
    for n in REFS:
        before=np.array(Image.open(out/f'before_{n:03}_indices.png'));after=np.array(Image.open(out/f'after_{n:03}_indices.png'));p=np.column_stack(np.nonzero((after>0)&(before==0)));need(len(p)==0,'After outside jacket');subsets.append({'ref':n,'after_alpha_subset':True})
    write(out/'report.json',{'candidate_only':True,'parent_sha256':sha(a.data),'rows':rows,'subset_checks':subsets,'all_nonshot_22_sole_heights_exact':True,'source_newbody_all_11_present':True,'shot11_not_created':True,'resource_written':False,'gameplay_verified':False,'user_accepted':False});print(json.dumps({'rows':len(rows),'subsets':len(subsets),'unresolved_nonshot_arms':[51,53]}))
if __name__=='__main__':main()
