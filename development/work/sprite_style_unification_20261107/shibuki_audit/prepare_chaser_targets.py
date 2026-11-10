"""새 체이서4키의65층을 실제 부모의 Y별칭13참조로 전개한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from inspect_chaser_sources import shifted
P=H/'prepared_standing_fire_base01/PL00_U.ARC'
PARENT='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
PBS=(0,5,6,7,8);REFS=tuple(range(162,175));TD=H/'chaser_targets01'
GROUPS=((162,163,164,165),(166,167,168,169),(170,171,172,173),(174,))
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
SOURCE_DIRS=('chaser_base_inputs01','chaser_base_inputs02','chaser_base_native01','chaser_base_native02','chaser_layers_probe02','chaser_layers_final02','chaser_sources01')

def main():
    need(not TD.exists(),'새 목표 폴더 필요');need(sha(P.read_bytes())==PARENT,'부모 변경');a=Archive(P.read_bytes())
    original=Archive((H/'chaser_sources01/original_base.ARC').read_bytes());sources={};targets={};aliases=[]
    for ns in GROUPS:
        k=ns[0];master={b:np.array(Image.open(H/f'chaser_layers_final02/{k:03}_bank{b}_indices.png'))for b in PBS}
        for n in ns:
            for b in PBS:
                for arc in(a,original):need(np.array_equal(arc.layer(n,b)[0],shifted(arc.layer(k,b)[0],DY[n])),f'원Y별칭 불일치 {n}/{b}')
            targets[n]={b:shifted(z,DY[n])for b,z in master.items()}
            need(all(np.count_nonzero(targets[n][b])==np.count_nonzero(master[b])for b in PBS),'Y이동 잘림')
            aliases.append({'ref':n,'master':k,'dy':DY[n],'current_parent_and_original_US_all5_layers_exact':True})
    TD.mkdir()
    for folder in SOURCE_DIRS:
        for p in sorted((H/folder).iterdir()):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('prepare_chaser_base.py','prepare_chaser_base_page02.py','register_chaser_base.py','register_chaser_base_page02.py','probe_chaser_layers_v2.py','register_chaser_layer_edges_v2.py','inspect_chaser_sources.py','prepare_chaser_targets.py'):
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for n,ll in targets.items():
        for b,z in ll.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
        for form,mask in(('base',0),('fourth',15)):compose(a,ll,mask).save(TD/f'{form}_{n:03}.png')
    for form,mask in(('base',0),('fourth',15)):
        for i,ns in enumerate(GROUPS):page([(str(n),compose(a,targets[n],mask))for n in ns],a.composite(0,mask)[0],TD/f'{form}_group_{i:02}.png',cols=2,scale=4)
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'source_files':sources,'aliases':aliases,'targets':{str(n):{str(b):sha(z.tobytes())for b,z in ll.items()}for n,ll in targets.items()},'source_policy':'새4키 각2의상에서 공통머리/피부와 의상4층을 등록한 뒤 실제 원US·현재PL00의Y이동으로13참조를 전개. 구형머리·몸체 덮기나 색축소 없음.','arc_written':False,'runtime_verified':False,'limits':['현재PL02 after의9파생은 이 exact별칭이 아니며 별개 후속 대상이다.','손 피부ROI 정적 비교와 실제 체이서 손잡이/발판 접촉은 구별한다.']})
    print(json.dumps({'manifest_sha256':sha((TD/'manifest.json').read_bytes()),'files':len(sources),'layers':65}))
if __name__=='__main__':main()
