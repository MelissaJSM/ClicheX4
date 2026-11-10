"""회복4의 독립·원MIPS·원화·루트 실제 열람 증거를 고정한다."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_bank1_recovery128';V=R/'bank1_recovery240_review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
expected='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89'
assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
proofs={'source':R/'rin240_source_proof.json','native':R/'rin240_components_native_checks.json','guards':R/'rin240_guard_checks.json','timeline':V/'report.json','independent':D.parent/'nana_audit/rin240_independent_readback.json'}
assert sha(proofs['independent'])=='2de274591bca021cab66dc07c6d96126c565de535359477db44e0b12e1bd565c'
for p in proofs.values():
 j=read(p);assert j['passed'];assert j.get('candidate_sha256',expected)==expected
q=read(P/'proposal.json');plan=read(R/'rin240_components.json')
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC']
result=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
dump(R/'rin240_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':result})
proofs['static']=R/'rin240_static_binding_check.json'
paths=[P/f'{form}_readback_00.png'for form in('normal','black')]+[V/n for n in read(V/'report.json')['sheets']]
root_review={'source':'/root 메시지: packed 일반/레드2판과 회복 원순서 일반/레드4판 총6판 실제 열람. 새 외곽·프릴·부츠 선명도와125→128→107→95 연결에 추가 확정 결함을 찾지 못함.','actually_viewed_sheets':[{'path':rel(p),'sha256':sha(p)}for p in paths],'candidate_art_accepted_by_root':True,'runtime_verified':False,'user_accepted':False}
dump(R/'rin240_root_review.json',root_review)
visual={'actually_viewed':root_review['actually_viewed_sheets'],'observations':['패킹 결과2판과 원래 회복 순서4판을 직접 열람했다. 대기 기준의 머릿결·프릴·부츠 내부 명암이 추가되었고 목/장갑/발목에 새 확정 단절은 찾지 못했다.','고정1254→96 등록으로 원래 눈(143,154), 발바닥183, 전신 외곽 범위가 이미 일치했다. 전신 이동·국소 변형·기존 머리 덮기는 하지 않았다.','128~131은 원래 전체 표시가 동일한 회복 자세다. 새1원화를 원24타일 공유 스트림에 넣고10/10/9/9 파츠 구조를 보존했다.','원MIPS로 검증한 뇌신격 순서의 마지막 구간을 재사용하여125→128→129→130→131→107→98→95→87→86을 검토했다. 실제 외부상태/물리/가림 검증은 아니다.'],'limitations':read(V/'report.json')['limitations'],'root_final_review_pending':False,'root_review':rel(R/'rin240_root_review.json'),'runtime_verified':False,'user_accepted':False}
dump(V/'visual_review.json',visual)
audit={'passed':True,'candidate_sha256':expected,'cumulative_authored_refs':240,'incremental_refs':4,'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review':rel(V/'visual_review.json'),'visual_review_sha256':sha(V/'visual_review.json'),'previous236_preserved':True,'original24tile_shared_stream_retained':True,'unowned_tile15_exact':True,'bank1_slack':5668,'parts_bank5_slack':628,'independent_pending':False,'root_art_review_pending':False,'root_review':rel(R/'rin240_root_review.json'),'root_review_sha256':sha(R/'rin240_root_review.json'),'runtime_verified':False,'user_accepted':False}
dump(R/'final240_readback_audit.json',audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(R/'final240_readback_audit.json'),native_report=rel(proofs['native']),visual_report=rel(V/'visual_review.json'),root_art_review_pending=False,root_review=rel(R/'rin240_root_review.json'),ready_for_checkpoint_integration=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(R/'bank1_recovery128_registered_v1/registration.json'),'independent_report':rel(R/'final240_readback_audit.json'),'independent_report_sha256':sha(R/'final240_readback_audit.json'),'root_review':rel(R/'rin240_root_review.json'),'root_review_sha256':sha(R/'rin240_root_review.json'),'technical_checks_passed':True,'ready_for_checkpoint_integration':True,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False,'cumulative_main_refs':240,'new_art_refs':4,'scope':'새 뇌신격 회복128..131 네 참조와 이전236의 검토 자원 동결. 원래 순서/유지시간과24타일 공유 보존. 전수 실기·사용자 수용·전체 미술 완료는 별도다.'}
dump(P/'FROZEN.json',f)
print(json.dumps({'arc':expected,'frozen_sha256':sha(P/'FROZEN.json'),'proposal_sha256':sha(P/'proposal.json'),'recipe_sha256':sha(P/'static_effects.json')}))
