"""Record actual evidence and protected inputs without operating the emulator."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.project import digest,load_project,inspect_references

def put(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

pointer=json.loads((ROOT/'projects/ver_buki_riko/shibuki_ui_candidate.json').read_text('utf8'))
build=ROOT/pointer['build'];manifest=json.loads((build/'manifest.json').read_text('utf8'))
if digest(build/'shibuki_riko.bin')!=pointer['bin_sha256'] or digest(build/'modified.arc')!=pointer['arc_sha256']:
    raise ValueError('Final output changed')
project=load_project(ROOT,'ver_buki_riko');references=inspect_references(ROOT,project)
records=json.loads((Path(__file__).parent/'user_backup/manifest.json').read_text('utf8'))
records += [{'path':project['source_bin'],'sha256':project['source_sha256']},
    {'path':str(Path(manifest['parent_build'])/'shibuki_riko.bin'),'sha256':manifest['parent_bin_sha256']},
    {'path':'out/ver_buki_riko/shibuki_fourth_hover_alignment_20261027T033818587949Z/shibuki_riko.bin',
     'sha256':'6acc792ad365d091405e44d91d857e06b6ac806182769c8edad90e0d2f615ad0'}]
for record in records:
    path=ROOT/record['path'];actual=digest(path)
    if actual!=record['sha256']:raise ValueError('Protected input changed: '+record['path'])
    record.update(size=path.stat().st_size,verified=True)
put(build/'preservation.local.json',{'protected_files':records,'references':references,
    'all_matched':True,'save_states_replaced':False,'F1_F3_sent':False})
selection=ROOT/'work/ver_buki_riko/emulator_sessions/20261027T060353965298Z/20261027T060429356978Z.png'
save=ROOT/'work/ver_buki_riko/emulator_sessions/20261027T055108718804Z/20261027T055154705994Z.png'
previous=ROOT/'out/ver_buki_riko/shibuki_ui_dash_fix_20261027T054925036760Z'
for name in ['LOAD_U.ARC','MOJIPAT.ARC']:
    if (build/name).read_bytes()!=(previous/name).read_bytes():raise ValueError('Accepted save icon changed')
evidence={'build_sha256':pointer['bin_sha256'],'session':pointer['session'],
    'selection':{'screenshot':str(selection.relative_to(ROOT)),'sha256':digest(selection),'fresh_boot':True,
        'agent_visually_checked':True,'user_quote':pointer['user_acceptance']['selection_fix']},
    'save_icon':{'screenshot':str(save.relative_to(ROOT)),'sha256':digest(save),'fresh_boot':True,
        'tested_build':str(previous.relative_to(ROOT)),'resources_identical_in_final_build':True,
        'user_quote':pointer['user_acceptance']['load_icon_fix']},
    'runtime_scope':pointer['runtime_scope'],'process_memory_written':False,
    'F1_F3_sent':False,'further_input_stopped_after_acceptance':True,
    'input_interruption':'Title input playback stopped on focus change; no complete automatic playback claim.'}
put(build/'runtime_summary.local.json',evidence)
manifest.update(runtime_scope=pointer['runtime_scope'],user_acceptance=pointer['user_acceptance'],
    runtime_evidence='runtime_summary.local.json',preservation_evidence='preservation.local.json')
put(build/'manifest.json',manifest)
print(json.dumps({'build':pointer['build'],'protected_files':len(records),
    'references':len(references),'selection_save_user_accepted':True,'all_runtime_verified':False}))
