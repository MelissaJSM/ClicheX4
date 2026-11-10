"""Ultimate 호버10의 재현·변조 거부·최종 입력을 고정한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_hover_ultimate import build,validate,P,PARENT,TD,MANIFEST,REFS
FINAL='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
def main():
    d=H/'prepared_hover_ultimate01';need(not d.exists(),'기존 준비본 보호');s=H/'hover_ultimate_pack01';candidate=(s/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'후보 변경');source=P.read_bytes();repros=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 실패');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    normal=lambda p:p.read_bytes();rejected=[]
    def reject(name,data,reader):
        try:validate(data,reader)
        except(ValueError,json.JSONDecodeError,OSError)as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('변조 입력 수용 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    paths=[TD/'manifest.json',TD/'221_bank0_indices.png',TD/'222_bank0_indices.png',TD/'228_bank5_indices.png',TD/'229_bank0_indices.png',TD/'230_bank8_indices.png',H/'hover_ultimate_inputs01/generated_v1.png',H/'hover_ultimate_inputs02/generated_v1.png',H/'hover221_reach_inputs01/generated_v1.png',H/'hover222_cleanup_inputs01/generated_v1.png',H/'hover_ultimate_shot_inputs01/page01/generated_v1.png',H/'hover_ultimate_shot_inputs01/page02/generated_v1.png',H/'hover_ultimate_shot_composed03/registration.json',H/'prepare_hover_ultimate_targets.py',H/'compose_hover_five_shots.py',H/'hover_ultimate_shot_inputs01/222_barrel_mask.png']
    for p in paths:
        def reader(q,p=p):
            blob=normal(q);return bytes([blob[0]^1])+blob[1:]if q.resolve()==p.resolve()else blob
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');d.mkdir()
    for p in s.glob('*.png'):shutil.copy2(p,d/p.name)
    shutil.copy2(s/'PL02_U.ARC',d/'PL02_U.ARC')
    proof.update(total_identical_builds=3,reproduction_sha256=repros,rejected_inputs=rejected,rejected_count=len(rejected),source_parent_preserved=True,actual_engine_mask=15,actual_body_costume='accepted Ultimate after',original_static_jets_preserved=True,original_muzzle_table_unchanged=True)
    write(d/'verification.json',proof)
    meta=json.loads((TD/'manifest.json').read_text('utf8'));files=dict(meta['source_files'])
    for p in TD.iterdir():
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    deps=['pack_hover_ultimate.py','verify_hover_ultimate.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','repack_part_records_lossless.py','prepare_lowhp_final.py']
    for name in deps:p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_compress.py'):files[name]=sha((ROOT/name).read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'target_manifest_sha256':MANIFEST,'refs':list(REFS),'files':files,'all_inputs_fixed':True});locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_nova_strike_ultimate01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL02_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'target_manifest':TD.relative_to(ROOT).as_posix()+'/manifest.json','target_manifest_sha256':MANIFEST,'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'Ultimate 실제 강제mask15 호버221..230 새5몸/5사격팔, 원상체0·하체5 소유 유지. 원15추진위상/6전체타일·원총구표 보존, 정본34 총열60셀/투명11셀을 원총구로 평행등록.512raw 중502비대상·1090층·1741조립 보존. 모든은행/entry 경계·팔레트/음향/EXE 불변.','limits':['221 높이1px 차이는 새 손 관절을 유지하며 별도 기록.','226/228 생성총은 채택하지 않고 정본총을 새전완 앞에 합성했다. 팔 늘림/개별축소 없음.','부분mask0..14는 보존회귀 진단이며 실제호버는mask15이다.','222/228 손총 연결은 밝은배경과 원탄환 합성 추가검토 예정.'],'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in deps},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    write(H/'hover_ultimate_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.bin','source_sha256':'753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252','resources':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'Ultimate 호버10 원디코더/업로드/GPU 검사. 실제게임/전체디렉터리검사와 구분.'})
    print(json.dumps({'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes())}))
if __name__=='__main__':main()
