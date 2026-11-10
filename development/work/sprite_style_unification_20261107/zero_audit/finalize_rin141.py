"""Freeze 19 authored ground/wall refs after bounded native and visual review."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];R=D/'rin_extension';P=R/'prepared_ground_wall_v1';V=R/'ground_wall141_review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists()
expected='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
ap=R/'final141_readback_audit.json';audit=json.loads(ap.read_text('utf8'))
np=R/'rin141_components_native_checks.json';native=json.loads(np.read_text('utf8'))
gp=R/'rin141_guard_checks.json';guard=json.loads(gp.read_text('utf8'))
plan=json.loads((R/'rin141_components.json').read_text('utf8'));q=json.loads((P/'proposal.json').read_text('utf8'))
assert sha(P/'PL01_U.ARC')==audit['candidate_sha256']==guard['candidate_sha256']==q['after_sha256']==expected
assert audit['passed']and native['passed']and guard['passed']
names=[f'readback_{i:02}.png'for i in range(5)]
for form in ('normal','black'):
 names.extend(f'ground_{form}_effects_{i:02}.png'for i in range(2))
 names.extend(f'wall_{form}_effects_{i:02}.png'for i in range(3))
 names.extend(f'{g}_transitions_{form}.png'for g in ('ground','wall'))
names.append('head_band_comparison.png')
seen=[{'path':rel(V/n),'sha256':sha(V/n),'actually_viewed':True}for n in names]
review_manifest=json.loads((V/'manifest.json').read_text('utf8'))
visual={'sheets':seen,'observations':[
 '최종 ARC의19자세를 일반·레드 전후5장으로 직접 열람했다. 머릿결, 옷깃, 커프, 앞치마·치맛단, 부츠 명암이 이전 단순면보다 대기 기준에 가까워졌고 목·허리·무릎의 뚜렷한 단절은 보이지 않는다.',
 '지상·벽 정적 검기 합성10장을 직접 열람했다. 71/72의 검기 시작과 손 사이 작은 간격 및 후반 소멸 입자는 이전에도 존재한다. 새 몸체가 검기와 추가로 크게 떨어진 현상은 보이지 않는다. 벽 중간 자세는 검기가 장갑을 가려 손 전체 픽셀을 이 합성만으로 확인할 수 없다.',
 '고정 원점 순서 스트립 일반·레드4장에서69→71→73,82→131→133과벽50→51→54→57→56→53을 비교했다.71/73의 머리 폭이 갑자기 커지는 뚜렷한 불연속은 보이지 않는다. 회복133은 기존 원화이므로 아직 전체 첫타 모든 자세의 동일 상세 수준 완료를 주장하지 않는다.',
 '71/73의 눈 위 머리 최대 행폭은 기존21→새20px, 대기20px이다. 눈~정수리 높이는 대기10 대비 새11px이며 얼굴 피부bbox는 새5×8로 대기5×8과 같다. 보닛·볼 명암과1px 높이 차이 때문에 크게 읽힐 수 있다. 이 값은 선택한 눈 위 구간만의 측정이며 전체 머리 광학 면적이나 미술 수용을 자동 판정하지 않는다.'
 ],'head_metrics':review_manifest['head_metrics'],'root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False,'simulation_review':rel(V/'REVIEW.html'),'simulation_browser_proof':rel(V/'browser_verification.json'),'simulation_browser_scope':'60개 위치의 오프라인 로딩·정수4배·JS오류 없음 검사. 연속 애니메이션의 실제 육안 시청 또는 게임 실기와 동일하지 않다.','limitations':review_manifest['limitations']}
vp=V/'visual_review.json';dump(vp,visual)
audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True);dump(ap,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(ap),native_report=rel(np),guard_report=rel(gp),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_review_pending=True,root_final_packed_review_pending=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==122
(R/'progress_ledger122_snapshot.json').write_bytes(lp.read_bytes())
ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==141
ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=141,latest_scope=q['scope'],latest_proof='final141_readback_audit.json',latest_native='rin141_components_native_checks.json',next_page=None,next_page_scope='남은 지상2타/회복83..109·130 등, 공중검격·탑승 등 전수 장부를 계속 검토한다. 전체 미술 통일 완료 아님.')
dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'independent_sha256':sha(ap),'native_sha256':sha(np),'guard_sha256':sha(gp),'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'after122_registered_v1/registration.json'),'cumulative_main_refs':141,'incremental_main_refs':19,'new_authored_body_keys':8,'exact_alias_refs':11,'shared_support_refs_preserved':11,'shared_entire_consumed_tiles_preserved':52,'bank0_slack':3146,'bank1_slack':7266,'hidden_global_cleanup':False,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
dump(P/'FROZEN.json',f);print(json.dumps(f))
