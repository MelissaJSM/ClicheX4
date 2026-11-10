"""Rin236 기술·독립 검사와 루트 packed4/정상효과3 실제 수용을 결합."""
from pathlib import Path
import hashlib,json
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_special02';ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
expected='0f6073c262c0b851a1330b86fec51d1bae62838a73241b3e9140a0b7727a5d1e';assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
q=read(P/'proposal.json');a=read(D/'final236_readback_audit.json');assert a['passed']and a['candidate_sha256']==expected and not a['independent_pending']
ip=ROOT/a['proofs']['independent']['path'];assert sha(ip)=='5974329f4b5da12c684304f7b22da0252ce6c14f85fa7b8a8e054be1bff42392'
review={'source':'/root 메시지: 최종 packed 일반/레드4판+정상효과3판 실제 열람, 앞팔/장갑과 원효과 연결 및 새 옷 세부 수용','actually_viewed_sheets':[rel(P/f'{form}_readback_{i:02}.png')for form in('normal','black')for i in(0,1)]+[rel(D/f'bank1_special236_review/effects_normal_{i:02}.png')for i in range(3)],'additional_source_registration_sheets':[rel(D/'bank1_special02_registered_v1/normal_comparison.png'),rel(D/'bank1_special02_registered_v1/normal_effects_comparison.png')],'root_unviewed':'원순서 일반/레드10판과 레드효과3판은 agent 열람이며 root 미열람','candidate_art_accepted_by_root':True,'runtime_verified':False,'user_accepted':False}
write(D/'rin236_root_review.json',review)
v=read(D/'bank1_special236_review/visual_review.json');v.update(root_final_review_pending=False,root_review=rel(D/'rin236_root_review.json'));write(D/'bank1_special236_review/visual_review.json',v)
a.update(root_art_review_pending=False,root_review=rel(D/'rin236_root_review.json'),root_review_sha256=sha(D/'rin236_root_review.json'),visual_review_sha256=sha(D/'bank1_special236_review/visual_review.json'));write(D/'final236_readback_audit.json',a)
q.update(ready_for_checkpoint_integration=True,root_art_review_pending=False,root_review=rel(D/'rin236_root_review.json'));write(P/'proposal.json',q)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(D/'bank1_special02_registered_v1/registration.json'),'independent_report':rel(D/'final236_readback_audit.json'),'independent_report_sha256':sha(D/'final236_readback_audit.json'),'root_review':rel(D/'rin236_root_review.json'),'root_review_sha256':sha(D/'rin236_root_review.json'),'technical_checks_passed':True,'ready_for_checkpoint_integration':True,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False,'cumulative_main_refs':236,'new_art_refs':8,'scope':'새 뇌신격 찌르기8+이전228 검토 자원 동결. 실제 게임/사용자 수용과 전체 미술 완료는 별도다.'}
write(P/'FROZEN.json',f);print(json.dumps({'arc':expected,'frozen_sha256':sha(P/'FROZEN.json'),'proposal_sha256':sha(P/'proposal.json'),'recipe_sha256':sha(P/'static_effects.json')}))
