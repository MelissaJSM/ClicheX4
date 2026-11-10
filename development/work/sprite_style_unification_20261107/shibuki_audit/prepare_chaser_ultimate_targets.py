"""Ultimate 체이서 새4키와 원US Y9파생을65층으로 확정."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from inspect_chaser_sources import shifted
P=H/'prepared_standing_fire_ultimate01/PL02_U.ARC';PARENT='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
PBS=(0,5,6,7,8);REFS=tuple(range(162,175));TD=H/'chaser_ultimate_targets01'
GROUPS=((162,163,164,165),(166,167,168,169),(170,171,172,173),(174,))
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
SOURCE_DIRS=('chaser_ultimate_inputs01','chaser_ultimate_inputs02','chaser_ultimate_native01','chaser_ultimate_native02','chaser_ultimate_contacts01','chaser_ultimate_common01','chaser_ultimate_common02','chaser_sources01')
def main():
    need(not TD.exists(),'새 목표 폴더');need(sha(P.read_bytes())==PARENT,'부모 변경');a=Archive(P.read_bytes());original=Archive((H/'chaser_sources01/original_ultimate.ARC').read_bytes());targets={};aliases=[]
    for ns in GROUPS:
        k=ns[0];master={b:np.array(Image.open(H/f'chaser_ultimate_common02/{k:03}_bank{b}_indices.png'))for b in PBS}
        for n in ns:
            for b in PBS:need(np.array_equal(original.layer(n,b)[0],shifted(original.layer(k,b)[0],DY[n])),f'원US Y별칭 {n}/{b}')
            before_exact=np.array_equal(a.layer(n,0)[0],shifted(a.layer(k,0)[0],DY[n]))
            targets[n]={b:shifted(z,DY[n])for b,z in master.items()};need(all(np.count_nonzero(targets[n][b])==np.count_nonzero(master[b])for b in PBS),'파생 잘림')
            old_diffs={str(b):int((a.layer(n,b)[0]!=shifted(a.layer(k,b)[0],DY[n])).sum())for b in PBS}
            aliases.append({'ref':n,'master':k,'dy':DY[n],'original_US_all5_layers_exact':True,'current_parent_layer_differences':old_diffs,'new_policy':'새두의상 공통몸체에 원US Y이동을 적용. 현재후폼의별도 구형9파생과동일하다고하지않음.'})
    TD.mkdir();sources={}
    for folder in SOURCE_DIRS:
        for p in sorted((H/folder).iterdir()):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('prepare_chaser_ultimate.py','prepare_chaser_ultimate_late.py','register_chaser_ultimate.py','register_chaser_ultimate_contacts.py','probe_chaser_ultimate_common.py','register_chaser_ultimate_edges.py','inspect_chaser_sources.py','prepare_chaser_ultimate_targets.py'):
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for n,ll in targets.items():
        for b,z in ll.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
        for form,mask in(('before',15),('after',0)):compose(a,ll,mask).save(TD/f'{form}_{n:03}.png')
    for form,mask in(('before',15),('after',0)):
        for i,ns in enumerate(GROUPS):page([(str(n),compose(a,targets[n],mask))for n in ns],a.composite(0,mask)[0],TD/f'{form}_group_{i:02}.png',cols=2,scale=4)
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'source_files':sources,'aliases':aliases,'targets':{str(n):{str(b):sha(z.tobytes())for b,z in ll.items()}for n,ll in targets.items()},'source_policy':'新4키 두의상 공통머리/피부와 재킷overlay5. 원US Y이동을양폼에적용한새파생이며 부모after9차이는명시. 머리/몸크기일괄변형없음.','arc_written':False,'runtime_verified':False,'limits':['174 귀정점/머리폭은 새기본체이서보다각1px추가, 원바닥27은유지.','170은새발목/샌들35셀을1px위로등록하며 관절겹침9셀을따로기록.','피부손·발의 실제차량손잡이/발판 접촉은 미확인.']});print(json.dumps({'manifest_sha256':sha((TD/'manifest.json').read_bytes()),'source_files':len(sources),'layers':65}))
if __name__=='__main__':main()
