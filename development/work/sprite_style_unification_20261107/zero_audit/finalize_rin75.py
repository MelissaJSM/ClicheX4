"""Freeze the rear13 increment after separate readback/native/art checks."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_rear_continuation as wrapper
c=wrapper.core;e=c.engine;P=c.OUT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(P/'FROZEN.json').exists(),'Frozen output must not be rewritten'
arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejections=[]
for case in('wrong_parent','missing_art','changed_authored_pixel','index16','wrong_mirrored_alias'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_art':del t[0,178]
 elif case=='changed_authored_pixel':t[0,190][160,150]^=1
 elif case=='index16':t[0,186][160,150]=16
 else:t[0,180]=t[0,178].copy()
 try:e.build(a,t)
 except ValueError as exc:rejections.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
audit_path=R/'final75_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'))
native_path=R/'rin75_components_native_checks.json';native=json.loads(native_path.read_text('utf8'))
assert audit['passed']and native['passed']and sha(P/'PL01_U.ARC')==audit['candidate_sha256']=='806b3871055233a5c37c1c2c17685e02aadd07d647be62ea69bf696787f3fbe4'
seen=[]
for form in('normal','black'):
 for page in range(4):
  f=P/f'{form}_readback_{page:02}.png';seen.append({'path':str(f.relative_to(c.ROOT)),'sha256':sha(f),'actually_viewed':True})
visual={'scope':'실제 패킹 ARC에서 다시 그린 일반·레드 13참조와 대기147의 확대 비교 8장을 직접 열람했다. 정적 미술 검토이며 실기나 사용자 수용이 아니다.','sheets':seen,'observations':['178~181의 뒷머리 층과 치마의 내부 회색 면이 원래 큰 흰 면보다 세밀해졌다. 반전에서도 손·머리·리본 연결이 유지된다.','182~185의 등과 앞치마 끝 명암, 손목 접점이 이어진다. 같은 원화·반전 조립이므로 방향별 체형 차이가 없다.','186~189의 국소 종아리 보완을 유지했고 발목이 분리되거나 발끝이 잘린 곳을 발견하지 못했다.','190은 전체 y-1 이동을 취소했다. 머리는 새 원화 위치를 보존하고 부츠 일부만 y-1로 등록하여 기존 발끝에 맞췄다.','레드 팔레트에서도 머리·소매·치마의 명암 구분이 유지된다.'], 'root_review':{'registered_four_master_normal':True,'source':'루트가 rear_registered_grips_v1/normal_comparison 4키를 직접 열람하고 후보 미술 검토 통과를 전달함.','packed_readback_review_pending':True},'gameplay_runtime_verified':False,'user_accepted':False}
visual_path=R/'rear75_visual_review.json';visual_path.write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
audit.update({'visual_review_pending':False,'visual_review':str(visual_path.relative_to(c.ROOT)),'visual_review_sha256':sha(visual_path),'canonical_aliases_exact':True,'mirror_geometry':'픽셀 x′=319−x, 파츠 x′=−x−16 및 flipX 토글. 원점·시간표·타일 수는 동일.','limitations':['후면 13참조와 이전 62참조의 누적 작업이며 모든 동작의 미술 통일이나 실기 완료가 아니다.','190은 전체 y-1 등록을 취소하고 새 부츠 일부만 y-1로 정합했다. 178/182/186의 새 장갑과 손목만 원접점으로 국소 이동했다.','부분 VRAM 42..49의 원래 bank1 raw·조립·전체 은행은 보존했다. 모든 실제 전이 경로를 게임에서 검사한 것은 아니다.']})
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n','utf8')
guard=R/'rin75_guard_checks.json';guard.write_text(json.dumps({'passed':True,'native_input_rejections':rejections,'reproducible_twice':True,'source_palette_and_target_indices_guarded':True},ensure_ascii=False,indent=2)+'\n','utf8')
j=json.loads((P/'proposal.json').read_text('utf8'))
j.update({'scope':'대기 질감 기준의 새 후면 원화 4키와 186/190 다리 국소 보완을 동일·반전 13참조에 등록했다. 이전 62참조와 공유 자세191, 부분 VRAM 8참조, 시간표·음향·팔레트·정적 효과를 보존한다.','root_review_pending':False,'root_art_review':visual['root_review'],'independent_review_pending':False,'independent_report':str(audit_path.relative_to(c.ROOT)),'native_report':str(native_path.relative_to(c.ROOT)),'guard_report':str(guard.relative_to(c.ROOT)),'visual_report':str(visual_path.relative_to(c.ROOT)),'limitations':audit['limitations'],'ready_for_checkpoint_integration':True,'full_art_unification_complete':False,'hidden_global_cleanup':False,'canonical_shared_parts_normalized':True})
j['verification']['independent_incremental_counts']=audit['incremental_counts'];j['verification']['static404_reference_data_exact']=True
(P/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
ledger=R/'progress_ledger.json';l=json.loads(ledger.read_text('utf8'));assert l['prepared_count']==62
(R/'progress_ledger62_snapshot.json').write_bytes(ledger.read_bytes())
new=list(j['new_art_refs']);l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(new));assert len(l['new_art_prepared_refs'])==75
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit']if r not in new]
l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=sha(P/'PL01_U.ARC'),prepared_count=75,latest_scope=j['scope'],latest_proof='final75_readback_audit.json',latest_native='rin75_components_native_checks.json',next_page=None,next_page_scope='남은 후면191~196 및 공중 용염인 동작의 기존 단순한 머리·등/치마를 다음 원화 페이지로 준비한다. 미제작.',full_art_unification_complete=False,user_accepted=False,gameplay_runtime_verified=False)
l['full_visual_review_scope']='52단계436참조/58시트 전수 열람 뒤 62의 10참조6장, 75의 후면13참조8장을 각각 실제 열람했다.'
ledger.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha(P/'proposal.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'static_recipe_sha256':sha(P/'static_effects.json'),'guard_sha256':sha(guard),'visual_review_sha256':sha(visual_path),'cumulative_main_refs':75,'incremental_main_refs':13,'bank0_slack':4686,'root_registered_master_review':True,'root_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frozen))
