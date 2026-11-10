"""Ultimate 준비2몸체의 현수용 동일짝 정책을20층으로 전개한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_lowhp_final import compose
P=H/'prepared_chaser_ultimate01/PL02_U.ARC';PARENT='2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c'
PBS=(0,5,6,7,8);REFS=(213,214,215,216);GROUPS=((213,214),(215,216));DY={n:0 for n in REFS};TD=H/'nova_ultimate_targets01'
FOLDERS=('nova_ultimate_inputs01','nova_ultimate_native01','nova_ultimate_footwear_inputs01','nova_ultimate_footwear_native01','nova_ultimate_footwear_composed01','nova_ultimate_common01','nova_ultimate_common02')
SCRIPTS=('prepare_nova_ultimate.py','register_nova_ultimate.py','prepare_nova_ultimate_footwear.py','register_nova_ultimate_footwear.py','compose_nova_ultimate_footwear.py','probe_nova_ultimate_common.py','finalize_nova_ultimate_common.py','prepare_nova_ultimate_targets.py','register_chaser_ultimate.py','probe_nova_layers.py')
def main():
    need(not TD.exists(),'새 목표');need(sha(P.read_bytes())==PARENT,'부모 변경');a=Archive(P.read_bytes());TD.mkdir();targets={};aliases=[]
    for ns in GROUPS:
        master=ns[0];layers={b:np.array(Image.open(H/f'nova_ultimate_common02/{master:03}_bank{b}_indices.png'))for b in PBS}
        for n in ns:
            need(all(np.array_equal(a.layer(n,b)[0],a.layer(master,b)[0])for b in PBS),'현재 동일짝 변경')
            aliases.append({'ref':n,'master':master,'dy':0,'current_parent_all5_exact':True,'policy':'현재 수용 동일몸체 정책 유지. 원US 213/214·215/216은 별도 자세이므로 원작 완전복원 주장 없음.'});targets[n]=layers
            for b,z in layers.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
            for form,m in(('after',0),('before',15)):compose(a,layers,m).save(TD/f'{form}_{n:03}.png')
    sources={}
    for folder in FOLDERS:
        for p in sorted((H/folder).iterdir()):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in SCRIPTS:
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    relation=H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json';sources[relation.relative_to(ROOT).as_posix()]=sha(relation.read_bytes())
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'source_files':sources,'aliases':aliases,'targets':{str(n):{str(b):sha(z.tobytes())for b,z in layers.items()}for n,layers in targets.items()},'policy':'새2몸체×Ultimate 전후4표시, 종아리 국소 donor와 첫새발 exact/공통머리·손발·동색외곽1셀→20층. 213214/215216 현재 동일표시 정책 유지.217이후 강제mask15/효과는 별도 미제작.','arc_written':False,'runtime_verified':False,'no_new_art_for_217_230_claimed':True})
    print(json.dumps({'manifest':sha((TD/'manifest.json').read_bytes()),'inputs':len(sources),'layers':20}))
if __name__=='__main__':main()
