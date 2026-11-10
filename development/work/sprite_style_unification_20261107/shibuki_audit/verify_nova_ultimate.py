"""Ultimate 노바 준비4를 재현·거부검사하고 고정 준비본으로 보존한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_nova_ultimate import build,validate,P,PARENT,TD,MANIFEST,REFS
FINAL='687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f'
def main():
    d=H/'prepared_nova_ultimate01';need(not d.exists(),'새 준비본');s=H/'nova_ultimate_pack01';candidate=(s/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'패킹 변경');source=P.read_bytes();repros=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 불일치');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    normal=lambda p:p.read_bytes();rejected=[]
    def reject(name,data,reader):
        try:validate(data,reader)
        except(ValueError,json.JSONDecodeError,OSError)as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('잘못된 입력 수용 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    inputs=[TD/'manifest.json',TD/'213_bank0_indices.png',TD/'214_bank5_indices.png',TD/'216_bank8_indices.png',H/'nova_ultimate_inputs01/generated.png',H/'nova_ultimate_footwear_inputs01/generated.png',H/'nova_ultimate_native01/report.json',H/'nova_ultimate_footwear_composed01/before_215_donor_mask.png',H/'nova_ultimate_common01/215_common_mask.png',H/'nova_ultimate_common02/215_bank5_indices.png',H/'compose_nova_ultimate_footwear.py',H/'finalize_nova_ultimate_common.py']
    for p in inputs:
        def reader(q,p=p):
            blob=normal(q);return bytes([blob[0]^1])+blob[1:]if q.resolve()==p.resolve()else blob
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');d.mkdir()
    for p in s.glob('*.png'):shutil.copy2(p,d/p.name)
    shutil.copy2(s/'PL02_U.ARC',d/'PL02_U.ARC');proof.update(total_identical_builds=3,reproduction_sha256=repros,rejected_inputs=rejected,rejected_count=len(rejected),source_parent_preserved=True);write(d/'verification.json',proof)
    meta=json.loads((TD/'manifest.json').read_text('utf8'));files=dict(meta['source_files'])
    for p in TD.iterdir():
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    deps=['pack_nova_ultimate.py','verify_nova_ultimate.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','repack_part_records_lossless.py','prepare_lowhp_final.py','compose_nova_fourth_costume.py']
    for name in deps:p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_compress.py'):files[name]=sha((ROOT/name).read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'target_manifest_sha256':MANIFEST,'refs':list(REFS),'files':files,'all_inputs_fixed':True});locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_chaser_ultimate01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL02_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'target_manifest':TD.relative_to(ROOT).as_posix()+'/manifest.json','target_manifest_sha256':MANIFEST,'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'Ultimate 노바 준비2몸체×전후4표시와 현재 동일짝213214/215216을20층으로 전개. 새 하체 국소 donor/첫새발 보존·공통머리/사지·동색외곽1셀. 원US의 별도짝 완전복원 아님. 508비대상raw/1120층·원효과217..230·음향/팔레트/은행/EXE 보존.','native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in deps},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    write(H/'nova_ultimate_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v27/shibuki_riko.bin','source_sha256':'73c2b28eb59739234351b59d9f18de6a1a9429bcf9d8e71327f3206dcb6d2cbb','resources':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'Ultimate 준비4 원디코더/업로드/GPU 검사. 실제게임/전체디렉터리검사와구분.'})
    print(json.dumps({'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes())}))
if __name__=='__main__':main()
