"""현재 수용 동일그림 정책으로213/214·215/216의20층을 고정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_lowhp_final import compose
P=H/'prepared_chaser_base01/PL00_U.ARC';PARENT='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'
PBS=(0,5,6,7,8);REFS=(213,214,215,216);GROUPS=((213,214),(215,216));DY={n:0 for n in REFS};TD=H/'nova_base_targets01'
FOLDERS=('nova_base_inputs01','nova_base_native01','nova_fourth_costume_inputs01','nova_fourth_costume_native01','nova_fourth_costume_composed01','nova_layers_probe01','nova_layers_final01')
SCRIPTS=('prepare_nova_base.py','register_nova_base.py','prepare_nova_fourth_costume.py','register_nova_fourth_costume.py','compose_nova_fourth_costume.py','probe_nova_layers.py','register_nova_layer_edges.py','prepare_nova_base_targets.py')
def main():
    need(not TD.exists(),'새 목표');need(sha(P.read_bytes())==PARENT,'부모변경');a=Archive(P.read_bytes());original=Archive((H/'chaser_sources01/original_base.ARC').read_bytes());TD.mkdir();targets={};aliases=[]
    for ns in GROUPS:
        master=ns[0];layers={b:np.array(Image.open(H/f'nova_layers_final01/{master:03}_bank{b}_indices.png'))for b in PBS}
        for n in ns:
            need(all(np.array_equal(a.layer(n,b)[0],a.layer(master,b)[0])for b in PBS),'현재동일성 변경')
            aliases.append({'ref':n,'master':master,'dy':0,'current_parent_all5_exact':True,'original_US_all5_exact':all(np.array_equal(original.layer(n,b)[0],original.layer(master,b)[0])for b in PBS),'policy':'현재 수용 동일몸체 정책 유지. 원US 별도자세 완전복원 아님.'});targets[n]=layers
            for b,z in layers.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
            for form,m in(('base',0),('fourth',15)):compose(a,layers,m).save(TD/f'{form}_{n:03}.png')
    sources={}
    for folder in FOLDERS:
        for p in sorted((H/folder).iterdir()):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in SCRIPTS:
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'source_files':sources,'aliases':aliases,'targets':{str(n):{str(b):sha(z.tobytes())for b,z in layers.items()}for n,layers in targets.items()},'policy':'새2몸체×기본/포스4표시, 포스 소매 국소 원화·공통머리/손·외곽11표본을20층으로 전개. 실제게임213214/215216 동일표시의 기존 수용정책 유지.','arc_written':False,'runtime_verified':False,'no_new_art_for_217_230_claimed':True})
    print(json.dumps({'manifest':sha((TD/'manifest.json').read_bytes()),'inputs':len(sources),'layers':20}))
if __name__=='__main__':main()
