from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_priority_victory as module
c=module.core;e=c.engine;arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejections=[]
for case in('wrong_parent','missing_art','changed_authored_pixel','index16'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_art':del t[1,5]
 elif case=='changed_authored_pixel':t[1,5][164,160]^=1
 else:t[1,5][164,160]=16
 try:e.build(a,t)
 except ValueError as exc:rejections.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
p=R/'prepared_priority_final_v2/proposal.json';j=json.loads(p.read_text('utf8'));audit=json.loads((R/'final50_readback_audit.json').read_text('utf8'));native=json.loads((R/'rin50_components_native_checks.json').read_text('utf8'))
assert audit['passed']and native['passed'];j['verification']={'cumulative_independent_counts':audit['counts'],'increment_from42':{'art_references':8,'shared_support_raw_references':4,'static_references_changed':[24]},'palette_audio_other_entries_exact':True,'native_bank_boundaries_exact':True,'native_max_tiles':32,'existing42_exact':True,'static23_unchanged':True,'static24_old_and_new_body_reconstruction_exact':True,'other403_static_references_exact':True}
j.update({'user_accepted':False,'root_review_only':True,'independent_review_pending':False,'independent_report':str((R/'final50_readback_audit.json').relative_to(c.ROOT)),'native_report':str((R/'rin50_components_native_checks.json').relative_to(c.ROOT)),'guard_report':str((R/'rin50_guard_review/guard_checks.json').relative_to(c.ROOT)),'rejections':rejections,'limitations':audit['limitations'],'ready_for_checkpoint_integration':True,'full_art_unification_complete':False})
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha(p),'independent_sha256':sha(R/'final50_readback_audit.json'),'native_sha256':sha(R/'rin50_components_native_checks.json'),'static_recipe_sha256':sha(p.parent/'static_effects.json'),'cumulative_main_refs':50,'source_review':'root only','user_accepted':False,'runtime_verified':False}
(p.parent/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8')
(R/'prepared_priority_final_v1/NOT_A_BUILD.txt').write_text('정적24만 변경하는 후보를 기존 helper가 두 참조 변경 필수 규칙으로 거부한 중간 자료입니다. ARC가 없으며 통합 대상이 아닙니다. 최종 준비본은 prepared_priority_final_v2입니다.\n','utf8')
print(json.dumps({'frozen':frozen,'rejections':rejections,'native_counts':{k:v for k,v in native['resources']['PL01_U.ARC'].items()if k!='banks'}}))
