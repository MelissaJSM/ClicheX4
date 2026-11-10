from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.build_riko_idle import SABER_EFFECT_FRAMES
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def write(p,d):(ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
B='out/ver_buki_riko/riko_motion_20261024T031656659594Z';V=B+'/air_validation_20261024T032929976437Z'
M='work/ver_buki_riko/production_master/20261024T031722651640Z';D='work/ver_buki_riko/art_pilot/air_slash_v1';S='work/ver_buki_riko/emulator_sessions/20261024T031712603353Z';P='projects/ver_buki_riko/'
manifest=read(B+'/manifest.json');sha=manifest['modified_bin']['sha256'];assert digest(ROOT/B/'riko_motion.bin')==sha
r=read(V+'/runtime_summary.json');old=read(V+'/previous_current_build.json');all_refs=set(map(int,manifest['frame_inputs']))-SABER_EFFECT_FRAMES;verified=set(r['current_render_verified_frames'])
inherited=(set(old['runtime_verified_frames'])|set(old['runtime_inherited_unchanged_frames']))-verified
missing=all_refs-verified-inherited;assert len(all_refs)==114 and len(missing)==26
current={**old,'kind':'idle_jump_run_dash_wall_ground_air_slash_candidate','build':B,'cue':B+'/riko_motion.cue','bin_sha256':sha,
 'previous_build':old['build'],'previous_bin_sha256':old['bin_sha256'],'session':S,'session_closed':False,
 'session_state_at_last_observation':'Paused in game menu; one ePSXe observed','session_state_evidence':S+'/20261024T032930381354Z.png',
 'boot_navigation_fully_observed':True,'zero_selection_observed':True,'agent_loaded_save_state':False,'agent_created_save_state':False,'user_assisted_runtime':False,
 'motion_set':'work/ver_buki_riko/scale_frames/20261024T031638483272Z/motion_set.json','runtime_summary':V+'/runtime_summary.json',
 'runtime_verified_frames':sorted(verified),'runtime_inherited_unchanged_frames':sorted(inherited),
 'runtime_unverified_current_build_frames':sorted(all_refs-verified),'runtime_unverified_any_evidence_frames':sorted(missing),
 'existing_96_body_frames_byte_preserved':True,'riko_reference_count':114,'all_current_frames_preview':M+'/riko_master_preview_2x.png',
 'ground_slash_style_user_review_pending':False,'air_slash_art':D,'air_slash_style_user_review_pending':True,
 'air_slash_body_loaded_both_directions':True,'air_slash_full_render_unverified':r['new_body_full_render_unverified'],
 'report':'docs/RIKO_AIR_SLASH.md','runtime_previous_summary':old['runtime_summary'],
 'next_task':'Inspect ladder and wall saber sharing and replay conditions; retain pending effect-occluded render checks'}
art=read(V+'/previous_art_selection.json')
art.update({'status':'accepted_ground_slash_basis_air_landing_candidate_review_pending','game_applied_scope':'114 body references; original96 body plus34 effects unchanged; new18 data verified both directions, new7 full visible-pixel evidence both directions',
 'runtime_verified_build':B,'runtime_evidence':'docs/RIKO_AIR_SLASH.md','runtime_summary':V+'/runtime_summary.json','runtime_verified_frame_scope':sorted(verified),
 'runtime_limitations':{'unverified_frames_including_inherited_evidence':sorted(missing),'new_air_landing_full_render_unverified':r['new_body_full_render_unverified'],
 'wall_left_runtime_verified':False,'shared_animation104_unverified':True,'sword_design_implemented':False,
 'other_evidence':'Unchanged old frames inherit earlier evidence; current21/22/23/32/33/34/147 rechecked; same-sample and pipeline checks distinguished'},
 'ground_slash_style_user_review_pending':False,'air_slash_production_implemented':True,'air_slash_style_user_review_pending':True,'air_slash_art_directory':D,
 'historical_selection_snapshot':V+'/previous_art_selection.json'})
master=read(V+'/previous_master_sheet.json')
master.update({'source_build':B,'source_bin_sha256':sha,'directory':M,'master':M+'/master.local.json','sheet':M+'/riko_master_indexed.png',
 'preview':M+'/riko_master_preview_2x.png','roundtrip':'work/ver_buki_riko/master_split/20261024T031750844443Z/validation.local.json',
 'guard_checks':D+'/guard_checks.json','riko_references':114,'preserved_effect_reference_count':50,'whole_character_completed':False,
 'ground_slash_art_review_pending':False,'air_slash_art_review_pending':True,'report':'docs/RIKO_AIR_SLASH.md','next_group':'ladder_wall_saber_structure_and_replay_conditions'})
for name,data in [('current_build.json',current),('art_selection.json',art),('master_sheet.json',master)]:
 actual=read(P+name);previous=read(V+'/previous_'+name);assert actual==previous or actual==data,'Concurrent pointer change: '+name;write(P+name,data)
print(json.dumps({'build':B,'body':len(all_refs),'current_render_verified':len(verified),'inherited':len(inherited),'remaining_full_render':len(missing)}))
