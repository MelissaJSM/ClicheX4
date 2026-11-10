"""원점별칭19에 새13x15 머리를 평행 등록하고 빈198/678을 보호한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_lowhp_final import compose
P=H/'prepared_hover_ultimate01/PL02_U.ARC';PARENT='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
PBS=(0,5,6,7,8);REFS=tuple(n for n in range(184,204) if n!=198);TD=H/'vehicle_head_ultimate_targets01'
def main():
    need(not TD.exists(),'목표 보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 변경');src=H/'vehicle_head_ultimate_native02';new={b:np.array(Image.open(src/f'184_bank{b}_indices.png')) for b in (0,5)};master={mask:a.composite(184,mask)[0] for mask in (0,15)};bb=master[0].getbbox();targets={};shifts=[]
    for n in REFS:
        before=a.composite(n,15)[0];after=a.composite(n,0)[0];nb=after.getbbox();dx,dy=nb[0]-bb[0],nb[1]-bb[1]
        for mask,im in ((0,after),(15,before)):need(im.crop(im.getbbox()).tobytes()==master[mask].crop(bb).tobytes(),'부모 별칭 그림 차이')
        ll={b:a.layer(n,b)[0].copy() for b in PBS};need(not any(ll[b].any() for b in (6,7,8)),'기존 빈층')
        for b in (0,5):
            out=np.zeros((384,384),np.uint8);ys,xs=np.nonzero(new[b]);out[ys+dy,xs+dx]=new[b][ys,xs];ll[b]=out
        targets[n]=ll;shifts.append({'ref':n,'translation_from184':[dx,dy],'parent_bbox_world':[v-160 for v in nb],'before_after_normalized_parent_exact':True,'new_bbox_world':[v-160 for v in compose(a,ll,0).getbbox()]})
    TD.mkdir();sources={P.relative_to(ROOT).as_posix():PARENT}
    for folder in ('vehicle_head_accessory_read01','vehicle_head_ultimate_inputs01','vehicle_head_ultimate_native01','vehicle_head_ultimate_native02'):
        for p in sorted((H/folder).rglob('*')):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in ('prepare_vehicle_head_input.py','register_vehicle_head_ultimate.py','register_vehicle_head_gold.py','prepare_vehicle_head_targets.py'):
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for n,ll in targets.items():
        for b,z in ll.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
        for form,mask in (('before',15),('after',0)):compose(a,ll,mask).save(TD/f'{form}_{n:03}.png')
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'source_files':sources,'targets':{str(n):{str(b):sha(z.tobytes()) for b,z in ll.items()} for n,ll in targets.items()},'translations':shifts,'master_ref':184,'preserve_empty_ref198':True,'preserve_existing_empty678_records':True,'source_policy':'新작화 머리1셀의13x15/눈/원점/144px를 유지하여 부모19위치에 평행등록.금색표본10개는기존색인7.귀사이1셀추가/1셀제거와before측면8셀소유는명시적새정책.기본/포스와대기자원불변.','arc_written':False,'runtime_verified':False});print(json.dumps({'manifest':sha((TD/'manifest.json').read_bytes()),'sources':len(sources),'refs':len(REFS),'layers':95}))
if __name__=='__main__':main()
