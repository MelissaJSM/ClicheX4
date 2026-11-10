"""Ultimate 사격8 후보 재현·잘못된 입력 거부·준비본 잠금."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_standing_fire import build,validate,P,PARENT,TD,MANIFEST,REFS
FINAL='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'

def main():
    d=H/'prepared_standing_fire_ultimate01';need(not d.exists(),'새 준비본 폴더 필요')
    s=H/'ultimate_standing_fire_pack01';candidate=(s/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'첫 패킹 변경')
    source=P.read_bytes();repros=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 결과 차이');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    rejected=[];normal=lambda p:p.read_bytes()
    def reject(name,data,reader):
        try:validate(data,reader)
        except(ValueError,json.JSONDecodeError,OSError)as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('잘못된 입력을 수용함 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    inputs=[TD/'manifest.json',TD/'original_PL02_U.ARC',TD/'085_bank0_indices.png',TD/'088_bank5_indices.png',TD/'092_bank8_indices.png',TD/'088_effect_tile7.png',TD/'088_effect_tile8.png',TD/'088_effect_indices.png',H/'ultimate_standing_fire_inputs01/generated.png',H/'ultimate_standing89_arm02/generated.png',H/'ultimate_standing_followthrough_inputs01/generated.png',H/'ultimate_standing90_arm01/generated.png',H/'ultimate_standing_recovery_inputs01/generated.png',H/'ultimate_standing_followthrough_common03/090_common_mask.png',H/'standing_fire_modules_probe02/086_gun_guard.png']
    for p in inputs:
        def reader(q,p=p):
            raw=normal(q);return bytes([raw[0]^1])+raw[1:]if q.resolve()==p.resolve()else raw
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');d.mkdir()
    for p in s.glob('*.png'):shutil.copy2(p,d/p.name)
    shutil.copy2(s/'PL02_U.ARC',d/'PL02_U.ARC')
    proof.update(total_identical_builds=3,reproduction_sha256=repros,rejected_inputs=rejected,rejected_count=len(rejected),source_parent_preserved=True)
    write(d/'verification.json',proof)
    meta=json.loads((TD/'manifest.json').read_text('utf8'));files=dict(meta['source_files'])
    for p in TD.iterdir():
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    dependencies=['pack_ultimate_standing_fire.py','verify_ultimate_standing_fire.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','repack_part_records_lossless.py','prepare_lowhp_final.py']
    for name in dependencies:
        p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in ['scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_compress.py']:
        p=ROOT/name;files[name]=sha(p.read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'target_manifest_sha256':MANIFEST,'refs':list(REFS),'files':files,'all_inputs_fixed':True})
    locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_standing_special_ultimate01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL02_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'target_manifest':(TD/'manifest.json').relative_to(ROOT).as_posix(),'target_manifest_sha256':MANIFEST,'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'Ultimate 사격85..92 양폼40층.86/87/90/91/92 별도 새자세,88은새89 x-1+원US83효과의기존색6.기존대기/135·다른모션/팔레트/소리/은행경계 보존.','native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in dependencies},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    write(H/'ultimate_standing_fire_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v23/shibuki_riko.bin','source_sha256':'cba70c5fee260a7e0d0e7751be9e8583ef2050696a3700add9cf06f6679b0724','resources':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'Ultimate 사격8의 원MIPS 디코드/업로드 및 GPU검사. 새 게임실기 또는 전체디렉터리 로더fixture와 구분.'})
    print(json.dumps({'prepared':d.relative_to(ROOT).as_posix(),'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes())}))
if __name__=='__main__':main()
