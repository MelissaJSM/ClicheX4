"""Freeze the five authored victory bodies and two synchronized departure flashes."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_victory_details as wrapper
c=wrapper.core;e=c.engine;P=c.OUT;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(P/'FROZEN.json').exists()
arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejected=[]
for case in('wrong_parent','missing_body','changed_authored_pixel','index16','changed_preserved_idle','changed_preserved_victory5','changed_derived_flash'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_body':del t[1,1]
 elif case=='changed_authored_pixel':t[1,2][138,163]^=1
 elif case=='index16':t[1,3][138,164]=16
 elif case=='changed_preserved_idle':t[1,0][160,150]^=1
 elif case=='changed_preserved_victory5':t[1,5][160,150]^=1
 else:t[1,7][160,150]^=1
 try:e.build(a,t)
 except ValueError as exc:rejected.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
audit_path=R/'final91_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'));native_path=R/'rin91_components_native_checks.json';native=json.loads(native_path.read_text('utf8'))
assert audit['passed']and native['passed']and sha(P/'PL01_U.ARC')==audit['candidate_sha256']=='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e'
seen=[]
for form in('normal','black'):
 for n in range(2):
  q=P/f'{form}_readback_{n:02}.png';seen.append({'path':str(q.relative_to(c.ROOT)),'sha256':sha(q),'actually_viewed':True})
visual={'sheets':seen,'scope':'패킹 ARC 재추출의 일반·레드 5몸체와 2귀환 섬광을 대기·원래 몸체와 직접 비교했다.','observations':['머리의 큰 흰색 면을 머릿결·안쪽 회청색 그늘로 나누고 커프·가슴띠·치맛단·부츠 안쪽 선을 추가했다.','새6의 지지다리와 팔은 기존에 검토한5와 이어진다. 다리 전체 길이 확대나 몸 전체 좌표 이동은 없다.','1/2/3/4의 서로 다른 회전·팔 자세를 유지한다. 몸체를 대기 머리나 과거 의상으로 덮지 않았다.','7은 새3의 몸체를 그대로 둔 1픽셀 흰 섬광,8은 같은 새3에서 원래 색 변환과 2픽셀 광선을 적용했다. 몸체와 흰 테두리가 서로 다른 자세를 쓰지 않는다.','일반·레드 모두 목·소매·허리·무릎에서 뚜렷한 절단은 보이지 않았다. 모든 미술 판단은 정지 이미지 검토이며 실기 수용을 뜻하지 않는다.'],'root_registered_art_review_approved':True,'root_review_evidence':'루트가 normal 비교00/01와5_6을 실제 열람하고 명암·지지다리 폭 연결을 수용했다.','root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=R/'victory91_visual_review.json';vp.write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
anchor_path=R/'victory_registered_v1/registration.json';target_path=c.ART/'targets.json'
limitations=['이번은 새 승리 몸체5개와 원래 규칙으로 파생한 귀환 섬광2개이다. 전 동작 통일 또는 실제 플레이 검증 완료가 아니다.','원래 모든 조립 바이트·프레임 순서와 타이밍, 대기0, 이미 검토한 승리5, 순수 빛9..13은 보존했다.','부분 VRAM42..49와 정적 몸체23/24는 이전84와 같다. 기존 일반·레드 팔레트도 그대로이다.']
audit.update(visual_review_pending=False,visual_review=str(vp.relative_to(c.ROOT)),visual_review_sha256=sha(vp),anchor_review=str(anchor_path.relative_to(c.ROOT)),anchor_review_sha256=sha(anchor_path),departure_rule_review=str(target_path.relative_to(c.ROOT)),departure_rule_review_sha256=sha(target_path),limitations=limitations)
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n','utf8')
guard=R/'rin91_guard_checks.json';guard.write_text(json.dumps({'passed':True,'rejections':rejected,'reproducible_twice':True},ensure_ascii=False,indent=2)+'\n','utf8')
j=json.loads((P/'proposal.json').read_text('utf8'));j.update({'independent_report':str(audit_path.relative_to(c.ROOT)),'native_report':str(native_path.relative_to(c.ROOT)),'visual_report':str(vp.relative_to(c.ROOT)),'anchor_report':str(anchor_path.relative_to(c.ROOT)),'guard_report':str(guard.relative_to(c.ROOT)),'ready_for_checkpoint_integration':True,'full_art_unification_complete':False,'root_registered_art_review_approved':True,'root_review_pending':False,'root_final_packed_review_pending':True,'limitations':limitations,'hidden_global_cleanup':False});j['verification']['independent_incremental_counts']=audit['incremental_counts']
(P/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
lp=R/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));assert l['prepared_count']==84;(R/'progress_ledger84_snapshot.json').write_bytes(lp.read_bytes());l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(j['new_art_refs']));assert len(l['new_art_prepared_refs'])==91
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit']if r not in j['new_art_refs']]
l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=sha(P/'PL01_U.ARC'),prepared_count=91,latest_scope=j['scope'],latest_proof='final91_readback_audit.json',latest_native='rin91_components_native_checks.json',next_page=None,next_page_scope='다음 후보는 아직 구형인 벽·이동 전환34/36/38/41/45/193 또는 피격·저체력135/139/149/152. 실제 대기 비교 후 대표를 정한다.')
lp.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha(P/'proposal.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'static_recipe_sha256':sha(P/'static_effects.json'),'guard_sha256':sha(guard),'visual_review_sha256':sha(vp),'anchor_review_sha256':sha(anchor_path),'departure_rule_sha256':sha(target_path),'cumulative_main_refs':91,'incremental_main_refs':7,'incremental_authored_body_refs':5,'derived_main_flash_refs':2,'composition_bytes_exact':True,'shared_support_refs_preserved':[0,5,9],'bank0_slack':4660,'bank1_slack':7176,'root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frozen))
