"""Rin228 기술근거와 루트 packed4 실제 미술 수용을 결합해 동결한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_special01';ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
expected='989b68597fa276164a16902806136f897c16ef3c1c81950b3b16fa039bede7a0';assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
q=read(P/'proposal.json');a=read(D/'final228_readback_audit.json');assert a['passed']and a['candidate_sha256']==expected
review={'source':'/root 메시지: 새 머리·커프·스커트·부츠 세부, 손/팔 연결과 대기 대비 체형 수용','actually_viewed_sheets':[rel(P/f'{form}_readback_{i:02}.png')for form in('normal','black')for i in(0,1)],'root_unviewed':'원표/검기14판은 에이전트 실제 열람이며 root는 미열람','candidate_art_accepted_by_root':True,'runtime_verified':False,'user_accepted':False}
write(D/'rin228_root_review.json',review)
v=read(D/'bank1_special228_review/visual_review.json');v.update(root_final_review_pending=False,root_review=rel(D/'rin228_root_review.json'));write(D/'bank1_special228_review/visual_review.json',v)
a.update(root_art_review_pending=False,root_review=rel(D/'rin228_root_review.json'),root_review_sha256=sha(D/'rin228_root_review.json'),visual_review_sha256=sha(D/'bank1_special228_review/visual_review.json'));write(D/'final228_readback_audit.json',a)
q.update(ready_for_checkpoint_integration=True,root_art_review_pending=False,root_review=rel(D/'rin228_root_review.json'));write(P/'proposal.json',q)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(D/'bank1_special_registered_v1/registration.json'),'independent_report':rel(D/'final228_readback_audit.json'),'independent_report_sha256':sha(D/'final228_readback_audit.json'),'root_review':rel(D/'rin228_root_review.json'),'root_review_sha256':sha(D/'rin228_root_review.json'),'technical_checks_passed':True,'ready_for_checkpoint_integration':True,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False,'cumulative_main_refs':228,'new_art_refs':6,'scope':'새 뇌신격 준비/회복6+이전222의 검토 자원 동결. 실제 게임/사용자 수용과 전체 미술 완료는 별도다.'}
write(P/'FROZEN.json',f);print(json.dumps({'arc':expected,'frozen_sha256':sha(P/'FROZEN.json'),'proposal_sha256':sha(P/'proposal.json')}))
