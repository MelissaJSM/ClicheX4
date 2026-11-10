import json,sys,importlib.util
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.project import digest
D=R/'work/ver_rin_nana/nana_ultimate_armor';e=R/'work/ver_rin_nana/armor_capture/20261104T105703747488Z/verification.local.json';v=json.loads(e.read_text('utf8'));assert all(all(q['complete_entries_match'].values())for q in v['checked_ram_entries']);sample=next(q for q in v['samples_without_full_match']if q['frame']==147);assert sample['ram_equal']and sample['vram_equal'];deployment=json.loads((D/'ceremony_deployment.json').read_text('utf8'));cards=[]
for q in deployment['cards']:
 same=digest(R/q['path'])==q['sha256'];assert same;cards.append(dict(path=q['path'],unchanged=same))
spec=importlib.util.spec_from_file_location('progress',D/'ceremony_progress.py');progress=importlib.util.module_from_spec(spec);spec.loader.exec_module(progress);now=progress.player()
for name in('current_build.json','nana_ultimate_candidate.json'):
 p=R/'projects/ver_rin_nana'/name;c=json.loads(p.read_text('utf8'));assert c['sha256']==v['modified_bin_sha256'];c.update(ultimate_ceremony_loaded_arc_verified=True,ultimate_ceremony_baseline_ram_vram_verified=True,ultimate_ceremony_baseline_full_screen_verified=False,ultimate_ceremony_runtime_assets_verified=False,ultimate_ceremony_exhaustive_runtime_verified=False,ultimate_ceremony_user_accepted=False,ultimate_ceremony_runtime_evidence=e.relative_to(R).as_posix(),ultimate_ceremony_handoff=(D/'ceremony_handoff.json').relative_to(R).as_posix(),control_handed_to_user=True);p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
handoff=dict(build=deployment['build']['build'],sha256=v['modified_bin_sha256'],runtime_evidence=e.relative_to(R).as_posix(),user_accepted=False,cards=cards,control_handed_to_user=True,automatic_input_stopped=True,refreshed_state_sha256=deployment['state_sha256'],latest_saved_progress=deployment['saved'],current_player=now,subsequent_user_progress_not_rewound=True)
(D/'ceremony_handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(now))
