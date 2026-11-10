"""Ultimate 라이징7의 동결 증거. 게임/포인터/저장자료에 쓰지 않는다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=D/'packed_ultimate_candidate_v1'
FINAL='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
PARENT='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    out=P/'FROZEN.json';assert not out.exists()
    assert sha(P/'PL02_U.ARC')==FINAL
    proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL02_U.ARC']['after']==FINAL
    independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_rising7_independent01/report.json'
    assert sha(independent)=='bb8d5573179cc038980bd82d0f19966907fc7cd4e992984304f04109d9014b70'
    ij=read(independent);assert ij['passed']and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
    lock=P/'INPUT_FROZEN.json';assert sha(lock)==ij['input_frozen_sha256'];j=read(lock);assert j['candidate_sha256']==FINAL
    for q in j['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
    td=D/'ultimate_layers_probe_v2/manifest.json';assert sha(td)==ij['target_manifest_sha256']
    proofs=[P/'verification.json',P/'weapon_effect_verification.json',P/'source_reconstruction.json',P/'reproduction.json',D/'ultimate_native_components_native_checks.json',D/'ultimate_native_cycle_v1/verification.json',D/'ultimate_effect_contact_v1/report.json',independent]
    for p in proofs:assert read(p)['passed'],rel(p)
    assert read(D/'ultimate_native_components_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
    assert read(P/'reproduction.json')['candidate_sha256']==FINAL
    assert read(D/'ultimate_native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
    checkpoints=[];viewed=[]
    for n,h in((73,'13248ff75584db1f7d4735d7a7cab8300aa3bcf798cbf9fbfa5367aa0be080b7'),(74,'f2bb489428355c99d1843e64887f3b19f610de612cee165817951945ee81605d')):
        p=ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{n}.json';assert sha(p)==h;checkpoints.append(p)
        for q in read(p)['root_actually_viewed']:
            p=ROOT/q['path'];assert sha(p)==q['sha256'];viewed.append(p)
    assert len(viewed)==10
    files=[P/'PL02_U.ARC',P/'proposal.json',lock,td,*proofs,*checkpoints,*viewed,D/'ultimate_native_components.json',D/'ultimate_native_cycle_v1/manifest.json',D/'ultimate_native_cycle_v1/REVIEW.html',D/'verify_ultimate_source_chain.py',D/'verify_ultimate_reproduction.py',D/'verify_ultimate_effect_contact.py',D/'make_ultimate_cycle.py',D/'verify_ultimate_cycle.py',Path(__file__).resolve()]
    result={'frozen':True,'status':'나나 Ultimate 라이징7 준비 자원 동결. 제작/독립/native 및 루트 정적미술 검토 완료. 새 통합게임은 별도.','character':'nana','forms':['ultimate_before','ultimate_after'],'refs':[100,101,102,103,104,231,232],'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(j['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(p)for p in checkpoints],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,'source_reconstruction':'생성원화12 고정셀→정본권총→실제 원화경계5셀→의상 의미영역→231접지→35층 제작자 재구성. 독립reader는35층/실제ARC와 고정해시 중심.','reproduction':'동일 프로세스 byte-identical 재제작, 12종 잘못된 입력 거부. 별도 출력 프로세스 재생성 미실행.','231_232_relation':'디코딩 데이터/표시와 물리 스트림 offset141410까지 공유한다. 기본PL00 후보의 별도스트림과 혼동하지 않는다.','limits':['청록 불꽃판은 원 초기효과 점유의 양방향 공간 검사이며 실제 CLUT/시간위상/플레이 영상이 아니다.','권총은 수용85의 20색인 정본8px 모듈을90도회전해 신규 손가림 아래에 놓았다.','231/232는 새 신발/아래발목 모듈3행을1px아래로 옮기고 같은 원화의 상부 발목행을 유지했다. 전체하체 축척이나 단색채움은 없다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'frozen':True,'asset_sha256':FINAL,'freeze_sha256':sha(out)}))
if __name__=='__main__':main()
