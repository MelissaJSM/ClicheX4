"""루트의 최종 실제 열람 수용을 결합하여 Rin222 검토 자원을 동결한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).parent/'rin_extension';P=D/'prepared_dash_saber01';ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da';assert sha(P/'PL01_U.ARC')==expected
q=read(P/'proposal.json');a=read(D/'final222_readback_audit.json');assert a['passed']and a['candidate_sha256']==expected
review={'source':'/root 메시지: 최종 normal/black packed4 + normal 원순서3/효과3 실제 열람 수용','actually_viewed_sheets':[rel(P/f'{form}_readback_{i:02}.png')for form in('normal','black')for i in(0,1)]+[rel(D/'dash_saber222_review'/f'{kind}_normal_{i:02}.png')for kind in('body_sequence','effects')for i in(0,1,2)],'root_unviewed':['black body_sequence 3판','black effects 3판'],'conclusion':'대기 대비 세부·체형 개선과 신규8 몸체/검기 접점에서 추가 확정 결함 없음. 후보 미술 수용.','runtime_verified':False,'user_accepted':False}
for p in review['actually_viewed_sheets']:assert(ROOT/p).exists()
write(D/'rin222_root_review.json',review)
q.update(ready_for_checkpoint_integration=True,root_art_review_pending=False,root_review=rel(D/'rin222_root_review.json'))
a.update(root_art_review_pending=False,root_review=rel(D/'rin222_root_review.json'),root_review_sha256=sha(D/'rin222_root_review.json'))
write(D/'final222_readback_audit.json',a);write(P/'proposal.json',q)
v=read(D/'dash_saber222_review/visual_review.json');v['root_final_packed_review_pending']=False;v['root_review']=rel(D/'rin222_root_review.json');write(D/'dash_saber222_review/visual_review.json',v)
a['visual_review_sha256']=sha(D/'dash_saber222_review/visual_review.json');write(D/'final222_readback_audit.json',a)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(D/'dash_saber_registered_v1/registration.json'),'independent_report':rel(D/'final222_readback_audit.json'),'independent_report_sha256':sha(D/'final222_readback_audit.json'),'root_review':rel(D/'rin222_root_review.json'),'root_review_sha256':sha(D/'rin222_root_review.json'),'technical_checks_passed':True,'ready_for_checkpoint_integration':True,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False,'cumulative_main_refs':222,'new_art_refs':8,'scope':'새 질풍아8+이전214의 검토 자원 동결. 루트 미술·원MIPS·독립·재현·정적 검사를 통과했으며 실제 게임/사용자 수용과 전체 미술 완료는 별도다.'}
write(P/'FROZEN.json',f);print(json.dumps({'arc':expected,'frozen_sha256':sha(P/'FROZEN.json'),'proposal_sha256':sha(P/'proposal.json')}))
