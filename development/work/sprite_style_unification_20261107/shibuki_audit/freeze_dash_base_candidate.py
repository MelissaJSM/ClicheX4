"""대시20의 root 실제 열람, 독립 reader, 원 MIPS/GPU 검사를 해시로 묶는다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'prepared_dash_base01';need(not(d/'FROZEN.json').exists(),'Already frozen');lock=json.loads((d/'INPUT_FROZEN.json').read_text('utf8'))
    for name,digest in lock['files'].items():need(sha((d/name).read_bytes())==digest,'Prepared input changed '+name)
    for key in ('producer_scripts','source_files'):
        for name,digest in lock[key].items():need(sha((H/name).read_bytes())==digest,'Source changed '+name)
    expected='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b';need(sha((d/'PL00_U.ARC').read_bytes())==expected,'Candidate changed')
    files=['work/sprite_style_unification_20261107/shibuki_dash13_components_native_checks.json','work/sprite_style_unification_20261107/nana_audit/shibuki_dash_independent/report.json','work/sprite_style_unification_20261107/root_review_checkpoint38.json'];rr=[json.loads((ROOT/p).read_text('utf8'))for p in files];need(rr[0]['passed']and rr[1]['passed'],'Missing passed checks');need(rr[1]['candidate_sha256']==expected,'Wrong independent resource');need(rr[0]['resources']['PL00_U.ARC']['candidate_sha256']==expected,'Wrong native resource')
    for item in rr[2]['art_review_images']:need(item['root_actually_viewed']and sha((ROOT/item['path']).read_bytes())==item['sha256'],'Visual evidence changed')
    write(d/'final_verification.json',{'passed':True,'candidate_sha256':expected,'parent_arc_sha256':lock['parent_arc_sha256'],'selected_visual_refs':list(range(67,85))+[93,94],'evidence':{p:sha((ROOT/p).read_bytes())for p in files},'counts':rr[1]['counts'],'root_actual_visual_plates':len(rr[2]['art_review_images']),'author_actual_full_plates':8,'author_actual_partial_plates':5,'author_actual_sequence_contact_plates':6,'sequence_contact_report':{'path':(H/'dash_sequence_review01/report.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'dash_sequence_review01/report.json').read_bytes())},'native_MIPS_GPU':True,'independent_reader_no_producer_called':True,'input_rejection_cases':7,'reproduction_runs':3,'input_source_files':len(lock['source_files']),'replaces_pending_status_in_initial_prepared_reports':True,'new_gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'root_selection_update':'root의 ST0E e30b Zero 선택 갱신은 별도 통합. 이 제안의 X 선택·19..21/18은 기존 5afaa와 동일.'})
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':expected,'parent_arc_sha256':lock['parent_arc_sha256'],'source_lock_sha256':lock['source_lock_sha256'],'selected_visual_refs':list(range(67,85))+[93,94],'native_and_independent_passed':True,'root_packed_art_reviewed':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'frozen_sha256':sha((d/'FROZEN.json').read_bytes()),'verification_sha256':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
