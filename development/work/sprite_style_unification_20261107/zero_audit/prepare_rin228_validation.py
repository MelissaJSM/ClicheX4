"""Rin228의 실제 시각 검토와 독립/네이티브/정적 검사를 결합한다."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_bank1_special01';V=R/'bank1_special228_review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
read=lambda p:json.loads(p.read_text('utf8'))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
expected='989b68597fa276164a16902806136f897c16ef3c1c81950b3b16fa039bede7a0';assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
proofs={'independent':D.parent/'nana_audit/rin228_independent_readback.json','source':R/'rin228_source_proof.json','native':R/'rin228_components_native_checks.json','guards':R/'rin228_guard_checks.json','native_timeline':V/'report.json'}
for k,p in proofs.items():
 j=read(p);assert j['passed'];assert j.get('candidate_sha256',expected)==expected
q=read(P/'proposal.json');plan=read(R/'rin228_components.json');base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];result=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
dump(R/'rin228_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':result});proofs['static']=R/'rin228_static_binding_check.json'
paths=[P/f'{form}_readback_{i:02}.png'for form in('normal','black')for i in(0,1)]+[V/f'effects_{form}_{i:02}.png'for form in('normal','black')for i in(0,1)]+[V/f'sequence95_{form}_{i:02}.png'for form in('normal','black')for i in range(5)]
visual={'actually_viewed':[{'path':rel(p),'sha256':sha(p)}for p in paths],'unviewed_generated_sheets':[f'sequence96_{form}_{i:02}.png'for form in('normal','black')for i in range(5)],'observations':['실제 패킹 일반/레드4판과 원뇌신격 순서10판, 실제 팔레트5 원검기 합성4판 총18판을 직접 열람했다. 새 머리결·커프·앞치마·부츠가 대기와 세부 수준이 가까워지고, 새6 몸체에서 추가 확정 목/장갑/무릎 단절을 찾지 못했다.','101 앞팔(-1,+1),105 앞팔(0,+2)은 새 원화 의미영역과 내부 투명을 함께 이동해 원 손 높이로 정합했다. 91/93은 전신 등록 후 그대로이며 구형 머리 덮기/색 채움은 없다.','91/93 주변 전기와101/103 뒤쪽 전기는 원효과 그대로다. 새6의 검기 접점에 추가 확정 틈은 못 찾았으나 실제 동적가림·효과 삭제를 검사한 것은 아니다.','순서판에서 다음108/110/112/119/128 등의 구형 단색 머리·팔·치마가 새 준비 자세와 대비되는 잔여 작업임을 확인했다. 다음 108/110/112/119 원화 입력을 준비했다.'],'limitations':read(V/'report.json')['limitations'],'root_final_review_pending':True,'runtime_verified':False,'user_accepted':False}
dump(V/'visual_review.json',visual)
audit={'passed':True,'candidate_sha256':expected,'cumulative_authored_refs':228,'incremental_refs':6,'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review':rel(V/'visual_review.json'),'visual_review_sha256':sha(V/'visual_review.json'),'previous222_preserved':True,'three_original_shared_streams_retained':True,'five_support_effects_consumed_full_tiles_preserved':True,'bank1_slack':6094,'parts_bank5_slack':376,'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False}
dump(R/'final228_readback_audit.json',audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(R/'final228_readback_audit.json'),native_report=rel(proofs['native']),visual_report=rel(V/'visual_review.json'),root_art_review_pending=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(R/'bank1_special_registered_v1/registration.json'),'technical_checks_passed':True,'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False,'scope':'4새원화→6정확공유 참조를 이전222에 추가한 검토용228. 기술검사와18판 실제 열람 완료; 루트 최종 미술 검토/실기/사용자수용은 별도다.'}
dump(P/'INPUT_FROZEN.json',f);print(json.dumps(f))
