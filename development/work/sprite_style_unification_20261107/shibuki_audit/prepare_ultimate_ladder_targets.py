"""Ultimate 사다리14 목표층을 검토용 고정. 원화/원자산은 변경하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page
P=H/'prepared_ultimate_dash01/PL02_U.ARC';PARENT='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb';REFS=tuple(range(143,156))+(183,)
def main():
    o=H/'ultimate_ladder_complete_targets01';need(not o.exists(),'Fresh target');need(sha(P.read_bytes())==PARENT,'Parent changed');a=Archive(P.read_bytes());o.mkdir();sources={};rows=[];pics={'before':[],'after':[]}
    def read(p):sources[p.relative_to(H).as_posix()]=sha(p.read_bytes());return np.array(Image.open(p))
    for n in REFS:
        folder='ultimate_ladder_shots_registered01'if n in(150,155)else'ultimate_ladder_contacts01';full=read(H/folder/f'before_{n:03}_indices.png');base=read(H/folder/f'after_{n:03}_indices.png');points=[]
        if n==155:
            expected=[[-13,-3,15],[-12,-2,15],[-8,-1,15]];actual=[[int(x-160),int(y-160),int(base[y,x])]for y,x in zip(*np.nonzero((base>0)&(full==0)))];need(actual==expected,'Unreviewed contour')
            for x,y,v in expected:need(a.words[v]==a.words[16+v],'Different contour color');full[y+160,x+160]=v;points.append([x,y,v])
        need(not np.any((base>0)&(full==0)),'After alpha escapes');targets={0:base,5:np.where(same_rgba(a,full,base),0,full).astype('uint8')}
        for b in(6,7,8):need(not a.layer(n,b)[0].any(),'Independent armor nonblank');targets[b]=np.zeros_like(base)
        gunproof=None
        if n in(150,155):
            s=H/'ultimate_ladder_shot_inputs01';gun=read(s/f'{n:03}_barrel_indices.png');guard=read(s/f'{n:03}_barrel_mask.png')>0
            for v in(full,base):need(np.array_equal(v[guard],gun[guard]),'Canonical gun changed');need(label(v>0,np.ones((3,3)))[1]==1,'Detached piece');need(np.any(binary_dilation(gun>0,np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard),'No fourway wrist contact')
            gunproof={'opaque':60,'transparent':11,'fourway_contact':True,'palette_both_exact':True}
        for b,v in targets.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
        for form,v,pal in [('before',full,16),('after',base,0)]:Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{form}_{n:03}.png');pics[form].append((f'{n} new {form}',im))
        rows.append({'ref':n,'source_folder':folder,'after_alpha_subset':True,'before_pixels':int((full>0).sum()),'after_pixels':int((base>0).sum()),'jacket_delta_pixels':int((targets[5]>0).sum()),'new_after_outline_preserved_in_jacket':points,'canonical_barrel':gunproof})
    for form,mask in [('before',15),('after',0)]:
        for start in range(0,len(pics[form]),6):page(pics[form][start:start+6],a.composite(0,mask)[0],o/f'{form}_comparison_{start//6:02}.png',cols=3,scale=4)
    prefixes=['ultimate_ladder_inputs01','ultimate_ladder_inputs02','ultimate_ladder_back_accessory01','ultimate_ladder_native03','ultimate_ladder_native_page02','ultimate_ladder_native_page03','ultimate_ladder151_arm_edit01','ultimate_ladder151_arm_edit02','ultimate_ladder151_arm_native02','ultimate_ladder151_arm_composed01','ultimate_ladder_common_probe02','ultimate_ladder_contacts01','ultimate_ladder_shot_inputs01','ultimate_ladder_shots_registered01']
    for folder in prefixes:
        for p in sorted((H/folder).rglob('*')):
            if p.is_file()and p.suffix in('.png','.txt','.json'):sources[p.relative_to(H).as_posix()]=sha(p.read_bytes())
    for name in('prepare_ultimate_ladder_targets.py','probe_ultimate_ladder_common.py','probe_ultimate_ladder_common02.py','prepare_ultimate_ladder_body_targets.py','compose_ladder151_arm.py','register_ultimate_ladder_shots.py'):sources[name]=sha((H/name).read_bytes())
    meta={'parent_sha256':PARENT,'refs':list(REFS),'rows':rows,'sources':sources,'source_policy':'새 원화 본체/팔과 수용34 총열만 사용. 155는 수용된 기본형처럼149몸체+다른반동팔을사용한새제작정책이며 원US155 전체반동복원이 아님.','pending':['일부발최하단1..2px 원그림대비차이 시각판단','사격 최종재추출 미술검토','원MIPS/GPU 및독립검사'],'old_coarse_body_reused':False,'palette_changed':False,'gameplay_timing_changed':False,'runtime_verified':False,'candidate_only':True};write(o/'targets.json',meta);write(o/'LOCK.json',{'target_manifest_sha256':sha((o/'targets.json').read_bytes()),'files':{p.name:sha(p.read_bytes())for p in sorted(o.glob('*.png'))},'sources':sources});print(json.dumps({'refs':len(rows),'target_layers':len(rows)*5,'lock':sha((o/'LOCK.json').read_bytes())}))
if __name__=='__main__':main()
