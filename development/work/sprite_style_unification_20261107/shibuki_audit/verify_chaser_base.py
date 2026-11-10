"""체이서13 최종 후보의 재현·잘못된 입력 거부·준비본 잠금."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_chaser_base_final import build,validate,P,PARENT,TD,REFS,LOCK,LOCK_SHA
FINAL='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'

def main():
    d=H/'prepared_chaser_base01';need(not d.exists(),'새 준비본 필요');s=H/'chaser_base_pack03';candidate=(s/'PL00_U.ARC').read_bytes();need(sha(candidate)==FINAL,'후보 변경');data=P.read_bytes();repro=[]
    for i in range(2):
        result,proof=build(data);need(result==candidate,'재현 불일치');repro.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    rejected=[];normal=lambda p:p.read_bytes()
    def reject(name,blob,reader):
        try:validate(blob,reader)
        except(ValueError,OSError,json.JSONDecodeError)as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('잘못된 입력 수용 '+name)
    bad=bytearray(data);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',data[:-1],normal)
    inputs=[LOCK,TD/'manifest.json',TD/'162_bank0_indices.png',TD/'173_bank5_indices.png',TD/'174_bank8_indices.png',H/'chaser_base_inputs01/generated.png',H/'chaser_base_inputs02/generated.png',H/'chaser_storage01/recipe.json',H/'chaser_storage01/166.raw',H/'chaser_storage_plan01/report.json',H/'standing_fire_existing_tileorder01/033_trial_raw.bin',H/'standing_fire_existing_tileorder01/report.json',H/'chaser_layers_final02/170_bank0_indices.png',H/'register_chaser_layer_edges_v2.py']
    for p in inputs:
        def reader(q,p=p):
            blob=normal(q);return bytes([blob[0]^1])+blob[1:]if q.resolve()==p.resolve()else blob
        reject('changed_'+p.relative_to(H).as_posix(),data,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');d.mkdir()
    for p in s.glob('*.png'):shutil.copy2(p,d/p.name)
    shutil.copy2(s/'PL00_U.ARC',d/'PL00_U.ARC');proof.update(total_identical_builds=3,reproduction_sha256=repro,rejected_inputs=rejected,rejected_count=len(rejected),source_parent_preserved=True);write(d/'verification.json',proof)
    lock=json.loads(LOCK.read_text('utf8'));files=dict(lock['files']);files[LOCK.relative_to(ROOT).as_posix()]=LOCK_SHA
    deps=['pack_chaser_base_final.py','pack_chaser_base.py','verify_chaser_base.py','prepare_chaser_targets.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','repack_part_records_lossless.py','prepare_lowhp_final.py']
    for name in deps:p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','scripts/optimize_rin_style_tiles.py','src/psx_player.py','src/psx_compress.py'):
        files[name]=sha((ROOT/name).read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'refs':list(REFS),'storage_only_refs':lock['storage_only_refs'],'files':files,'all_inputs_fixed':True});locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_standing_fire_base01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL00_U.ARC':{'path':(d/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL00_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'storage_only_refs':lock['storage_only_refs'],'target_manifest':(TD/'manifest.json').relative_to(ROOT).as_posix(),'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'체이서4새자세×2의상→원Y파생13참조65층. 기존16참조는 모든256nibble 보존한 타일순열과 대응 조립번호만 변경. 모든은행경계/팔레트/음향/비대상표시/선택사본 보존.','native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in deps},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    print(json.dumps({'prepared':d.relative_to(ROOT).as_posix(),'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes())}))
if __name__=='__main__':main()
