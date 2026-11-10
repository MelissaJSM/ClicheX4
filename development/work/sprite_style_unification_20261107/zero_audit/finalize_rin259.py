"""최종 탑승 머리19의 증거를 고정하고 장부259를 갱신한다."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_ride_heads02';expected='c82e6230bcc687e2cc851a88735b695b04636b9fce3baddcf4c771abf81e265b'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert sha(P/'PL01_U.ARC')==expected and not(P/'FROZEN.json').exists()
proofs={'source_reproduction_and_rejections':R/'rin259_v2_source_proof.json','native':R/'rin259_v2_components_native_checks.json','independent':D.parent/'nana_audit/rin259_v2_independent_readback.json'}
assert sha(proofs['independent'])=='aed0240eb8dc6c29ac682e43ae86b4fc7cf089c3f3d28186d2f5d30c2881a6c3'
for p in proofs.values():
 j=read(p);assert j['passed'];assert j.get('candidate_sha256',expected)==expected
root_review=D.parent/'root_review_checkpoint39.json';rv=read(root_review);assert rv['candidate_sha256']==expected and len(rv['art_review_images'])==4
for im in rv['art_review_images']:assert im['root_actually_viewed'] and sha(ROOT/im['path'])==im['sha256']
q=read(P/'proposal.json');plan=read(R/'rin259_v2_components.json');base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC']
check=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
dump(R/'rin259_v2_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'result':check});proofs['static']=R/'rin259_v2_static_binding_check.json'
visual={'actually_viewed_by_agent':rv['art_review_images'],'root_review':rel(root_review),'root_review_sha256':sha(root_review),'findings':['최종 일반/레드 재추출4판을 직접 열람했다. 새 머릿결·작은 눈·보닛의 밝은 능선이 타일에서도 유지된다.','75/77이 최초안에서 작게 보였던 문제는 실제 복원한 조종석 위 비교로 확인했다. 새75/77 원화와75 상단17셀 국소 원화로 높이/부피를 보완하고 나머지3각도와 턱 접점을 보존했다.','75의 뾰족한 능선은 새 원화의 상단 표본으로 넓어졌다.77은 앞서 수용된 v2와 같다.'], 'limitations':['조종석 원본66 복원은2498개 불투명 픽셀 exact이다. 다른4각도는 같은 중립 조종석 위 크기 비교이며 실제 해당 자세 조합의 실행 증거가 아니다.','새 독립 reader는 대상/비대상과 타일을 검사했으며 새 비교판 시각열람은 별도라고 명시했다.','실제 차량 전각도 플레이와 사용자 수용은 미확인.'],'runtime_verified':False,'user_accepted':False}
dump(R/'rin259_v2_visual_review.json',visual)
audit={'passed':True,'candidate_sha256':expected,'cumulative_authored_refs':259,'incremental_refs':19,'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review':rel(R/'rin259_v2_visual_review.json'),'visual_review_sha256':sha(R/'rin259_v2_visual_review.json'),'root_review':rel(root_review),'root_review_sha256':sha(root_review),'previous240_preserved':True,'all_composition_bytes_exact':True,'partial8_exact':True,'blank80_display_and_consumed_tiles_exact':True,'bank1_slack':5714,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False}
dump(R/'final259_readback_audit.json',audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(R/'final259_readback_audit.json'),native_report=rel(proofs['native']),visual_report=rel(R/'rin259_v2_visual_review.json'),root_art_review_pending=False,root_review=rel(root_review),root_review_sha256=sha(root_review),ready_for_checkpoint_integration=True,full_art_unification_complete=False)
dump(P/'proposal.json',q)
f={'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'static_recipe_sha256':sha(P/'static_effects.json'),'registration_sha256':sha(R/'ride_head_registered_v3/registration.json'),'independent_report':rel(R/'final259_readback_audit.json'),'independent_report_sha256':sha(R/'final259_readback_audit.json'),'root_review':rel(root_review),'root_review_sha256':sha(root_review),'technical_checks_passed':True,'ready_for_checkpoint_integration':True,'root_art_review_pending':False,'runtime_verified':False,'user_accepted':False,'cumulative_main_refs':259,'new_art_refs':19,'scope':'라이드 아머5각도 머리19참조와 기존240을 동결. 조립·부분VRAM·모든 비대상·팔레트·음향·정적효과 보존. 조종석 비교와 원MIPS 검사는 실제 전각도 플레이 및 사용자 수용과 별도다.'}
dump(P/'FROZEN.json',f)
lp=R/'progress_ledger.json';j=read(lp);assert j['prepared_count']==240
done=set(j['new_art_prepared_refs'])|set(q['new_art_refs']);assert len(done)==259
body={x for g in j['groups']for x in g['body_or_head_refs']};remaining=body-done;assert len(remaining)==56
for g in j['groups']:
 refs=set(g['body_or_head_refs']);g['new_art_prepared']=sorted(refs&done);g['remaining']=sorted(refs-done)
m=read(R/'remaining240_review/manifest.json');m['groups']=[g for g in m['groups']if g['group']!='ride_armor_head'];m.update(candidate_sha256=expected,frozen=rel(P/'FROZEN.json'),frozen_sha256=sha(P/'FROZEN.json'),new_art_refs_with_aliases_and_effect_derivations=259,remaining_ledger_refs=56,needs_new_art_refs=42,source240_nonride_remaining_preserved=True,scope='체이서28·등장몸체5·낙봉파잔여9의42참조를 계속 제작한다. 나머지14는 수용대기/전환10·의도한섬광2·정적동기화2이며 새그림 필요 수와 완료율로 혼동하지 않는다.')
dump(R/'remaining259_manifest.json',m)
m['concrete_backlog'].pop('ride_armor_head',None);m['concrete_backlog'].update(total_ledger_refs=56,active_repaint_refs=42)
m['limitations']=[s.replace('고정240','고정259')for s in m['limitations']]
m['prior240_visual_observations']=m.pop('visual_observations',[])
dump(R/'remaining259_manifest.json',m)
j.update(current_arc=rel(P/'PL01_U.ARC'),current_sha256=expected,new_art_prepared_refs=sorted(done),remaining_refs_in_original_audit=sorted(remaining),prepared_count=259,latest_scope=f['scope'],latest_proof='final259_readback_audit.json',latest_native=rel(proofs['native']),latest_frozen=rel(P/'FROZEN.json'),remaining_classification=rel(R/'remaining259_manifest.json'),next_page='chaser_detail01',next_page_scope='체이서4몸체28참조 원화 등록 후 등장249..253와 낙봉파 잔여9참조.',next_authored_inputs=[{'directory':rel(R/'chaser_detail01'),'refs':[14,22,30,38],'bank':1,'reason':'원몸체4기울기/4리본파형/기존상하진동의28참조. 새원화 저장, 아직 정합/패킹 전.'}])
j['limitations']=[s for s in j['limitations']if'누적240'not in s]+['누적259는 원화·공유·파생 참조 수이며 전체미술 완료율이 아니다. 새 탑승19 전각도 실기는 미확인.']
dump(lp,j);dump(R/'progress_ledger259_snapshot.json',j)
print(json.dumps({'arc':expected,'frozen_sha256':sha(P/'FROZEN.json'),'proposal_sha256':sha(P/'proposal.json'),'recipe_sha256':sha(P/'static_effects.json'),'remaining':len(remaining)},ensure_ascii=False))
