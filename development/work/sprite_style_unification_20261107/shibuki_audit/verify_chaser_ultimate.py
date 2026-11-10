"""Ultimate 체이서13 재현·거부 검증과 읽기 전용 준비본 잠금."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_chaser_ultimate import build,validate,P,PARENT,TD,MANIFEST,REFS
FINAL='2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c'
def main():
    d=H/'prepared_chaser_ultimate01';need(not d.exists(),'새 준비본');s=H/'chaser_ultimate_pack01';candidate=(s/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'첫 패킹 변경');source=P.read_bytes();repros=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 결과 차이');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    rejected=[];normal=lambda p:p.read_bytes()
    def reject(name,data,reader):
        try:validate(data,reader)
        except(ValueError,json.JSONDecodeError,OSError)as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('잘못된 입력 수용 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    inputs=[TD/'manifest.json',TD/'162_bank0_indices.png',TD/'173_bank5_indices.png',TD/'174_bank8_indices.png',H/'chaser_ultimate_inputs01/generated.png',H/'chaser_ultimate_inputs02/generated.png',H/'chaser_ultimate_contacts01/report.json',H/'chaser_ultimate_common01/166_common_mask.png',H/'chaser_ultimate_common02/170_before_indices.png',H/'register_chaser_ultimate_edges.py']
    inputs[-2]=H/'chaser_ultimate_common02/before_170_indices.png'
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
    deps=['pack_chaser_ultimate.py','verify_chaser_ultimate.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','repack_part_records_lossless.py','prepare_lowhp_final.py']
    for name in deps:p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_compress.py'):files[name]=sha((ROOT/name).read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'target_manifest_sha256':MANIFEST,'refs':list(REFS),'files':files,'all_inputs_fixed':True});locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_standing_fire_ultimate01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL02_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'target_manifest':(TD/'manifest.json').relative_to(ROOT).as_posix(),'target_manifest_sha256':MANIFEST,'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'Ultimate 체이서 새4키×2의상과 원US Y9이동을 두폼에 적용한13참조65층. 부모후폼9구형차이는 새공통몸체로대체한 제작정책.499비대상raw/1075층·원음향/팔레트/은행/EXE 보존.','native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in deps},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    write(H/'chaser_ultimate_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v25/shibuki_riko.bin','source_sha256':'21696e9bae002ef6c9f95fed683e7cd531fd6cdfc6c0fdae97529c3b28a09636','resources':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'Ultimate 체이서13의 원디코더/업로드 및 GPU검사. 전체디렉터리/게임 실기와구분.'})
    print(json.dumps({'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes())}))
if __name__=='__main__':main()
