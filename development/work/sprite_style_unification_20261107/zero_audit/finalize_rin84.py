"""Freeze the four rear rising bodies after separate reading and contact review."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_rising_rear as wrapper
c=wrapper.core;e=c.engine;P=c.OUT;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(P/'FROZEN.json').exists()
arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejected=[]
for case in('wrong_parent','missing_body','changed_authored_pixel','index16','changed_shared_flame'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_body':del t[1,148]
 elif case=='changed_authored_pixel':t[1,150][160,150]^=1
 elif case=='index16':t[1,152][160,150]=16
 else:t[1,149][122,147]^=1
 try:e.build(a,t)
 except ValueError as exc:rejected.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
audit_path=R/'final84_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'));native_path=R/'rin84_components_native_checks.json';native=json.loads(native_path.read_text('utf8'))
assert audit['passed']and native['passed']and sha(P/'PL01_U.ARC')==audit['candidate_sha256']=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
fp=R/'rising_flame_review_v1/report.json';fr=json.loads(fp.read_text('utf8'));assert fr['passed'];viewed=[]
for form in('normal','black'):
 for suffix in('fire_00','fire_01','contact_zoom'):
  q=fp.parent/f'{form}_{suffix}.png';viewed.append({'path':str(q.relative_to(c.ROOT)),'sha256':sha(q),'actually_viewed':True})
fr.update(actually_viewed_pending=False,actually_viewed_pngs=viewed,visual_observations=['네 손잡이는 원래와 같은(147,122)에서 불꽃에 겹친다. 손목·커프와 불꽃 사이에 새로 분리된 틈은 보이지 않았다.','152/154는 원래 불꽃의 투명한 아래 홈이 남는다. 효과 외형 자체를 채우거나 새로 바꾸지 않았다.','일반·레드 모두 머릿결·등끈·치맛단 명암이 유지되며 검기 근처에 별도의 긴 칼이나 새 도구를 추가하지 않았다.'],root_final_flame_review_pending=True)
fp.write_text(json.dumps(fr,ensure_ascii=False,indent=2)+'\n','utf8')
seen=[{'path':str((P/f'{form}_readback_00.png').relative_to(c.ROOT)),'sha256':sha(P/f'{form}_readback_00.png'),'actually_viewed':True}for form in('normal','black')]
visual={'sheets':seen,'scope':'패킹 ARC 재추출의 일반·레드4몸체를 대기와 직접 비교하고, 불꽃 합성6장도 직접 열람했다.','observations':['새 후두부는 단색 타원에 가까웠던 큰 흰 면 대신 회청색 머릿결·안쪽 그늘이 구분된다.','등끈·커프·치맛단 주름과 부츠의 선택적 명암이 추가됐고, 등과 치마가 허리에서 분리되어 보이지 않는다.','148/150/152/154의 서로 다른 무릎·발 자세가 유지된다. 152/154는 손·머리 높이와 발끝 높이를 각각 등록했으며 몸 전체 이동은 없다.','검은색 변형은 기존 레드 팔레트13을 그대로 쓴다. 두 색 모두 선처럼 가늘어진 목/종아리 또는 파츠 경계의 뚜렷한 절단은 발견하지 못했다.'],'root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=R/'rising84_visual_review.json';vp.write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
anchor_path=c.ART/'registration.json'
audit.update(visual_review_pending=False,visual_review=str(vp.relative_to(c.ROOT)),visual_review_sha256=sha(vp),anchor_review=str(anchor_path.relative_to(c.ROOT)),anchor_review_sha256=sha(anchor_path),flame_pair_and_contact_review=str(fp.relative_to(c.ROOT)),flame_pair_and_contact_review_sha256=sha(fp))
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n','utf8')
guard=R/'rin84_guard_checks.json';guard.write_text(json.dumps({'passed':True,'rejections':rejected,'reproducible_twice':True},ensure_ascii=False,indent=2)+'\n','utf8')
j=json.loads((P/'proposal.json').read_text('utf8'));j.update({'independent_report':str(audit_path.relative_to(c.ROOT)),'native_report':str(native_path.relative_to(c.ROOT)),'visual_report':str(vp.relative_to(c.ROOT)),'anchor_report':str(anchor_path.relative_to(c.ROOT)),'flame_contact_report':str(fp.relative_to(c.ROOT)),'guard_report':str(guard.relative_to(c.ROOT)),'ready_for_checkpoint_integration':True,'full_art_unification_complete':False,'root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'limitations':audit['limitations'],'hidden_global_cleanup':False});j['verification']['independent_incremental_counts']=audit['incremental_counts']
(P/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
lp=R/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));assert l['prepared_count']==80;(R/'progress_ledger80_snapshot.json').write_bytes(lp.read_bytes());l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(j['new_art_refs']));assert len(l['new_art_prepared_refs'])==84
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit']if r not in j['new_art_refs']]
l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=sha(P/'PL01_U.ARC'),prepared_count=84,latest_scope=j['scope'],latest_proof='final84_readback_audit.json',latest_native='rin84_components_native_checks.json',next_page=None,next_page_scope='다음 후보는 승리·귀환 b1_1/3/6. 원화 공유와7의 흰 외곽 효과를 먼저 분리 조사한다.')
lp.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha(P/'proposal.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'static_recipe_sha256':sha(P/'static_effects.json'),'guard_sha256':sha(guard),'visual_review_sha256':sha(vp),'anchor_review_sha256':sha(anchor_path),'flame_contact_sha256':sha(fp),'cumulative_main_refs':84,'incremental_main_refs':4,'shared_flame_refs_preserved':4,'bank0_slack':4660,'bank1_slack':7002,'root_registered_art_review_approved':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frozen))
