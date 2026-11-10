"""Freeze a verified intermediate; final art/runtime approval remain distinct."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_movement_finish_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists()
expected='72d04d36dde42379a144dc4688b09c582e4c0f867bc70d5742c33bb65b75b42a'
audit_path=R/'final100_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'))
native_path=R/'rin100_components_native_checks.json';native=json.loads(native_path.read_text('utf8'))
guard_path=R/'rin100_guard_checks.json';guard=json.loads(guard_path.read_text('utf8'))
plan=json.loads((R/'rin100_components.json').read_text('utf8'));q=json.loads((P/'proposal.json').read_text('utf8'))
assert sha(P/'PL01_U.ARC')==audit['candidate_sha256']==guard['candidate_sha256']==q['after_sha256']==expected
assert audit['passed']and native['passed']and guard['passed']
assert audit['source_bin_sha256']==plan['source_sha256']and audit['source_arc_sha256']==plan['resources']['PL01_U.ARC']['before']
assert q['source_arc_sha256']==sha(ROOT/q['source_arc'])=='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
seen=[]
for form in('normal','black'):
 p=P/f'{form}_readback_00.png';seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
visual={'sheets':seen,'observations':['37의 머릿결과 커프·앞치마·부츠 묘사가 개선됐고 원래 눈 중심과 바닥 높이가 유지된다.','45는 낮은 몸통 기울기와 긴 뒤 리본을 유지하며, 머리만1px 내려 원래 눈 높이에 정합했다. 새로운 허리·치맛단 명암이 목·팔과 연결된다.','193 새 원화에 있던 전신 왼쪽 밀림을3px 보정하고 머리(+1,+1)를 별도로 정합했다. 바닥·눈이 원래 기준으로 돌아왔고 옛 머리나 옷을 복사하지 않았다.','일반·레드에서 목/허리의 뚜렷한 단절은 보이지 않았다.45의 신발 마지막 행 중심은 원래보다1.5px 오른쪽인 작은 차이가 남는다.'],'registration':rel(R/'movement_finish_registered_v1/registration.json'),'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=R/'movement100_visual_review.json';dump(vp,visual)
audit.update(visual_review_pending=False,visual_review=rel(vp),visual_review_sha256=sha(vp),root_final_packed_review_pending=True);dump(audit_path,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(audit_path),native_report=rel(native_path),guard_report=rel(guard_path),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_review_pending=True,root_final_packed_review_pending=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));assert l['prepared_count']==97
(R/'progress_ledger97_snapshot.json').write_bytes(lp.read_bytes());l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(l['new_art_prepared_refs'])==100
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=100,latest_scope=q['scope'],latest_proof='final100_readback_audit.json',latest_native='rin100_components_native_checks.json',next_page='hurt_lowhp01',next_page_scope='피격135/139와 저체력149/152의 새4몸체·원래 효과를17참조로 동기화한다. 원화 생성 전이며 현재그림은 보존한다.')
dump(lp,l)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'guard_sha256':sha(guard_path),'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'movement_finish_registered_v1/registration.json'),'cumulative_main_refs':100,'incremental_main_refs':3,'new_authored_body_keys':3,'composition_bytes_exact':True,'bank0_slack':4190,'bank1_slack':7176,'hidden_global_cleanup':False,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
dump(P/'FROZEN.json',f);print(json.dumps(f))
