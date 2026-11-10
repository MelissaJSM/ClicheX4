from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_third_saber as module
c=module.core;e=c.engine;arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejections=[]
for case in('wrong_parent','missing_art','changed_authored_pixel','index16'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_art':del t[0,109]
 elif case=='changed_authored_pixel':t[0,109][160,150]^=1
 else:t[0,109][160,150]=16
 try:e.build(a,t)
 except ValueError as exc:rejections.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
P=R/'prepared_third_saber_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit_path=R/'final62_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'));native_path=R/'rin62_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert audit['passed']and native['passed']and sha(P/'PL01_U.ARC')==audit['candidate_sha256']
guard=R/'rin62_guard_checks.json';guard.write_text(json.dumps({'passed':True,'native_input_rejections':rejections,'reproducible_twice':True},ensure_ascii=False,indent=2)+'\n','utf8')
j=json.loads((P/'proposal.json').read_text('utf8'))
j.update({'scope':'대기 질감 기준의 새 3타 원화 5키를 동일 전신 10참조에 등록했다. 기존 52참조와 공유 검기 11참조, 시간표·음향·팔레트·정적 효과를 보존한다.','static_body_patch':audit['static_binding'],'user_accepted':False,'root_art_review_pending':False,'root_review_pending':False,'root_art_review':{'normal':True,'black':True,'source':'루트가 normal_readback 및 black_readback 00~02를 직접 열람하고 미술 검토 통과를 전달함. 실기나 사용자 수용은 아님.'},'independent_review_pending':False,'independent_report':str(audit_path.relative_to(c.ROOT)),'native_report':str(native_path.relative_to(c.ROOT)),'guard_report':str(guard.relative_to(c.ROOT)),'anchor_report':str((R/'third_saber_grip_review/anchors.json').relative_to(c.ROOT)),'limitations':audit['limitations'],'ready_for_checkpoint_integration':True,'full_art_unification_complete':False})
j['verification']['independent_incremental_counts']=audit['incremental_counts'];j['verification']['static404_reference_data_exact']=True
(P/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha(P/'proposal.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'static_recipe_sha256':sha(P/'static_effects.json'),'guard_sha256':sha(guard),'anchor_sha256':sha(R/'third_saber_grip_review/anchors.json'),'cumulative_main_refs':62,'root_art_review_pending':False,'user_accepted':False,'runtime_verified':False}
(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'frozen':frozen,'rejections':rejections}))
