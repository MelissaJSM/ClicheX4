from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import write_json,digest
D=Path(__file__).parent
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T012121410066Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T012141953805Z'
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T012142905863Z'
rel=lambda p:p.relative_to(ROOT).as_posix()
current_path=ROOT/'projects/ver_buki_riko/current_build.json';art_path=ROOT/'projects/ver_buki_riko/art_selection.json';master_path=ROOT/'projects/ver_buki_riko/master_sheet.json'
def save(path,document):
 if path.exists() and path not in (current_path,art_path,master_path):
  if json.loads(path.read_text('utf8'))!=document:raise ValueError('Existing evidence differs')
  return
 path.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
write_json=save
for path in (current_path,art_path,master_path):
 backup=D/('previous_'+path.name)
 if not backup.exists():shutil.copyfile(path,backup)
previous=json.loads((D/'previous_current_build.json').read_text('utf8'))
assert previous['bin_sha256']=='191999a414d842ca115e219303c6cc0a6d0c105ee4d5f03a7c58ec04f8eabede'
manifest=json.loads((B/'manifest.json').read_text('utf8'));numbers=sorted(map(int,manifest['frame_inputs']))
inherited=sorted((set(previous['runtime_verified_frames'])|set(previous['runtime_inherited_unchanged_frames']))-{147})
unverified=sorted(set(numbers)-set(inherited)-{147})
runtime={'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'direct_frames':[147],
 'wall_frames_verified':[],'wall_frames_unverified':list(range(35,44)),
 'baseline':'work/ver_buki_riko/live_poc/20261024T012314775813Z/verification.local.json',
 'observation_only_run':'work/ver_buki_riko/wall_runtime/20261024T012337590789Z/verification.local.json',
 'inherited_build':previous['build'],'inherited_unchanged_frames':inherited,'unverified_with_inherited_evidence':unverified,
 'session':rel(S),'session_closed':True,'close_evidence':rel(S/'close.local.json'),
 'agent_loaded_save_state':False,'agent_process_memory_written':False,'boot_navigation_fully_observed':False,
 'boot_observation':'Zero Sky Lagoon loading and character1/full patched graphics bank confirmed; selection navigation not continuously observed',
 'wall_attempt':'Ordinary directional/jump/dash/saber inputs; repeated deaths and mission failed before useful wall samples. Later observation rejected stale baseline after game-over resource change.',
 'mission_failed_capture':rel(S/'20261024T012734227080Z.png'),'whole_character_completed':False}
write_json(B/'runtime_summary.json',runtime)
current={'project':'ver_buki_riko','task':'zero_riko','stage':'ZERO_PRODUCTION','kind':'idle_jump_run_dash_wall_candidate',
 'build':rel(B),'cue':rel(B/'riko_motion.cue'),'bin_sha256':manifest['modified_bin']['sha256'],'source_sha256':manifest['source_sha256'],
 'previous_build':previous['build'],'previous_bin_sha256':previous['bin_sha256'],
 'session':rel(S),'session_closed':True,'session_exit_observation':'Agent Escape close confirmed process exited',
 'fresh_process_launch_verified':True,'boot_navigation_fully_observed':False,'agent_loaded_save_state':False,
 'idle_frames':previous['idle_frames'],'idle_revision':previous['idle_revision'],
 'motion_set':'work/ver_buki_riko/scale_frames/20261024T012048733813Z/motion_set.json',
 'runtime_summary':rel(B/'runtime_summary.json'),'runtime_verified_frames':[147],
 'runtime_inherited_unchanged_frames':inherited,'runtime_unverified_current_build_frames':[n for n in numbers if n!=147],
 'runtime_unverified_any_evidence_frames':unverified,'wall_runtime_verified':False,'wall_style_user_review_pending':True,
 'existing_47_frames_byte_preserved':True,'riko_reference_count':56,'production_master':'projects/ver_buki_riko/master_sheet.json',
 'all_current_frames_preview':rel(M/'riko_master_preview_2x.png'),'wall_context_preview':rel(B/'wall_context_sheet.png'),
 'next_task':'Validate wall grab/kick/slide both orientations before expanding to attacks','report':'docs/RIKO_WALL_PRODUCTION.md'}
write_json(current_path,current)
master={'project':'ver_buki_riko','task':'zero_riko','kind':'editable_master_sheet','source_build':rel(B),
 'source_bin_sha256':manifest['modified_bin']['sha256'],'directory':rel(M),'master':rel(M/'master.local.json'),
 'sheet':rel(M/'riko_master_indexed.png'),'preview':rel(M/'riko_master_preview_2x.png'),
 'roundtrip':'work/ver_buki_riko/master_split/20261024T012202968819Z/validation.local.json',
 'guard_checks':rel(D/'guard_checks.json'),'riko_references':56,'whole_character_completed':False,
 'new_wall_art_created':True,'wall_art_review_pending':True,'wall_runtime_verified':False,'next_group':'wall_runtime_validation',
 'report':'docs/RIKO_WALL_PRODUCTION.md'}
write_json(master_path,master)
art=json.loads(art_path.read_text('utf8'));art.update({'status':'accepted_design_basis_wall_candidate_applied_review_pending',
 'game_applied_scope':'56 bank0 references in candidate BIN; original47 PNGs preserved; only147 freshly runtime verified',
 'runtime_verified_build':rel(B),'runtime_evidence':'docs/RIKO_WALL_PRODUCTION.md','runtime_summary':rel(B/'runtime_summary.json'),
 'runtime_verified_frame_scope':[147],'wall_production_implemented':True,'wall_style_user_review_pending':True,
 'wall_runtime_verified':False,'wall_head_view_standard':'config/riko_wall_head_view.json',
 'historical_selection_snapshot':rel(D/'previous_art_selection.json')})
art['runtime_limitations']={'unverified_frames_including_inherited_evidence':unverified,'wall_frames_not_observed':list(range(35,44)),
 'other_evidence':'Unchanged47 images inherit older results, not fresh wall validation','prior_details':rel(D/'previous_art_selection.json')}
write_json(art_path,art)
calls=[]
for i,(prompt,filename,generated) in enumerate([
 ('prompt.txt','generated_wall_v1.png','exec-2d3970b3-7b1c-4200-8a80-6964f8440809.png'),
 ('prompt_refine.txt','generated_wall_v2.png','exec-87492813-95e0-4358-8b3e-8b3eed8723ba.png'),
 ('prompt_fit.txt','generated_wall_v3.png','exec-373af389-a5ff-4771-bada-5422f451750b.png')],1):
 calls.append({'call':i,'tool':'built-in image_gen.imagegen','prompt':rel(D/prompt),'prompt_sha256':digest(D/prompt),
 'workspace_image':rel(D/filename),'image_sha256':digest(D/filename),'generated_filename':generated,'transparent_background':True})
write_json(D/'imagegen_calls.local.json',{'calls':calls,'call_count':3,'used_for_final_art':3,'rom_bios_save_state_sent':False,'api_cli_used':False})
for name in ('imagegen_calls.local.json','guard_checks.json','tests.log'):shutil.copyfile(D/name,B/name)
history=ROOT/'docs/history/STATUS_20261024_BEFORE_WALL_PRODUCTION.md'
if not history.exists():shutil.copyfile(ROOT/'docs/STATUS.md',history)
print(json.dumps({'build':rel(B),'references':56,'fresh_runtime_frames':[147],'unverified_with_inheritance':unverified,'master':rel(M)}))
