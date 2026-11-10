"""Promote the verified v2 candidate; original inputs and game data are read-only."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):(ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
B='out/ver_buki_riko/riko_motion_20261024T024352897084Z'
V=B+'/ground_validation_20261024T025508722696Z'
M='work/ver_buki_riko/production_master/20261024T024429065616Z'
S='work/ver_buki_riko/emulator_sessions/20261024T024408334939Z'
D='work/ver_buki_riko/art_pilot/ground_slash_v2'
P='projects/ver_buki_riko/'
manifest=read(B+'/manifest.json');sha=manifest['modified_bin']['sha256']
assert digest(ROOT/B/'riko_motion.bin')==sha
runtime=read(V+'/runtime_summary.json');assert runtime['bin_sha256']==sha
old=read(V+'/previous_current_build.json')
all_refs=set(range(53))|{146,147,148}|set(runtime['ground_body_refs'])
verified=set(runtime['new_body_render_verified'])|{147}
inherited=(set(old['runtime_verified_frames'])|set(old['runtime_inherited_unchanged_frames']))-verified
missing=all_refs-verified-inherited;assert missing==set(runtime['new_body_full_render_unverified'])|{32,41,42,43,44}
current={**old,'kind':'idle_jump_run_dash_wall_ground_slash_candidate','build':B,'cue':B+'/riko_motion.cue','bin_sha256':sha,
 'previous_build':old['build'],'previous_bin_sha256':old['bin_sha256'],'session':S,'session_closed':False,
 'session_state_at_last_observation':'Paused in game menu; only one ePSXe instance observed',
 'session_state_evidence':S+'/20261024T030000695150Z.png','agent_created_save_state':False,
 'user_assisted_runtime':False,'initial_v1_gameplay_user_assisted':True,'boot_navigation_fully_observed':False,
 'motion_set':'work/ver_buki_riko/scale_frames/20261024T024335915417Z/motion_set.json',
 'runtime_summary':V+'/runtime_summary.json','runtime_verified_frames':sorted(verified),
 'runtime_inherited_unchanged_frames':sorted(inherited),'runtime_unverified_current_build_frames':sorted(all_refs-verified),
 'runtime_unverified_any_evidence_frames':sorted(missing),'existing_56_frames_byte_preserved':True,
 'riko_reference_count':96,'all_current_frames_preview':M+'/riko_master_preview_2x.png',
 'ground_slash_art':D,'ground_slash_runtime_full_render_unverified':runtime['new_body_full_render_unverified'],
 'ground_slash_style_user_review_pending':True,'ground_slash_cape_fix_implemented':True,
 'next_task':'Validate remaining obscured renders and animation104 shared recovery; inspect next attack group',
 'report':'docs/RIKO_GROUND_SLASH.md','runtime_previous_summary':old['runtime_summary']}
current.pop('session_exit_observation',None)
art=read(V+'/previous_art_selection.json')
art.update({'status':'accepted_design_basis_ground_slash_candidate_applied_review_pending',
 'game_applied_scope':'96 body references; original56 PNGs preserved; ground40 RAM/VRAM verified, ground29 plus idle147 full opaque render evidence per direction',
 'runtime_verified_build':B,'runtime_evidence':'docs/RIKO_GROUND_SLASH.md','runtime_summary':V+'/runtime_summary.json',
 'runtime_verified_frame_scope':sorted(verified),'runtime_limitations':{'unverified_frames_including_inherited_evidence':sorted(missing),
 'ground_body_full_render_unverified':runtime['new_body_full_render_unverified'],'wall_left_runtime_verified':False,
 'shared_animation104_unverified':True,'sword_design_implemented':False,
 'other_evidence':'Current idle147 retested; unchanged older body frames inherit prior results; strict and pipeline evidence kept separate'},
 'ground_slash_production_implemented':True,'ground_slash_cape_revision_implemented':True,'ground_slash_style_user_review_pending':True,
 'ground_slash_art_directory':D,'historical_selection_snapshot':V+'/previous_art_selection.json'})
master=read(V+'/previous_master_sheet.json')
master.update({'source_build':B,'source_bin_sha256':sha,'directory':M,'master':M+'/master.local.json',
 'sheet':M+'/riko_master_indexed.png','preview':M+'/riko_master_preview_2x.png',
 'roundtrip':'work/ver_buki_riko/master_split/20261024T024441552560Z/validation.local.json',
 'guard_checks':D+'/guard_checks.json','riko_references':96,'whole_character_completed':False,
 'preserved_effect_reference_count':34,'ground_slash_art_review_pending':True,
 'next_group':'ground_slash_remaining_render_and_animation104_shared_recovery','report':'docs/RIKO_GROUND_SLASH.md'})
for name,data in [('current_build.json',current),('art_selection.json',art),('master_sheet.json',master)]:
    # Refuse to replace unexpected concurrent user changes; allow identical re-publication.
    actual=read(P+name);previous=read(V+'/previous_'+name)
    assert actual==previous or actual==data, 'Pointer changed since review: '+name
    write(P+name,data)
print(json.dumps({'build':B,'sha256':sha,'body_refs':len(all_refs),'verified_current':len(verified),'inherited':len(inherited),'full_render_missing':sorted(missing)}))
