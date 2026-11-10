"""Freeze verified17 addition without claiming game acceptance or complete unification."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_hurt_lowhp_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists()
expected='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
ap=R/'final117_readback_audit.json';audit=json.loads(ap.read_text('utf8'))
np=R/'rin117_components_native_checks.json';native=json.loads(np.read_text('utf8'))
gp=R/'rin117_guard_checks.json';guard=json.loads(gp.read_text('utf8'))
plan=json.loads((R/'rin117_components.json').read_text('utf8'));q=json.loads((P/'proposal.json').read_text('utf8'))
assert sha(P/'PL01_U.ARC')==audit['candidate_sha256']==guard['candidate_sha256']==q['after_sha256']==expected
assert audit['passed'] and native['passed'] and guard['passed']
assert audit['source_bin_sha256']==plan['source_sha256'] and audit['source_arc_sha256']==plan['resources']['PL01_U.ARC']['before']
seen=[]
for form in ('normal','black'):
 for i in range(5):
  p=P/f'{form}_readback_{i:02}.png';seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
visual={'sheets':seen,'observations':['일반·레드10시트를 실제 열람했다.135/139의 머릿결, cyan/붉은 눈, 옷깃, 장갑, 앞치마와 부츠 명암이 대기 기준에 가까워졌다.','139는 새 원화에서 무릎을 약2px 더 굽힌 피격 자세다. 루트가 native 비교에서 자연스러운 피격 범위로 판단했고 추가 강제 변형 없이 사용했다.','135의 눈은 원래(152,143),139는 새 원화 표본이 확인된(158,147)에 복원했다.149 눈은 새 원화표본18개에 근거하며152 전신은x+3 정합했다.','136/137 흰 불꽃과140/141 별도 번개의 모양·위치가 유지된다.138/142/143/144/145의 몸체형 섬광은 새머리·팔·치마·부츠 외곽과 일치한다.','149..151과152..154의 각 같은 몸체/자세 연결이 유지된다. 바닥y는 원래 기준이며 무릎·치맛단의 뚜렷한 단절은 보이지 않았다.','CLUT2 번개가 검게 보이는 것은 저장 팔레트 미리보기 한계다. 실제 게임의 전기 색상 검증으로 주장하지 않는다.'],'root_native_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=R/'hurt117_visual_review.json';dump(vp,visual)
audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True);dump(ap,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(ap),native_report=rel(np),guard_report=rel(gp),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_review_pending=True,root_final_packed_review_pending=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));assert l['prepared_count']==100
(R/'progress_ledger100_snapshot.json').write_bytes(lp.read_bytes())
l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(l['new_art_prepared_refs'])==117
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit'] if r not in q['new_art_refs']]
l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=117,latest_scope=q['scope'],latest_proof='final117_readback_audit.json',latest_native='rin117_components_native_checks.json',next_page=None,next_page_scope='남은 기본검격·특수기·탑승·등장 체형/질감 장부에서 큰 차이 순으로 다음 원화 묶음을 정한다. 전수 완료 아님.')
dump(lp,l)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'independent_sha256':sha(ap),'native_sha256':sha(np),'guard_sha256':sha(gp),'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'hurt_registered_v2/registration.json'),'cumulative_main_refs':117,'incremental_main_refs':17,'new_authored_body_keys':4,'derived_effect_refs':9,'same_body_lowhp_alias_refs':4,'bank0_slack':2432,'bank1_slack':7176,'hidden_global_cleanup':False,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
dump(P/'FROZEN.json',f);print(json.dumps(f))
