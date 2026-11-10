import json,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.project import digest
D=R/'work/ver_rin_nana/nana_ultimate_armor';e=R/'work/ver_rin_nana/armor_capture/20261104T103035739673Z/verification.local.json';v=json.loads(e.read_text('utf8'));assert v['verified_frames']==list(range(120,126))
deployment=json.loads((D/'low_hp_shape_deployment.json').read_text('utf8'))
for q in deployment['cards']:assert digest(R/q['path'])==q['sha256']
for f in ('current_build.json','nana_ultimate_candidate.json'):
 p=R/'projects/ver_rin_nana'/f;c=json.loads(p.read_text('utf8'));assert c['sha256']==v['modified_bin_sha256'];c.update(stage='LADDER_PRODUCTION',ultimate_low_hp_user_accepted=True,ultimate_low_hp_acceptance_quote='좋아 지금이면 충분해 다음작업으로 넘어가도좋아',ultimate_low_hp_runtime_assets_verified=True,ultimate_low_hp_full_screen_frames=v['verified_frames'],ultimate_low_hp_runtime_evidence=e.relative_to(R).as_posix(),control_handed_to_user=True,next_scope='Produce Ultimate ladder143..155/183 with accepted idle body volume and Sarang-i')
 p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
handoff=dict(build=deployment['build']['build'],sha256=v['modified_bin_sha256'],runtime_evidence=e.relative_to(R).as_posix(),frames=v['verified_frames'],user_accepted=True,acceptance_quote='좋아 지금이면 충분해 다음작업으로 넘어가도좋아',cards_preserved=True,control_handed_to_user=True,automatic_input_stopped=True,refreshed_state_sha256=deployment['state_sha256'],latest_saved_progress=deployment['saved'],subsequent_user_progress_not_rewound=True)
(D/'low_hp_shape_handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
