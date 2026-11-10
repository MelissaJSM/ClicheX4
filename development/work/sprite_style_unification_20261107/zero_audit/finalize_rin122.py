"""Freeze the five-reference first-swing checkpoint, not the entire art project."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_ground_first_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists()
expected='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1'
ap=R/'final122_readback_audit.json';audit=json.loads(ap.read_text('utf8'))
np=R/'rin122_components_native_checks.json';native=json.loads(np.read_text('utf8'))
gp=R/'rin122_guard_checks.json';guard=json.loads(gp.read_text('utf8'))
plan=json.loads((R/'rin122_components.json').read_text('utf8'));q=json.loads((P/'proposal.json').read_text('utf8'))
assert sha(P/'PL01_U.ARC')==audit['candidate_sha256']==guard['candidate_sha256']==q['after_sha256']==expected
assert audit['passed']and native['passed']and guard['passed']
seen=[]
for form in ('normal','black'):
 for i in range(2):
  p=P/f'{form}_readback_{i:02}.png';seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
for name in ('normal_effects.png','black_effects.png','normal_sequence_00.png','normal_sequence_01.png','normal_sequence_02.png'):
 p=R/'ground122_contact_review'/name;seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
visual={'sheets':seen,'observations':['일반·레드 재추출4장과 동일 원점 검기 비교2장, 일반 전체 첫타 연결3장을 직접 열람했다.','새62/63/65/67의 머릿결, 옷깃, 커프, 앞치마와 부츠 명암이 기존 대기 및 새61에 가까워졌다.63의 손과65의 전완을 원래 접점 쪽으로 정합하여 목·손목·무릎의 뚜렷한 단절은 보이지 않는다.','62→63에서 위로 들린 손이 앞쪽으로 내려오고65→67→69에서 낮게 이어진다.67과69의 새 그림은 정확히 같으며 원래 동일 자세 관계를 유지한다.','63/64·65/66·67/68·69/70은 동일 원점에서 검기와 몸체를 함께 보았다. 새 그림으로 인한 큰 추가 틈은 보이지 않았으나 외부 검기 객체의 실제 위치와 색상은 런타임 검증이 필요하다.','71 이후 후반 자세는 얼굴·옷 내부가 아직 단순하다. 원래 몸체·검기 순서를 보존했고 다음 원화 작업 대상으로 유지한다. 전체 첫타 그림체 통일 완료로 세지 않는다.'],'root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False,'simulation_review':rel(R/'ground122_contact_review/REVIEW.html'),'simulation_browser_proof':rel(R/'ground122_contact_review/browser_verification.json'),'simulation_not_game':True}
vp=R/'ground122_visual_review.json';dump(vp,visual)
audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True);dump(ap,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(ap),native_report=rel(np),guard_report=rel(gp),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_review_pending=True,root_final_packed_review_pending=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==117
(R/'progress_ledger117_snapshot.json').write_bytes(lp.read_bytes())
ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==122
ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=122,latest_scope=q['scope'],latest_proof='final122_readback_audit.json',latest_native='rin122_components_native_checks.json',next_page=None,next_page_scope='첫타 후반71..82 등과 벽검격50/51/54/57을 다음 우선 원화로 준비한다. 전체 미술 통일 완료 아님.')
dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'independent_sha256':sha(ap),'native_sha256':sha(np),'guard_sha256':sha(gp),'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'ground_registered_v1/registration.json'),'cumulative_main_refs':122,'incremental_main_refs':5,'new_authored_body_keys':4,'exact_alias_refs':1,'bank0_slack':2022,'bank1_slack':7176,'hidden_global_cleanup':False,'joint_original_pool62_63':list(range(9,28)),'shared61_and_original64_full_tiles_preserved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
dump(P/'FROZEN.json',f);print(json.dumps(f))
