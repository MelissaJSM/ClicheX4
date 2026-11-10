"""선택1..8 동기화 준비본의 재현/실제열람 출처를 잠근다."""
from pathlib import Path
import sys,json,shutil,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];W=H.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
    src=H/'selection_standing_sync03';older=H/'selection_standing_sync02';d=H/'prepared_selection_standing01';assert not d.exists()
    assert sha(src/'ST0E_U1.ARC')==sha(older/'ST0E_U1.ARC')=='47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'
    report=json.loads((src/'report.json').read_text('utf8'));assert report['passed'] and not report['packing']['historical_part_counts_preserved']
    d.mkdir();shutil.copy2(src/'ST0E_U1.ARC',d/'ST0E_U1.ARC')
    pictures=[]
    for n in range(1,9):
        name=f'copy_{n:02}.png';assert sha(src/name)==sha(older/name)
        shutil.copy2(src/name,d/name);pictures.append(bound(d/name))
    review={'actual_images_viewed':8,'images':pictures,'observations':['기존 선택1..8과 새 사본, 새 게임85..92를 같은 원점 판에서 실제 열람했다.','머리갈래·소매·신발의 새 세부가 선택 사본에도 유지되며 추가 확정 절단을 찾지 못했다.','선택별 Y차 -1/0/0/0/0/-1/-2/0는 기존 표시에서 확인한 값이며 전체 그림 크기를 바꾸지 않았다.'],'runtime_or_animation_review':False}
    write(d/'visual_review.json',review)
    proposal={'kind':'shibuki_selection_standing_8','candidate':bound(d/'ST0E_U1.ARC'),'parent':report['inputs'][0],'game_old':report['inputs'][1],'game_new':report['inputs'][2],'source_report':bound(src/'report.json'),'source_code':bound(H/'sync_standing_selection.py'),'allowed_selection_bank':2,'allowed_refs':list(range(1,9)),'mapping':report['mapping'],'original_target_owned_tiles':report['original_target_owned_tiles'],'nonselected_frames_exact':report['nonselected_ui_frames_exact'],'original_shared_blank_tile4_preserved':4 not in report['changed_tiles'],'texture_changed_tiles':report['changed_tiles'],'composition_directory_bank_bounds_preserved':True,'original_part_counts_preserved':False,'new_part_counts':[r['new_parts']for r in report['mapping']],'parts_slack':report['parts_slack'],'reproduction':{'identical_builds':2,'candidate_sha256':sha(d/'ST0E_U1.ARC'),'runs':['selection_standing_sync02','selection_standing_sync03'],'second_run_also_checks_actual_COL0E_row16':True},'own_visual':bound(d/'visual_review.json'),'independent_reading':bound(W/'zero_audit/shibuki_selection8_relations01/report.json'),'builder_v4_scope_pending':True,'independent_candidate_pending':True,'new_mips_or_runtime':False,'bin_written':False,'active_pointer_changed':False}
    write(d/'proposal.json',proposal)
    files=[H/'sync_standing_selection.py',Path(__file__),src/'report.json',*[(ROOT/r['path'])for r in report['inputs']],W/'pack_selection_mirrors.py',ROOT/'src/psx_ui_atlas.py',ROOT/'src/psx_static_effect.py',ROOT/'src/psx_player.py',ROOT/'scripts/prepare_shibuki_ultimate_production.py',ROOT/'scripts/prepare_riko_ui.py',ROOT/'scripts/export_x_consistency.py',W/'zero_audit/shibuki_selection8_relations01/report.json']
    write(d/'INPUT_LOCK.json',{'files':[bound(p)for p in files]})
    write(d/'PREPARED_LOCK.json',{'files':[bound(p)for p in sorted(d.iterdir())if p.is_file()],'not_frozen':True})
    print(json.dumps({'candidate':sha(d/'ST0E_U1.ARC'),'proposal':sha(d/'proposal.json'),'lock':sha(d/'PREPARED_LOCK.json')}))
if __name__=='__main__':main()
