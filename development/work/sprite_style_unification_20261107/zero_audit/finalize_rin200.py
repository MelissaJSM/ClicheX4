"""용염인 진입1·회전8 준비본 검수와 장부를 동결한다."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
R=D/'rin_extension';P=R/'prepared_spin01';V=R/'spin200_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
proofs={k:R/f for k,f in [('independent','final200_readback_audit.json'),('native','rin200_components_native_checks.json'),('guard','rin200_guard_checks.json')]}
checks={k:json.loads(p.read_text('utf8'))for k,p in proofs.items()};q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin200_components.json').read_text('utf8'));browser=json.loads((V/'browser_verification.json').read_text('utf8'))
assert all(j['passed']for j in checks.values())and browser['passed'];assert sha(P/'PL01_U.ARC')==q['after_sha256']==checks['independent']['candidate_sha256']==expected
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch']);dump(R/'rin200_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
m=json.loads((V/'manifest.json').read_text('utf8'));rot=json.loads((V/'rotation_review.json').read_text('utf8'));paths=[V/name for name in m['sheets']]+[V/s['path']for s in rot['sheets']]+[P/f'{form}_readback_{n:02}.png'for form in('normal','black')for n in(0,1,2)]
assert len(paths)==14
visual={'sheets':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in paths],
 'observations':['패킹 일반·레드6장, 원표100/101 순서4장, 회전 반복/검기 참고4장을 실제 열람했다.',
 '144의 새 커프·치마 주름·부츠 명암과161/163 머릿결·칼라·접힌 다리 디테일이 대기와 기존 새 공중 자세에 가까워졌다. 144 왼발 새 구두만1px 위,163 새 머리만x+3 정합했으며 옛 머리/몸을 덮지 않았다.',
 '159.5,159.5를 중심으로 새161/163을 정수90도 회전해8방향을 만들었다. 167/171의 원래 대각선18/15px 차이는 원래 exact라고 주장하지 않고 새 마스터의 동일한 회전 묘사로 통일했다.',
 '161→163→165→167→169→171→173→175 및 마지막→처음 미술 반복에서 머리/접힌 다리가 별개로 흔들리는 확정 단절을 찾지 못했다. 검기짝은 원점 동일 불투명 합성 참고일 뿐 실제 객체 재현이 아니다.',
 '원표100은132로 진입한 뒤8방향을 지나160을 유지한다.175→161 반복은 검토용이다.144는 원표101 용염인 진입이며 이전 입력 파일의 빙열참 준비 표기는 이 기록에서 정정한다.'],
 'limitations':m['limitations']+rot['limitations'],'browser_verification':rel(V/'browser_verification.json'),'browser_scope':'오프라인46표 위치·정수4배·JS오류 없음. 연속 동영상 육안 및 실제 게임 미실행.',
 'root_registered_art_review_pending':False,'root_final_packed_review_pending':False,'root_review_evidence':'root 메시지: 등록 비교와 air_spin 일반·레드/normal_closed_art_cycle/normal_effects_reference 4장 직접 열람, 추가 확정 튀는 문제 없음. 후보 동결 승인.',
 'user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit=checks['independent'];audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=False,static_binding_proof=rel(R/'rin200_static_binding_check.json'));dump(proofs['independent'],audit)
scope='용염인 진입144 새1원화와 회전161/163 새2원화의8방향: 총9참조, 누적200. 이전191·지원11의소비114타일·부분VRAM8·정적몸체 보존. 독립reader·원MIPS·8거부·정적미술/root 검토 통과. 전수실기·사용자수용은 미확인.'
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(proofs['independent']),native_report=rel(proofs['native']),guard_report=rel(proofs['guard']),visual_report=rel(vp),ready_for_checkpoint_integration=True,frozen_candidate=True,root_art_review_pending=False,full_art_unification_complete=False,scope=scope);dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==191;(R/'progress_ledger191_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==200;ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
ledger['limitations']=[s for s in ledger['limitations']if '새 원화 누적191'not in s]+['새 원화 누적200의 전수 실제 플레이와 사용자 최종 수용은 미확인이다. root 정적미술 검토와 원MIPS/GPU 검사는 구분한다.']
ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=200,latest_scope=scope,latest_proof='final200_readback_audit.json',latest_native='rin200_components_native_checks.json',next_page=None,next_page_scope='용염인146/156/158·사다리197/199/202·질풍아155..172·공유지상특수·등장/탑승 잔여를 세부 원화로 이어간다.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'ice_spin_registered_v1/registration.json'),'cumulative_main_refs':200,'incremental_main_refs':9,'body_refs':9,'shared_support_refs_preserved':11,'shared_entire_consumed_tiles_preserved':114,'bank0_slack':2766,'bank1_slack':6488,'hidden_global_cleanup':False,'root_art_review_pending':False,'user_accepted':False,'runtime_verified':False};dump(P/'FROZEN.json',f);print(json.dumps(f))
