import json,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.project import digest
D=R/'work/ver_rin_nana/nana_ultimate_armor';e=R/'work/ver_rin_nana/armor_capture/20261104T104443827182Z/verification.local.json';v=json.loads(e.read_text('utf8'));assert all(all(q['complete_entries_match'].values())for q in v['checked_ram_entries']);deployment=json.loads((D/'ladder_deployment.json').read_text('utf8'))
cards=[]
for q in deployment['cards']:cards.append(dict(path=q['path'],unchanged=digest(R/q['path'])==q['sha256']))
for name in('current_build.json','nana_ultimate_candidate.json'):
 p=R/'projects/ver_rin_nana'/name;c=json.loads(p.read_text('utf8'));assert c['sha256']==v['modified_bin_sha256'];c.update(stage='CEREMONY_PRODUCTION',ultimate_ladder_user_accepted=True,ultimate_ladder_acceptance_quote='오케이 충분해 다음으로 넘어가도 좋아',ultimate_ladder_loaded_arc_verified=True,ultimate_ladder_runtime_assets_verified=False,ultimate_ladder_exhaustive_runtime_verified=False,ultimate_ladder_runtime_evidence=e.relative_to(R).as_posix(),control_handed_to_user=True,next_scope='Produce Ultimate arrival/ready/victory/return138,139,141,142,156,157,204..207');p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(D/'ladder_handoff.json').write_text(json.dumps(dict(build=deployment['build']['build'],sha256=v['modified_bin_sha256'],runtime_evidence=e.relative_to(R).as_posix(),user_accepted=True,acceptance_quote='오케이 충분해 다음으로 넘어가도 좋아',cards=cards,control_handed_to_user=True,automatic_input_stopped=True,refreshed_state_sha256=deployment['state_sha256'],latest_saved_progress=deployment['saved'],subsequent_user_progress_not_rewound=True),ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(cards))
