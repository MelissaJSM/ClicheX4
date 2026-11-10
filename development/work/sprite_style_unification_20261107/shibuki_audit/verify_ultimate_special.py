"""Ultimate 특수3의 반복 재현·입력거부 후 감사용 준비본을 고정한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_special import build,validate,P,PARENT,TD,MANIFEST
FINAL='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'

def main():
    out=H/'prepared_standing_special_ultimate01';need(not out.exists(),'Fresh prepared directory')
    trial=H/'ultimate_special_pack01';candidate=(trial/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'Trial changed')
    source=P.read_bytes();reproductions=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'Reproduction differs');reproductions.append(sha(result))
        print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    rejected=[];normal=lambda p:p.read_bytes()
    def reject(name,data,reader):
        try:validate(data,reader)
        except (ValueError,json.JSONDecodeError) as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('Bad source accepted '+name)
    wrong=bytearray(source);wrong[100]^=1;reject('wrong_parent',bytes(wrong),normal);reject('truncated_parent',source[:-1],normal)
    paths=[TD/'manifest.json',TD/'095_bank0_indices.png',TD/'097_bank5_indices.png',
           H/'ultimate_special_inputs01/generated.png',H/'ultimate_special_native01/before_095_indices.png',
           H/'ultimate_special_common_probe01/097_common_mask.png',H/'probe_ultimate_special_common.py']
    for p in paths:
        def reader(q,p=p):
            data=normal(q)
            return bytes([data[0]^1])+data[1:] if q.resolve()==p.resolve() else data
        try:reject('changed_'+p.relative_to(H).as_posix(),source,reader)
        except OSError as ex:rejected.append({'case':'changed_'+p.relative_to(H).as_posix(),'reason':str(ex),'rejected':True})
    need(sha(P.read_bytes())==PARENT,'Parent modified');out.mkdir()
    for p in trial.glob('*.png'):shutil.copyfile(p,out/p.name)
    shutil.copyfile(trial/'PL02_U.ARC',out/'PL02_U.ARC')
    proof.update(total_identical_builds=3,reproduction_sha256=reproductions,rejected_inputs=rejected,
        rejection_count=len(rejected),source_parent_preserved=True,independent_pending=True,native_cpu_pending=True,root_art_pending=True)
    write(out/'verification.json',proof)
    prev=json.loads((H/'prepared_ultimate_return01/proposal.json').read_text('utf8'))
    write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':prev['baseline_sha256'],
        'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),
                             'before':prev['files']['PL02_U.ARC']['before'],'after':FINAL}},
        'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},
        'refs':[95,96,97],'target_manifest':(TD/'manifest.json').relative_to(ROOT).as_posix(),'target_manifest_sha256':MANIFEST,
        'scope':'Ultimate 특수95/96/97 새15층. 새95의x+1을96에 쓰는 원US 기반 신규공통화이며 현재부모95/96 동형 주장은 아니다.',
        'all_bank_boundaries_preserved':True,'native_cpu_pending':True,'independent_pending':True,'runtime_verified':False,'frozen':False})
    write(out/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()},
        'scripts':{name:sha((H/name).read_bytes()) for name in ('pack_ultimate_special.py','verify_ultimate_special.py','pack_ultimate_victory.py')},
        'target_manifest_sha256':MANIFEST,'candidate_assets_fixed':True})
    plan=json.loads((H/'standing_special_components.json').read_text('utf8'))
    plan['resources']['PL02_U.ARC']={'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}
    plan['scope_note']='새특수95/96/97의 두 ARC 원MIPS/GPU 검사. 기본은행 재배치508 디렉터리 전수검사는 별도 독립 보고.'
    write(H/'standing_special_fourform_components.json',plan)
    print(json.dumps({'prepared':out.relative_to(ROOT).as_posix(),'candidate':FINAL,'rejections':len(rejected)}))

if __name__=='__main__':main()
