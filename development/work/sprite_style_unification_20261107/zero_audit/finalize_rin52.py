from pathlib import Path
import sys,json,hashlib,copy,os
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_burst_variant as module
from scripts.build_sprite_style_unification import check_static_body
c=module.core;c.EXPECTED_SHA={'b1_185':'85871ee3c0804c886b6ea80134e949a97f5bc23edb9dc7c411b8c7246d96ac21'};e=c.engine;arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejections=[]
for case in('wrong_parent','missing_art','changed_authored_pixel','index16'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_art':del t[1,185]
 elif case=='changed_authored_pixel':t[1,185][164,160]^=1
 else:t[1,185][164,160]=16
 try:e.build(a,t)
 except ValueError as exc:rejections.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
P=R/'prepared_burst_pair_final_v1';new=(P/'PL01_U.ARC').read_bytes();old=(R/'prepared_air_continuation2_v2/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();guard=R/'rin52_guard_review';guard.mkdir(exist_ok=True)
j=json.loads((P/'proposal.json').read_text('utf8'));positive=check_static_body(old,new,j['static_body_patch']);negative=[]
for case in('wrong_declared_ref','empty_scope','outside_scope','wrong_recipe_hash'):
 folder=guard/case;folder.mkdir(exist_ok=True);r=json.loads((P/'static_effects.json').read_text('utf8'))
 evidence=(P/r['palette_evidence_file']).resolve();r['palette_evidence_file']=os.path.relpath(evidence,folder)
 for name in('palette.bin','effect_23.png','effect_24.png'):(folder/name).write_bytes((P/name).read_bytes())
 if case=='wrong_declared_ref':r['expected_changed_references']=[[6,24]]
 elif case=='empty_scope':r['expected_changed_references']=[]
 elif case=='outside_scope':r['expected_changed_references']=[[6,25]]
 file=folder/'static_effects.json';file.write_text(json.dumps(r,indent=2)+'\n','utf8');binding={'recipe':str(file.relative_to(c.ROOT)),'sha256':sha(file.read_bytes())if case!='wrong_recipe_hash'else'0'*64}
 try:check_static_body(old,new,binding)
 except ValueError as exc:negative.append({'case':case,'reason':str(exc)})
 else:raise AssertionError('Unsafe static binding accepted')
guards={'passed':True,'positive':positive,'negative':negative,'native_input_rejections':rejections};(guard/'guard_checks.json').write_text(json.dumps(guards,ensure_ascii=False,indent=2)+'\n','utf8')
audit=json.loads((R/'final52_readback_audit.json').read_text('utf8'));native=json.loads((R/'rin52_components_native_checks.json').read_text('utf8'));assert audit['passed']and native['passed']
j['verification']={'increment_from50':audit['incremental_counts'],'cumulative_authored_refs':52,'previous50_art_exact':True,'entire_parts_exact':True,'palette_audio_other_entries_exact':True,'native_bank_boundaries_exact':True,'native_max_tiles':32,'static24_unchanged_from50':True,'static23_old_and_new_body_reconstruction_exact':True,'other403_static_references_exact_from50':True}
j.update({'user_accepted':False,'root_art_review_pending':True,'independent_review_pending':False,'independent_report':str((R/'final52_readback_audit.json').relative_to(c.ROOT)),'native_report':str((R/'rin52_components_native_checks.json').relative_to(c.ROOT)),'guard_report':str((guard/'guard_checks.json').relative_to(c.ROOT)),'rejections':rejections,'limitations':audit['limitations'],'ready_for_checkpoint_integration':True,'full_art_unification_complete':False})
(P/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha((P/'proposal.json').read_bytes()),'independent_sha256':sha((R/'final52_readback_audit.json').read_bytes()),'native_sha256':sha((R/'rin52_components_native_checks.json').read_bytes()),'static_recipe_sha256':sha((P/'static_effects.json').read_bytes()),'cumulative_main_refs':52,'root_art_review_pending':True,'user_accepted':False,'runtime_verified':False}
(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'frozen':frozen,'native_parts':native['resources']['PL01_U.ARC']['GPU_part_edge_checks'],'rejections':rejections,'static_rejections':negative}))
