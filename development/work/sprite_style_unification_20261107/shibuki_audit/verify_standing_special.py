"""특수3 후보를 반복 재현하고 입력변조 거부 및 부모 보존을 확인한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_standing_special_relocated import build,validate,P,PARENT,LOCK,LOCK_SHA
FINAL='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'

def main():
    out=H/'prepared_standing_special_base01';need(not out.exists(),'Fresh prepared directory')
    trial=H/'standing_special_pack02';candidate=(trial/'PL00_U.ARC').read_bytes()
    need(sha(candidate)==FINAL,'Trial changed');source=P.read_bytes();reproductions=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'Non-deterministic build')
        reproductions.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    rejected=[];normal=lambda p:p.read_bytes()
    def reject(name,data,reader):
        try:validate(data,reader)
        except (ValueError,json.JSONDecodeError) as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('Bad input accepted '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    names=('standing_special_inputs01/generated.png','standing_special95_chest01/generated.png',
           'standing_special_native02/fourth_095_indices.png','standing_special_layers01/095_bank0_indices.png',
           'standing_special_layers01/097_bank7_indices.png','standing_special_storage03/joint.raw',
           'standing_special_storage03/report.json','probe_standing_special_layers.py')
    for p in [LOCK,*[H/name for name in names]]:
        def reader(q,p=p):
            raw=normal(q)
            return bytes([raw[0]^1])+raw[1:] if q.resolve()==p.resolve() else raw
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'Parent changed');out.mkdir()
    for p in trial.glob('*.png'):shutil.copyfile(p,out/p.name)
    shutil.copyfile(trial/'PL00_U.ARC',out/'PL00_U.ARC')
    proof.update(total_identical_builds=3,reproduction_sha256=reproductions,rejected_inputs=rejected,
                 rejected_count=len(rejected),source_parent_preserved=True)
    write(out/'verification.json',proof)
    previous=json.loads((H/'prepared_hurt_base01/proposal.json').read_text('utf8'))
    proposal={'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],
        'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),
                              'before':previous['files']['PL00_U.ARC']['before'],'after':FINAL}},
        'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},
        'selected_refs':[95,96,97],'target_lock':LOCK.relative_to(ROOT).as_posix(),'target_lock_sha256':LOCK_SHA,
        'scope':'기본/포스 특수95/96/97 새15층. 96은 새95의 x+1. 다른 자세·원표·팔레트·음향은 보존.',
        'graphics_directory_change':proof['graphics'],
        'relocation_evidence':{'path':'work/sprite_style_unification_20261107/zero_audit/shibuki_bank12_tail280_audit01/report.json',
                               'sha256':'6bf084080e538acf10f589fbca9efd31896b4fced4d6b771e98c31e67861ee83'},
        'approval_scope':'root가 기존 승인된 가역 내부 패킹 범위에서 판단. 사용자 새 주소 직접승인 주장이 아님.',
        'native_cpu_pending':True,'independent_pending':True,'runtime_verified':False,'frozen':False}
    write(out/'proposal.json',proposal)
    write(out/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()},
        'source_scripts':{name:sha((H/name).read_bytes()) for name in ('pack_standing_special_relocated.py','verify_standing_special.py')},
        'target_lock_sha256':LOCK_SHA,'candidate_assets_fixed':True})
    write(H/'standing_special_components.json',{'project':'ver_buki_riko',
        'source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v21/shibuki_riko.bin',
        'source_sha256':'6d550cbcbcf06315c07aa17bbee75e07f64e4f0dc4efd6b2f381a3dc7a40db42',
        'resources':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},
        'checkpoint_only':True,'scope_note':'새특수3 원MIPS/GPU 후보 검사. 별도508 디렉터리 로더 전수검사는 독립 담당이 수행한다.'})
    print(json.dumps({'prepared':out.relative_to(ROOT).as_posix(),'candidate':FINAL,'rejections':len(rejected)}))

if __name__=='__main__':main()
