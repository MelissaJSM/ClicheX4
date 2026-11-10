"""Ultimate 돌진4의 재현·변조 거부·최종 입력을 고정한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_nova_strike_ultimate03 import build,validate,P,PARENT,TD,MANIFEST,REFS
FINAL='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7'
def main():
    d=H/'prepared_nova_strike_ultimate01';need(not d.exists(),'기존 준비본 보호');s=H/'nova_strike_ultimate_pack03';candidate=(s/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'후보 변경');source=P.read_bytes();repros=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 실패');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    normal=lambda p:p.read_bytes();rejected=[]
    def reject(name,data,reader):
        try:validate(data,reader)
        except(ValueError,json.JSONDecodeError,OSError)as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('변조 입력 수용 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    paths=[TD/'manifest.json',TD/'217_bank0_indices.png',TD/'218_bank5_indices.png',TD/'219_bank5_indices.png',TD/'220_bank5_indices.png',TD/'220_bank8_indices.png',H/'nova_strike_ultimate_inputs01/generated_v1.png',H/'nova_strike_ultimate_native01/217_indices.png',H/'nova_strike_ultimate_native01/registration.json',H/'nova_strike_ultimate_effects02/manifest.json',H/'prepare_nova_strike_ultimate_effects02.py',H/'prepare_nova_strike_ultimate_targets.py']
    for p in paths:
        def reader(q,p=p):
            blob=normal(q);return bytes([blob[0]^1])+blob[1:]if q.resolve()==p.resolve()else blob
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');d.mkdir()
    for p in s.glob('*.png'):shutil.copy2(p,d/p.name)
    shutil.copy2(s/'PL02_U.ARC',d/'PL02_U.ARC')
    proof.update(total_identical_builds=3,reproduction_sha256=repros,rejected_inputs=rejected,rejected_count=len(rejected),source_parent_preserved=True,actual_engine_mask=15,actual_body_costume='accepted Ultimate after',effects218_current3_exact=True,effect220_changed_cells=93,effect219_new_silhouette=True)
    write(d/'verification.json',proof)
    meta=json.loads((TD/'manifest.json').read_text('utf8'));files=dict(meta['source_files'])
    for p in TD.iterdir():
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    deps=['pack_nova_strike_ultimate03.py','verify_nova_strike_ultimate.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','repack_part_records_lossless.py','prepare_lowhp_final.py']
    for name in deps:p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_compress.py'):files[name]=sha((ROOT/name).read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'target_manifest_sha256':MANIFEST,'refs':list(REFS),'files':files,'all_inputs_fixed':True});locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_nova_ultimate01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL02_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'target_manifest':TD.relative_to(ROOT).as_posix()+'/manifest.json','target_manifest_sha256':MANIFEST,'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'Ultimate 실제 강제mask15에 맞춘 새 after 몸체217/218/220와 새219 실루엣.218 현재3점 exact,220 역사 외부효과 보존 및 새몸 가림93셀 변경.512raw 중508비대상·1120층·1771조립 보존. 모든은행/entry 경계·팔레트/음향/EXE 불변.','native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in deps},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    write(H/'nova_strike_ultimate_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v28/shibuki_riko.bin','source_sha256':'13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77','resources':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'Ultimate 돌진4 원디코더/업로드/GPU 검사. 실제게임/전체디렉터리검사와 구분.'})
    print(json.dumps({'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes())}))
if __name__=='__main__':main()
