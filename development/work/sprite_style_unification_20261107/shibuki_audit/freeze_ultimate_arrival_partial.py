"""등장8만 동결한다. 보류135 및 전체 프로젝트 미완료 상태를 유지한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from prepare_arrival_partial_candidate import D,P,PARENT,FINAL,REFS,validate
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
 need(not(D/'FROZEN.json').exists(),'Already frozen');lk=json.loads((D/'SOURCE_LOCK.json').read_text('utf8'));validate(P.read_bytes(),lk)
 prepared=json.loads((D/'PREPARED_LOCK.json').read_text('utf8'))
 for name,h in prepared['files'].items():need(sha((D/name).read_bytes())==h,'Prepared file changed '+name)
 need(sha((D/'PL02_U.ARC').read_bytes())==FINAL,'Candidate changed')
 paths=[H/'ultimate_arrival_partial_components_native_checks.json',H.parent/'zero_audit/shibuki_ultimate_arrival8_independent01/report.json',H.parent/'zero_audit/shibuki_ultimate_arrival8_independent01/visual_review.json',H.parent/'root_review_checkpoint116.json',H/'ultimate_arrival_sequence01/report.json',H/'ultimate_arrival_sequence01/browser_verification.json',H/'ultimate_arrival_author_review01.json']
 native,ind,vis,root,seq,web,author=[json.loads(p.read_text('utf8'))for p in paths]
 need(native['passed']and ind['passed']and web['passed'],'Pending check');need(native['resources']['PL02_U.ARC']['candidate_sha256']==FINAL,'Native asset binding');need(ind['candidate_sha256']==FINAL and ind['source_lock_sha256']==sha((D/'SOURCE_LOCK.json').read_bytes()),'Independent source binding');need(ind['protected_ref135_exact']and ind['shared132_all_raw_layers_parts_exact'],'Protected frames changed')
 need(vis['candidate_sha256']==FINAL and vis['independent_report_sha256']==sha(paths[1].read_bytes()),'Independent visual binding');need(root['arc_sha256']==FINAL and len(root['root_actually_viewed'])==16,'Root review16 mismatch')
 for q in root['root_actually_viewed']:need(sha((ROOT/q['path']).read_bytes())==q['sha256'],'Root reviewed image changed')
 need(seq['candidate_sha256']==FINAL and seq['native_table_bytes_verified'],'Native table binding');need([s['id']for s in seq['sequences']]==[2,95,96],'Sequence scope');need(web['native_table_report_sha256']==sha(paths[4].read_bytes())and web['html_sha256']==sha((H/'ultimate_arrival_sequence01/REVIEW.html').read_bytes()),'Browser source binding');count=sum(r['canvas_forms_checked']for r in web['cases']);need(count==406,'Browser coverage');need(author['candidate']['sha256']==FINAL,'Author binding')
 for group in author['actually_viewed'].values():
  for q in group:need(sha((ROOT/q['path']).read_bytes())==q['sha256'],'Author image changed')
 v=json.loads((D/'verification.json').read_text('utf8'));need(len(v['reproduction_runs'])==3 and v['rejection_count']==12,'Build validation missing')
 proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'source_lock_sha256':sha((D/'SOURCE_LOCK.json').read_bytes()),'selected_visual_refs':list(REFS),'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'counts':ind['counts'],'native_MIPS_GPU':True,'native_refs':list(REFS),'native_isolated_not_gameplay':True,'independent_reader_no_producer_called':True,'root_actually_viewed_packed':6,'root_actually_viewed_partial':4,'root_actually_viewed_ordered':6,'native_sequence_ids':[2,95,96],'native_step_bytes_exact':29,'offline_canvas_form_checks':count,'reproduction_runs':v['reproduction_runs'],'rejection_count':12,'protected135_incomplete_parent_exact':True,'protected132_shared_stream_split_exact':True,'bank_and_entry_boundaries_preserved':True,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'initial_pending_flags_superseded':True,'limitations':['135는 도구 거부 이후 재시도하지 않았고 부모 그대로 보존했다. 등장 전체 재작화 완료가 아닌8참조 부분 동결이다.','원표95/96에 이어지는 구형95/96은 이번 변경 범위 밖이며 큰 단색 머리/의상 면이 남아 있다.','136은 새 발 두 모듈 y+1로 부모 바닥에 등록했다. 새 상부 무릎/눈축은 exact이며 실제게임 접촉/모든방향은 아직 미검증이다.','원표 검토는 고정 두 의상 표시와 실제 step 유지 호출수만 재현했다. 실제 임시 아머 전환·효과객체·물리·소리/종료상태를 재현한 게임 실기가 아니다.','130/131의 기존 공통 실루엣 정책과140~142 수용 대기 연결은 유지한다.136/139는 별도 새 포즈이며 원래 단순별칭이라고 주장하지 않는다.'],'next_scope':'Ultimate 승리204..207·정면귀환156..158 및 전폼 잔여 특수/차량'}
 write(D/'final_verification.json',proof);write(D/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(D.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'source_lock_sha256':sha((D/'SOURCE_LOCK.json').read_bytes()),'selected_visual_refs':list(REFS),'native_and_independent_passed':True,'root_packed_partial_ordered_reviewed':True,'incomplete_ref135_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
 print(json.dumps({'frozen':ev(D/'FROZEN.json'),'final_verification':ev(D/'final_verification.json'),'candidate':FINAL}))
if __name__=='__main__':main()
