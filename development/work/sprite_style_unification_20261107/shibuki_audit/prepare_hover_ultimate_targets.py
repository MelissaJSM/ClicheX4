"""Ultimate 호버 새5몸/5팔의 실제상체0·하체5·빈678을 고정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from prepare_hover_ultimate_inputs import P,PARENT,CUTS
PBS=(0,5,6,7,8);REFS=tuple(range(221,231));GROUPS=tuple((n,n+1)for n in range(221,230,2));TD=H/'hover_ultimate_targets01'
SOURCE_DIRS=('hover_ultimate_inputs01','hover_ultimate_inputs02','hover_ultimate_native01','hover_ultimate_native02','hover221_arm_inputs01','hover221_arm_native01','hover221_reach_inputs01','hover221_reach_native01','hover222_cleanup_inputs01','hover222_cleanup_native01','hover_ultimate_body_layers01','hover_ultimate_body5_contacts01','hover_ultimate_contact_sources01','hover_ultimate_shot_inputs01','hover_ultimate_shot_page01_registered01','hover_ultimate_shot_page02_registered01','hover_ultimate_shot_composed03')
SCRIPTS=('prepare_hover_ultimate_inputs.py','prepare_hover_ultimate_last.py','register_hover_ultimate_first.py','register_hover_ultimate_last.py','prepare_hover221_arm_correction.py','register_hover221_arm.py','prepare_hover221_reach.py','register_hover221_reach.py','prepare_hover222_arm_cleanup.py','register_hover222_cleanup.py','prepare_hover_ultimate_body_layers.py','prepare_hover_ultimate_contacts.py','review_hover_ultimate_body5.py','prepare_hover_ultimate_shots.py','register_hover_ultimate_shot_page.py','compose_hover_five_shots.py','prepare_hover_ultimate_targets.py')
def main():
    need(not TD.exists(),'기존목표보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');targets={};rows=[];sources={P.relative_to(ROOT).as_posix():PARENT}
    for n in REFS:
        src=H/('hover_ultimate_shot_composed03'if n%2==0 else'hover_ultimate_native02'if n==229 else'hover_ultimate_body_layers01');ll={b:np.array(Image.open(src/f'{n:03}_bank{b}_indices.png'))for b in PBS};need(all(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16 for z in ll.values()),'목표색인');need(not any(ll[b].any()for b in(6,7,8)),'빈소유층');k=n if n%2 else n-1;need(not ll[0][160+CUTS[k]:].any()and not ll[5][:160+CUTS[k]].any(),'원상하체행');targets[n]=ll
        if n%2==0:
            need(np.array_equal(ll[5],targets[n-1][5]),'사격하체변경');gd=H/'hover_ultimate_shot_inputs01';gun=np.array(Image.open(gd/f'{n:03}_barrel_indices.png'));mask=np.array(Image.open(gd/f'{n:03}_barrel_mask.png'))>0;need(np.array_equal(ll[0][mask],gun[mask]),'정본총창');rows.append({'body_ref':n-1,'shot_ref':n,'lower5_exact':True,'upper0_only_firing_region_changed':True,'canonical_guard':71,'muzzle_world':{222:[-27,-9],224:[-29,-8],226:[-20,-10],228:[-17,-10],230:[-24,-11]}[n]})
    TD.mkdir()
    for folder in SOURCE_DIRS:
        for p in sorted((H/folder).rglob('*')):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in SCRIPTS:
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for p in [H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json',H.parent/'zero_audit/shibuki_nova_hover_relations01/conclusions.json',H/'air_barrel_guard02/master_034_mask.png']:
        sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for n,ll in targets.items():
        for b,z in ll.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
        compose(a,ll,15).save(TD/f'actual_{n:03}.png')
    for i,ns in enumerate(GROUPS):page([(f'{n} actual mask15',compose(a,targets[n],15))for n in ns],a.composite(0,0)[0],TD/f'comparison_{i:02}.png',cols=2,scale=5)
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'source_files':sources,'targets':{str(n):{str(b):sha(z.tobytes())for b,z in ll.items()}for n,ll in targets.items()},'pairs':rows,'actual_hover_mask':15,'source_policy':'새5몸/사격5팔과222추가팔국소원화를등록.원상체0 CLUT0/하체5 CLUT16·빈678·원총구5·추진15위상유지.226/228의생성총은미채택하고정본총아래/뒤에새전완표본만등록.개별스케일/팔늘림없음.','arc_written':False,'runtime_verified':False,'limits':['221오른손높이잔여1px 및229높이1px차이는대기/원자세비교로검토하며원외곽exact라고주장않음.','15jet는공간진단이며실제CLUT/블렌딩·실기검증은별도.','mask0~14는엔진이호버에서쓰지않는진단조건이고그반몸표시를결함이라취급하지않음.']});print(json.dumps({'manifest':sha((TD/'manifest.json').read_bytes()),'source_files':len(sources),'layers':50}))
if __name__=='__main__':main()
