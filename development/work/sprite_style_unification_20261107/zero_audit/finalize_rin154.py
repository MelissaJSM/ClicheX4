"""Freeze reviewed 12 masters/13 refs without changing source images or game files."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_ground_remaining_v1';V=R/'ground_remaining154_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists()
expected='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319'
ap=R/'final154_readback_audit.json';np=R/'rin154_components_native_checks.json';gp=R/'rin154_guard_checks.json';bp=V/'browser_verification.json'
audit=json.loads(ap.read_text('utf8'));native=json.loads(np.read_text('utf8'));guard=json.loads(gp.read_text('utf8'));browser=json.loads(bp.read_text('utf8'));q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin154_components.json').read_text('utf8'))
assert sha(P/'PL01_U.ARC')==audit['candidate_sha256']==guard['candidate_sha256']==q['after_sha256']==expected
assert all(j['passed']for j in[audit,native,guard,browser])
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
dump(R/'rin154_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
fix=R/'recovery130_fix01';info=json.loads((fix/'inputs.json').read_text('utf8'));info['edit_scope']='새 원화의 양손과 커프만 보완한다. 기존 세밀한 머리·몸통·발은 등록 시 보호한다.';dump(fix/'inputs.json',info)
dump(fix/'generation.json',{'tool':'builtin image_gen.imagegen','output_original':'<LOCAL_PATH>','output_copy':rel(fix/'generated.png'),'output_sha256':sha(fix/'generated.png'),'size':[1536,1024],'prompt_sha256':sha(fix/'prompt.txt'),'transparent_background_requested':True,'approved_replacement_sprite_inputs_only':True,'raw_game_assets_sent':False,'registered':True,'local_arm_mask_only_used':True,'game_changed':False,'user_accepted':False})
manifest=json.loads((V/'manifest.json').read_text('utf8'));seen=[]
for name in manifest['sheets']:
 p=V/name;seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
for form in('normal','black'):
 for i in range(4):
  p=P/f'{form}_readback_{i:02}.png';seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
visual={'sheets':seen,'observations':[
 '실제 패킹 결과 일반·레드8장, 원순서 전후 스트립8장, 검기 합성4장을 모두 직접 열람했다. 새 머릿결·옷깃·커프·앞치마와 부츠 명암이 대기 수준에 가까워졌고 목·허리·무릎의 뚜렷한 단절은 보이지 않는다.',
 '130은 새 세밀한 머리와 몸통을 유지하며 양손을 몸 앞에 모으는 기존 포즈를 좁은 원화 편집으로 복구했다. 기존 거친 상체나 머리를 덮지 않았다.',
 '3/107 눈높이의 기존 대비2픽셀 차이와83/85/87 앞발1픽셀 차이는 기록한다. 원표의3→4→7→8 및105→107→109→111 순서 스트립에서는 갑자기 몸이 커지거나 목이 끊기는 변화는 보이지 않는다. 이 검토는 정지 스트립이며 실시간 영상 관찰을 대신하지 않는다.',
 '91/93은 원래 정확히 같은 몸체이므로 새 원화도 동일하다. 이어지는95/97의 이전에 보완한 몸체와 큰 상세 수준 차이가 보이지 않는다.',
 '검기8짝의 원래 이펙트를 보존해 일반·레드로 정적 합성했다. 새 커프와 검기 사이가 추가로 크게 벌어진 현상은 보이지 않는다.91/93 및105의 별도 후행 입자는 원래도 분리돼 있으며 실제 무기 객체의 동적 위치·CLUT는 이 합성으로 판단하지 않는다.'
 ],'eye_metrics':manifest['eye_metrics'],'limitations':manifest['limitations'],'browser_verification':rel(bp),'browser_sha256':sha(bp),'browser_scope':'오프라인140표 위치/정수4배/JS오류 없음/재생 진행 검사. 게임 실기 및 연속 영상 육안검증은 미실행.','root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True,static_binding_proof=rel(R/'rin154_static_binding_check.json'));dump(ap,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(ap),native_report=rel(np),guard_report=rel(gp),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_registered_art_review_approved=True,root_final_packed_review_pending=True,full_art_unification_complete=False,scope='새 지상2타·공격 회복·이동 진입12원화와91/93 정확공유, 총13참조를 네이티브 등록했다. 이전141·검기·부분VRAM·정적몸체를 보존했고 독립 reader·원MIPS·입력거부·정적미술 검토를 통과했다. 실제 플레이와 사용자 수용은 미실행이다.');dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==141
(R/'progress_ledger141_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==154
ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=154,latest_scope=q['scope'],latest_proof='final154_readback_audit.json',latest_native='rin154_components_native_checks.json',next_page=None,next_page_scope='남은 공중 검격·회전, 등장, 사다리·탑승과 특수기 공유 몸체의 미술 검토/새 원화를 계속한다. 전체 통일 완료 아님.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'independent_sha256':sha(ap),'native_sha256':sha(np),'guard_sha256':sha(gp),'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'after141_registered_v2/registration.json'),'cumulative_main_refs':154,'incremental_main_refs':13,'new_authored_body_keys':12,'exact_alias_refs':1,'shared_support_refs_preserved':8,'shared_entire_consumed_tiles_preserved':35,'bank0_slack':3268,'bank1_slack':7266,'hidden_global_cleanup':False,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
dump(P/'FROZEN.json',f);print(json.dumps(f))
