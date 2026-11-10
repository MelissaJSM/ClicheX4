"""피격13의 완료된 정적·독립·원MIPS·원순서 근거만 결합해 준비본을 동결한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=D/'packed_hurt_candidate_v1'
FINAL='978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
PARENT='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
    out=P/'FROZEN.json';assert not out.exists(),'동결 파일 덮어쓰기 거부'
    assert sha(P/'PL00_U.ARC')==FINAL
    proposal=read(P/'proposal.json');assert proposal['files']['PL00_U.ARC']['after']==FINAL and proposal['parent_arc_sha256']==PARENT
    independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_hurt13_independent01/report.json'
    assert sha(independent)=='290e224ec21e4d7dcb8716d7eeaad33a7c36d0bf5e3fc470dbdf329194625bb8'
    ij=read(independent);assert ij['passed']and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
    lockpath=P/'INPUT_FROZEN.json';assert sha(lockpath)==ij['input_frozen_sha256'];lock=read(lockpath)
    assert lock['asset_sha256']==FINAL and len(lock['files'])==259
    for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
    target=D/'final_targets_v1/manifest.json';assert sha(target)==ij['target_manifest_sha256']
    checkpoints=[];viewed=[]
    digests={77:'9ef6e080de1f9ed1e2786ee63e57b8db6c2c085c59e30ed9879adaea32b732c7',78:'bf3a13cae174dafa8fd0774cc82011dfe21136b20e4176bff6ba840d2359741d',81:'a47373b7e61e9f1e28d9b89a23b488bf1e081ef67bedd2e717fe337f2ac35b01',83:'b7a4981088c5562e6a73672b8235dd09ed727c6215269ae6a90b6eac81cee795',84:'3d57365ef89c1475a9261c1de02e907ef2fdae30538cf06c344a6a0d3c1f1870',85:'ca6df6b486e528b71d05b81c2b99bf684a8c1a9e14dff7afcc25b6c86c8eb86c',86:'46266c09f656658d63d7ecf82ab701b4b954f89a51cc723df63da01742476f65'}
    for number,digest in digests.items():
        p=ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{number}.json';assert sha(p)==digest;checkpoints.append(p)
        for q in read(p)['root_actually_viewed']:
            if '/nana_audit/'in q['path'] or '/nana_hurt_partial_review02/'in q['path']:
                f=ROOT/q['path'];assert sha(f)==q['sha256'];viewed.append(f)
    proofs=[P/'verification.json',P/'source_reconstruction.json',P/'reproduction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',independent]
    for p in proofs:assert read(p)['passed'],rel(p)
    assert read(P/'reproduction.json')['asset_sha256']==FINAL
    assert read(D/'native_components_v1_native_checks.json')['resources']['PL00_U.ARC']['candidate_sha256']==FINAL
    assert read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
    files=[P/'PL00_U.ARC',P/'proposal.json',lockpath,target,*proofs,*checkpoints,*viewed,D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_production.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',Path(__file__).resolve()]
    files=list(dict.fromkeys(files))
    result={'frozen':True,'status':'나나 기본/포스 피격13 준비본 동결. 원화·공유·효과·부분조합·독립·원MIPS/GPU·오프라인 원순서 검사와 루트 정적 미술 검토 완료. 새 게임 통합/실기는 별도.',
      'character':'nana','forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'refs':list(range(106,115))+[233,234,235,236],
      'new_authored_body_keys':[106,110,233,234],'derived_body_effect_refs':[107,108,109,111,112,113,114,235,236],
      'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL00_U.ARC']['before'],
      'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':259,'independent_counts':ij['counts'],
      'root_art_review_checkpoints':[rel(p)for p in checkpoints],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
      'reproduction':'동일 부모와 입력으로 메모리 재제작 byte-identical. 잘못된 입력8종 거부. 별도 프로세스 출력 파일 재생성은 미실행.',
      'aura_provenance':'235/236은 원작X효과가 아니라 이전에 수용된 나나 오라85/172px. 실제8연결 조각13/7개 중 겹친 조각만1~3px 강체이동, 색/픽셀/조각형상 보존. 새몸과부분의상 겹침0, 최대거리5/8px.',
      'shared_body_effect_policy':'106/107/108 및110/111 공유 유지. 원효과 전체타일과추가조립 보존.109/112..114는 새몸에 기존 실루엣 규칙을 적용하되 새작은성분 삭제 없음.',
      'limits':['실제 게임 피격·점멸/클럿·물리·이벤트복귀 검증은 아직 수행하지 않았다.','오프라인60호출/초는 검토 가정이며 사람의 실시간 게임 관찰과 다르다.','독립은416대상RGBA를 직접 확인하고 비대상층 보존을 검사했다. 제작자7296조합 전수와 구분한다.','Ultimate 피격/저체력 및 다른 모션은 이 후보 완료 범위에 포함되지 않는다.'],
      'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
