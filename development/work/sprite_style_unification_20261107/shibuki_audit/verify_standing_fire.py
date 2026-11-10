"""고정은행 새8참조와 무손실18순열을 재현하고 변조 거부를 확인한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_standing_fire import build,validate,P,PARENT,LOCK,LOCK_SHA
FINAL='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'

def main():
    out=H/'prepared_standing_fire_base01';need(not out.exists(),'새 준비 폴더 필요')
    trial=H/'standing_fire_base_pack01';candidate=(trial/'PL00_U.ARC').read_bytes()
    need(sha(candidate)==FINAL,'시험 후보 변경');source=P.read_bytes();reproductions=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 불일치')
        reproductions.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    rejected=[];normal=lambda p:p.read_bytes()
    def reject(name,data,reader):
        try:validate(data,reader)
        except (ValueError,json.JSONDecodeError) as ex:
            rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('변조 입력 수용 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    names=('standing_fire_inputs01/generated.png','standing_fire_inputs02/generated.png',
           'standing_fire_inputs03/generated.png','standing_fire_fourth_sleeves01/generated.png',
           'standing_fire_targets_probe01/085_bank0_indices.png','standing_fire_targets_probe01/091_bank7_indices.png',
           'standing_fire_compact01/report.json','standing_fire_existing_tileorder01/037_trial_raw.bin',
           'standing_fire_existing_tileorder01/report.json','standing_fire_storage_plan02/report.json',
           'register_standing_recovery_boot.py','probe_standing_fire_modules.py')
    for p in [LOCK,*[H/name for name in names]]:
        def reader(q,p=p):
            raw=normal(q)
            return bytes([raw[0]^1])+raw[1:] if q.resolve()==p.resolve() else raw
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');out.mkdir()
    for p in trial.glob('*.png'):shutil.copyfile(p,out/p.name)
    shutil.copyfile(trial/'PL00_U.ARC',out/'PL00_U.ARC')
    proof.update(total_identical_builds=3,reproduction_sha256=reproductions,rejected_inputs=rejected,
                 rejected_count=len(rejected),source_parent_preserved=True)
    write(out/'verification.json',proof)
    previous=json.loads((H/'prepared_standing_special_base01/proposal.json').read_text('utf8'))
    proposal={'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],
        'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),
                              'before':previous['files']['PL00_U.ARC']['before'],'after':FINAL}},
        'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},
        'selected_refs':list(range(85,93)),'storage_only_refs':proof['storage_only_refs'],
        'target_lock':LOCK.relative_to(ROOT).as_posix(),'target_lock_sha256':LOCK_SHA,
        'scope':'기본/포스85..92 새40층과 기존18참조 전체타일 순열. 기존raw는 역순열로 전체texel 복구, 모든 표시·부분아머 동일. 도트삭감 없음.',
        'graphics_directory_changed':False,'graphics_bank0_free_bytes':68,
        'parts_slack':proof['parts_slack'],'selection_sync':proof['ui_mapping_evidence'],
        'approval_scope':'root가 기존 승인된 고정은행 가역 패킹 범위에서 판단. 사용자 신규승인 문구가 아님.',
        'native_cpu_pending':True,'independent_pending':True,'runtime_verified':False,'frozen':False}
    write(out/'proposal.json',proposal)
    write(out/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()},
        'source_scripts':{name:sha((H/name).read_bytes()) for name in ('pack_standing_fire.py','verify_standing_fire.py')},
        'target_lock_sha256':LOCK_SHA,'candidate_assets_fixed':True})
    write(H/'standing_fire_components.json',{'project':'ver_buki_riko',
        'source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v22/shibuki_riko.bin',
        'source_sha256':'54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99',
        'resources':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},
        'checkpoint_only':True,'scope_note':'새8+순열18 원MIPS/GPU 후보 검사. 별도508 디렉터리 로더 전수검사는 독립 담당 수행.'})
    print(json.dumps({'prepared':out.relative_to(ROOT).as_posix(),'candidate':FINAL,'rejections':len(rejected)}))

if __name__=='__main__':main()
