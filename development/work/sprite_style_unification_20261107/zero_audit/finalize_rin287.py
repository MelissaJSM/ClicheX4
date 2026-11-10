"""체이서28의 원화·독립·원MIPS·루트 미술근거를 동결한다."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_chaser01';expected='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
proofs={'source_reproduction_rejections':R/'rin287_source_proof.json','native_gpu':R/'rin287_components_native_checks.json','independent':D.parent/'nana_audit/rin287_independent_readback.json','native_timeline':R/'chaser287_review/report.json'}
assert sha(proofs['independent'])=='9a622f76f2d355116896e61e1b37729cae2d532fef486c718cec43ffbd678fd8'
for p in proofs.values():
 j=read(p);assert j['passed'] and j.get('candidate_sha256',expected)==expected
review=D.parent/'root_review_checkpoint40.json';rv=read(review);assert rv['candidate_sha256']==expected and len(rv['art_review_images'])==9
for im in rv['art_review_images']:assert im['root_actually_viewed'] and sha(ROOT/im['path'])==im['sha256']
visual=R/'chaser287_review/visual_review.json';v=read(visual);assert len(v['actually_viewed_by_agent'])==20
for im in v['actually_viewed_by_agent']:assert sha(ROOT/im['path'])==im['sha256']
q=read(P/'proposal.json');plan=read(R/'rin287_components.json');base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];s=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
sp=R/'rin287_static_binding_check.json';dump(sp,{'passed':True,'candidate_sha256':expected,'result':s});proofs['static_binding']=sp
audit={'passed':True,'candidate_sha256':expected,'cumulative_authored_refs':287,'new_art_refs':28,'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'root_review':rel(review),'root_review_sha256':sha(review),'agent_visual_review':rel(visual),'agent_visual_review_sha256':sha(visual),'raw_count':444,'non_target_raw_exact':416,'display_count':436,'non_target_display_exact':408,'original_ribbon_tiles_exact':True,'native_timeline_calls':843,'original_animation_tables':12,'root_original_timeline_sheets_viewed':False,'source_body4_original_ribbon_bob_refs':28,'new_tile_window_x_only_bytes':24,'runtime_verified':False,'user_accepted':False,'limitations':['새28의 실제 체이서 차체/물리와 전각도 실기는 미확인.','원래표12의843원MIPS 호출은 애니메이션 순서/유지시간 검증이며 실제 게임 차량 제어를 재현하지 않는다.','Root는 최종 일반/레드8판+접점1판을 실제 열람했다. 원순서12판은 제작자만 실제 열람했다.']}
ap=R/'final287_readback_audit.json';dump(ap,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(ap),native_report=rel(proofs['native_gpu']),visual_report=rel(visual),root_art_review_pending=False,root_review=rel(review),root_review_sha256=sha(review),ready_for_checkpoint_integration=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(R/'chaser_contacts_probe_v1/registration.json'),'independent_report':rel(ap),'independent_report_sha256':sha(ap),'root_review':rel(review),'root_review_sha256':sha(review),'technical_checks_passed':True,'ready_for_checkpoint_integration':True,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False,'cumulative_main_refs':287,'new_art_refs':28,'scope':'체이서4새몸체와 원리본4위상/기존상하진동28참조를 동결. 원32타일·4공유stream·비대상408표시·부분8·원리본타일·팔레트/음향/정적효과 보존. 원표12개843MIPS호출과 정적열람은 실기 및 사용자수용과 별도.'}
dump(P/'FROZEN.json',f)
lp=R/'progress_ledger.json';j=read(lp);assert j['prepared_count']==259;done=set(j['new_art_prepared_refs'])|set(q['new_art_refs']);assert len(done)==287
body={x for g in j['groups']for x in g['body_or_head_refs']};remaining=body-done;assert len(remaining)==28
for g in j['groups']:
 refs=set(g['body_or_head_refs']);g['new_art_prepared']=sorted(refs&done);g['remaining']=sorted(refs-done)
m=read(R/'remaining259_manifest.json');m['groups']=[g for g in m['groups']if not any(x['ref'] in set(q['new_art_refs'])for x in g['refs'])];m.update(candidate_sha256=expected,frozen=rel(P/'FROZEN.json'),frozen_sha256=sha(P/'FROZEN.json'),new_art_refs_with_aliases_and_effect_derivations=287,remaining_ledger_refs=28,needs_new_art_refs=14,scope='등장5몸체+기존흰섬광2파생과 낙봉파 잔여9를 계속 제작한다. 나머지12는 수용대기/전환10·이미동기화정적2이며 무조건 재작화하지 않는다. 참조수는 전체품질 완료율이 아니다.')
m['concrete_backlog'].pop('ride_chaser',None);m['concrete_backlog'].update(total_ledger_refs=28,active_repaint_refs=14);m['limitations']=[s.replace('고정259','고정287')for s in m['limitations']];dump(R/'remaining287_manifest.json',m)
j.update(current_arc=rel(P/'PL01_U.ARC'),current_sha256=expected,new_art_prepared_refs=sorted(done),remaining_refs_in_original_audit=sorted(remaining),prepared_count=287,latest_scope=f['scope'],latest_proof=rel(ap),latest_native=rel(proofs['native_gpu']),latest_frozen=rel(P/'FROZEN.json'),remaining_classification=rel(R/'remaining287_manifest.json'),next_page='arrival_detail01',next_page_scope='등장249..253 원화와247/248흰섬광, 이후낙봉파잔여9.',next_authored_inputs=[{'directory':rel(R/'arrival_detail01'),'refs':list(range(249,254)),'bank':0,'reason':'기존포즈/손발접점 보존하며 머리·의상 상세 새5몸체. 흰섬광은원규칙파생.'}]);j['limitations']=[s for s in j['limitations']if'누적259'not in s]+['누적287은 원화·공유·파생 참조수이며 품질완료율이 아니다. 체이서28의 실제차량조합 실기는 미확인.'];dump(lp,j);dump(R/'progress_ledger287_snapshot.json',j)
print(json.dumps({'arc':expected,'frozen_sha256':sha(P/'FROZEN.json'),'proposal_sha256':sha(P/'proposal.json'),'recipe_sha256':sha(P/'static_effects.json'),'remaining':len(remaining)},ensure_ascii=False))
