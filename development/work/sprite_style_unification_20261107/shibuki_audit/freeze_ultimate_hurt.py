"""Ultimate 피격13 v2의 원화·자원·독립·MIPS·루트검토를 동결한다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_hurt import P,PARENT,FINAL,REFS,LOCK_SHA,validate
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}

def main():
    d=H/'prepared_ultimate_hurt02';need(not(d/'FROZEN.json').exists(),'Already frozen')
    lk=json.loads((d/'PREPARED_LOCK.json').read_text('utf8'))
    for n,h in lk['files'].items():need(sha((d/n).read_bytes())==h,'Prepared changed '+n)
    for n,h in lk['source_scripts'].items():need(sha((H/n).read_bytes())==h,'Producer changed '+n)
    validate(P.read_bytes());need(sha((d/'PL02_U.ARC').read_bytes())==FINAL,'Candidate changed')
    paths=[H/'ultimate_hurt_v2_components_native_checks.json',H.parent/'zero_audit/shibuki_ultimate_hurt13_independent01/report.json',H.parent/'zero_audit/shibuki_ultimate_hurt13_independent01/source_report.json',H.parent/'zero_audit/shibuki_ultimate_hurt13_independent01/visual_review.json',H.parent/'root_review_checkpoint109.json',H/'ultimate_hurt_sequence01/report.json',H/'ultimate_hurt_sequence01/browser_verification.json',H/'ultimate_hurt_author_review02.json',H/'ultimate_hurt_v1_rejection.json']
    native,independent,source,visual,root,seq,browser,author,rejection=[json.loads(p.read_text('utf8'))for p in paths]
    need(native['passed']and independent['passed']and browser['passed'],'Checks not passed')
    need(native['resources']['PL02_U.ARC']['candidate_sha256']==FINAL,'Native asset binding')
    need(independent['candidate_sha256']==FINAL and independent['lock_sha256']==LOCK_SHA,'Independent lock binding')
    need(visual['candidate_sha256']==FINAL and visual['independent_report_sha256']==sha(paths[1].read_bytes()),'Visual report binding')
    need(root['arc_sha256']==FINAL and len(root['root_actually_viewed'])==14,'Root final14')
    for row in root['root_actually_viewed']:need(sha((ROOT/row['path']).read_bytes())==row['sha256'],'Root image changed')
    need(seq['candidate_sha256']==FINAL and seq['native_table_bytes_verified'],'Sequence source')
    need(browser['native_table_report_sha256']==sha(paths[5].read_bytes()),'Browser report binding')
    need(browser['html_sha256']==sha((H/'ultimate_hurt_sequence01/REVIEW.html').read_bytes()),'HTML changed')
    checks=sum(r['canvas_forms_checked']for r in browser['cases']);need(checks==710 and len(seq['native_step_checks'])==5,'Sequence coverage')
    need(author['candidate']['sha256']==FINAL and rejection['replacement']['sha256']==FINAL,'Author/v1 replacement binding')
    v=json.loads((d/'verification.json').read_text('utf8'))
    proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'target_lock_sha256':LOCK_SHA,'selected_visual_refs':list(REFS),'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'counts':independent['counts'],'native_MIPS_GPU':True,'independent_reader_no_producer_called':True,'independent_source_layers_reconstructed':True,'root_actual_packed_plates':8,'root_actual_ordered_plates':6,'author_actual_packed_plates':8,'author_actual_ordered_plates':6,'native_sequence_ids':[33,34,35,36,37],'native_sequence_pointer_and_step_bytes_exact':True,'browser_actual_canvas_checks':checks,'browser_loop_terminal_hold_play_pause_verified':True,'continuous_video_actually_watched_by_model':False,'reproduction_runs':v['reproduction_runs'],'invalid_input_rejections':v['rejection_count'],'bank_and_entry_boundaries_preserved':True,'new_gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'replaces_pending_status_in_initial_prepared_reports':True,'limitations':v['limitations']+['원MIPS/GPU와원표검사는 통과했다. 실제게임의 물리/외부상태/무적깜빡임/소리와 모든방향 피격은 미확인.','112..114는 기존정책 공통재킷110 실루엣을 보존하며 수영복 독립효과로 주장하지 않는다.','v1은111의 신규layer5 U경계로 반려. v2는 원타일256nibble 복제만으로 동일그림을 보존하여 해결했다.'],'next_scope':'Ultimate 등장133/135/137/138 의상 새원화·공통관절·광선/번개 파생. 수용idle와141/142 연결 보호.'}
    write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'source_lock_sha256':LOCK_SHA,'selected_visual_refs':list(REFS),'native_and_independent_passed':True,'root_packed_and_ordered_art_reviewed':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'frozen':sha((d/'FROZEN.json').read_bytes()),'verification':sha((d/'final_verification.json').read_bytes()),'candidate':FINAL}))

if __name__=='__main__':main()
