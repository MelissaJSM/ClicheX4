"""새 뇌신격8 후보의 기술·원화·실제 열람 근거를 묶는다."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_bank1_special02';V=R/'bank1_special236_review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
expected='0f6073c262c0b851a1330b86fec51d1bae62838a73241b3e9140a0b7727a5d1e';assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
proofs={'source':R/'rin236_source_proof.json','native':R/'rin236_components_native_checks.json','guards':R/'rin236_guard_checks.json','timeline':V/'report.json'}
ind=D.parent/'nana_audit/rin236_independent_readback.json'
if ind.exists():proofs['independent']=ind
for k,p in proofs.items():
 j=read(p);assert j['passed'];assert j.get('candidate_sha256',expected)==expected
q=read(P/'proposal.json');plan=read(R/'rin236_components.json');base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];result=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
dump(R/'rin236_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':result});proofs['static']=R/'rin236_static_binding_check.json'
paths=[P/f'{form}_readback_{i:02}.png'for form in('normal','black')for i in(0,1)]+[V/n for n in read(V/'report.json')['sheets']]
visual={'actually_viewed':[{'path':rel(p),'sha256':sha(p)}for p in paths],'unviewed_generated_sheets':[],'observations':['실제 패킹 일반/레드4판, 원뇌신격 순서10판, 실제 팔레트5 원검기 합성6판 총20판을 직접 열람했다. 새8 몸체의 머릿결·커프·앞치마·부츠가 대기와 세부 수준이 가까워지고 추가 확정 목/장갑/무릎 단절을 찾지 못했다.','108/110은 새 원화가 전체3px 낮게 등록돼 전신y−3으로 원발바닥183을 회복했다. 112/119는y를 옮기지 않았다. 전체 x정합−1/+1/−1/+1 외 국소 몸체 변형은 없다.','119의 눈은 원화 청록92와 남색99 투표가 경쟁하던 정확 한 셀(135,154)을 원화의 청록 표본으로 보존했다. 머리/옷을 예전 그림으로 덮거나 없는 새 색을 채우지 않았다.','검기12짝의 전기 시작/가림과 연속 찌르기를 비교했다. 소매가 원래보다 세밀해졌고 새로운 명백한 접점 틈은 못 찾았다. 실제 게임의 외부효과 종료·가림·물리까지 검사한 것은 아니다.','후반128~131은 아직 예전 단색 머리·소매·치마이므로 별도 단독원화 보완이 필요하다.'],'limitations':read(V/'report.json')['limitations'],'root_final_review_pending':True,'runtime_verified':False,'user_accepted':False}
dump(V/'visual_review.json',visual)
audit={'passed':True,'candidate_sha256':expected,'cumulative_authored_refs':236,'incremental_refs':8,'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review':rel(V/'visual_review.json'),'visual_review_sha256':sha(V/'visual_review.json'),'previous228_preserved':True,'eight_original_shared_streams_retained':True,'twelve_support_effects_consumed_full_tiles_preserved':True,'bank1_slack':5566,'parts_bank5_slack':520,'independent_pending':'independent'not in proofs,'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False}
dump(R/'final236_readback_audit.json',audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(R/'final236_readback_audit.json'),native_report=rel(proofs['native']),visual_report=rel(V/'visual_review.json'),root_art_review_pending=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
dump(P/'INPUT_FROZEN.json',{'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(R/'bank1_special02_registered_v1/registration.json'),'own_technical_checks_passed':True,'independent_pending':'independent'not in proofs,'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False,'scope':'4새원화→8정확공유 참조를 이전228에 추가한 검토용236. 실제 원MIPS/원화재구성/20판 실제 열람 완료; 독립 결과·루트 미술·실기·사용자수용은 별도로 기록한다.'})
print(json.dumps({'candidate_sha256':expected,'audit':rel(R/'final236_readback_audit.json'),'independent_pending':audit['independent_pending']}))
