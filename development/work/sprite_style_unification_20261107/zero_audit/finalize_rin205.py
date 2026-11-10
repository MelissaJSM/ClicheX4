"""용염인 준비·회복3 및 사다리진입2의 검증된 미술 후보를 동결."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_followthrough01';V=R/'followthrough205_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8'
proofs={k:R/f for k,f in [('independent','final205_readback_audit.json'),('native','rin205_components_native_checks.json'),('guard','rin205_guard_checks.json')]}
checks={k:json.loads(p.read_text('utf8'))for k,p in proofs.items()};q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin205_components.json').read_text('utf8'));browser=json.loads((V/'browser_verification.json').read_text('utf8'))
assert all(j['passed']for j in checks.values())and browser['passed'];assert sha(P/'PL01_U.ARC')==q['after_sha256']==checks['independent']['candidate_sha256']==expected
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch']);dump(R/'rin205_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
m=json.loads((V/'manifest.json').read_text('utf8'));paths=[V/name for name in m['sheets']]+[P/f'{form}_readback_{n:02}.png'for form in('normal','black')for n in(0,1)];assert len(paths)==10
visual={'sheets':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in paths],
 'observations':['패킹 일반·레드4판, 실제 표101/102/93 순서 일반·레드6판을 직접 열람했다. 새 리본이 기존80px 검토창 밖으로 나오는 것을 발견해 미리보기만104×96 고정창으로 다시 만들고 전체 알파 보존을 검사했다.',
 '146의 짧은 웅크림과156/197의 내려간 정강이가 첫 원화에서 길어졌으므로 새 하체를 국소 재작화했다.158 양발 간격도 함께 보완했다. 새 머리·손·상의는 최초 정밀 원화에서 고정했고, 다른 원화로 덮거나 전신축소/행삭제하지 않았다.',
 '네 자세의 실제 최저 발Y는 원래값과 같다. 마지막 부츠 접점은 같은 새 원화의1px 평행이동과156의 같은 원화 첫 이음행 유지로 등록했다. 실제 관절/장갑/무릎 연결에서 추가 확정 단절은 찾지 못했다.',
 '197과212는 원래 전체 표시가 정확히 같아 동일한 새197 원화를 적용했다.199/202 및 그 사본은 그대로이므로 사다리 전체 미술 완료로 세지 않는다.',
 '용염인101은86/87/144/146을 거쳐148/150/152/154로 간다. 회복102의156/158/160, 사다리93의197→199→202…→212→196→174/175를 원표 순서로 검토했다. 효과/이벤트가 실제 게임에서 시퀀스를 끝내거나 바꾸는 동작은 이 자료에서 재현하지 않는다.'],
 'limitations':m['limitations'],'browser_verification':rel(V/'browser_verification.json'),'browser_scope':'오프라인60표 위치·정수4배·JS오류 없음. 연속 동영상 육안 및 실제 게임 미실행.',
 'root_registered_art_review_pending':False,'root_final_packed_review_pending':False,'root_review_evidence':'root 메시지: 등록 일반/레드2판, 최종 packed4판과 원표6판을 실제 열람하고 새5표시 미술후보 수용. 장갑/하체/리본 추가 확정 끊김 없음. checkpoint26 기록 예정.',
 'user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit=checks['independent'];audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=False,static_binding_proof=rel(R/'rin205_static_binding_check.json'));dump(proofs['independent'],audit)
scope='용염인 준비146·공중회복156·지상회복158와 사다리진입197/212: 새4자세·정확사본1, 누적205. 이전200·지원6의 전체소비31타일·부분VRAM8·정적몸체 보존. 독립reader·원MIPS/GPU·8거부·정적미술/root 검토 통과. 전수실기·사용자수용은 미확인.'
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(proofs['independent']),native_report=rel(proofs['native']),guard_report=rel(proofs['guard']),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_art_review_pending=False,full_art_unification_complete=False,scope=scope);dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==200;(R/'progress_ledger200_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==205;ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
ledger['limitations']=[s for s in ledger['limitations']if '새 원화 누적200'not in s]+['새 원화 누적205의 전수 실제 플레이와 사용자 최종 수용은 미확인이다. root 정적미술 검토와 원MIPS/GPU 검사는 구분한다.']
ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=205,latest_scope=scope,latest_proof='final205_readback_audit.json',latest_native='rin205_components_native_checks.json',next_page=None,next_page_scope='사다리199/202 두키의7참조·질풍아155..172·공유지상특수·등장/탑승 잔여를 이어간다.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'followthrough_registered_v1/registration.json'),'cumulative_main_refs':205,'incremental_main_refs':5,'body_refs':5,'shared_support_refs_preserved':6,'shared_entire_consumed_tiles_preserved':31,'bank0_slack':2558,'bank1_slack':6100,'hidden_global_cleanup':False,'root_art_review_pending':False,'user_accepted':False,'runtime_verified':False};dump(P/'FROZEN.json',f);print(json.dumps(f))
