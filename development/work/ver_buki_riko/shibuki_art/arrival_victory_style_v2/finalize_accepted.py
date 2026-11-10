"""사용자 수용 기록과 읽기 전용 보존 검사. 게임 조작은 수행하지 않는다."""
import gzip, hashlib, json, shutil, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent
build=ROOT/'out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z'
rel=lambda p:p.relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1<<20):h.update(b)
 return h.hexdigest()
rows=[]
for row in read(d/'preservation_before_approval.local.json')['files']:
 actual=digest(ROOT/row['path']);rows.append({'path':row['path'],'expected_sha256':row['sha256'],'sha256':actual,'matches':actual==row['sha256']})
if not all(r['matches'] for r in rows):raise ValueError('Protected input changed: '+repr([r for r in rows if not r['matches']]))
write(build/'final_preservation.local.json',{'files':rows,'all_match':True})
quote='내가  테스트다했어 이정도면 충분해'
targets=list(range(133,140))+list(range(204,208))
evidence='work/ver_buki_riko/live_poc/20261026T235623132309Z/verification.local.json'
trace='work/ver_buki_riko/shibuki_batch_runtime/20261026T235651197740Z/trace.json'
runtime={'build':rel(build),'bin_sha256':read(build/'manifest.json')['modified_bin']['sha256'],
 'fresh_launch_session':'work/ver_buki_riko/emulator_sessions/20261026T235522552420Z',
 'full_repacked_bank_matches':True,'verified_idle_frame':0,'ram_vram_framebuffer_evidence':evidence,
 'character':0,'hp_observed':48,'armor_observed':0,'boss_flags_observed':255,
 'assistant_F3_used':False,'graphics_refreshed_test_state_used':False,'process_memory_written':False,
 'working_F1_pressed':True,'working_files_backed_up_before_test':rel(d/'before_runtime_backup/backup.json'),
 'special_trial_completed':False,'special_trial_trace':trace,'special_trial_failure':read(ROOT/trace)['failure'],
 'new11_automated_full_cycle_verified':False,'user_playtest_accepted':True,'user_quote':quote,
 'user_playtest_frame_by_frame_evidence_available':False,'further_game_control_stopped_on_user_request':True,
 'session_closed_observed':True,'session_closed_by_assistant':False}
save=ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/sstates/SLUS_005.61.000'
savedir=build/'working_save_snapshot';savedir.mkdir(exist_ok=False)
shutil.copy2(save,savedir/save.name)
if digest(save)!=digest(savedir/save.name):raise ValueError('Save snapshot mismatch')
runtime.update(working_save_snapshot=rel(savedir/save.name),working_save_sha256=digest(save),working_save_kind='emulator F1; snapshot only, F3 replay not performed this turn')
write(build/'runtime_summary.local.json',runtime)
manifest=read(build/'manifest.json');manifest.update(kind='shibuki_arrival_victory_style_user_accepted',runtime_verified=True,runtime_verified_scope='full bank loading and idle0 RAM/VRAM/framebuffer only',style_revision_runtime_complete=False,new_animation_user_review_pending=False,user_playtest_accepted=True,user_acceptance_quote=quote,user_acceptance_date='2026-10-27',runtime_summary=rel(build/'runtime_summary.local.json'))
write(build/'manifest.json',manifest)
parent=read(d/'before_runtime_backup/shibuki_current_build.json')
v={**parent,'kind':'shibuki_arrival_victory_style_user_accepted','build':rel(build),'cue':rel(build/'shibuki_riko.cue'),'bin_sha256':manifest['modified_bin']['sha256'],'arc_sha256':manifest['modified_archive_sha256'],
 'parent_build':parent['build'],'parent_bin_sha256':parent['bin_sha256'],'parent_accepted_build':'projects/ver_buki_riko/shibuki_special_style_accepted_build.json',
 'active_art_study':rel(d),'final_art':rel(d/'production09'),'runtime_summary':rel(build/'runtime_summary.local.json'),
 'runtime_verified_frames':[0],'runtime_special_both_directions_frames':[],
 'session':runtime['fresh_launch_session'],'session_closed':True,'session_paused':None,'session_pause_capture':None,
 'working_save':runtime['working_save_snapshot'],'working_save_kind':runtime['working_save_kind'],
 'report':'docs/SHIBUKI_ARRIVAL_VICTORY_STYLE.md','style_revision_frames':targets,'style_revision_user_accepted':True,
 'style_revision_user_quote':quote,'style_revision_acceptance_date':'2026-10-27','style_revision_runtime_complete':False,
 'new_animation_user_review_pending':False,'new_animation_user_review_scope':targets,
 'inherited_runtime_summary':parent['runtime_summary'],'final_preservation':rel(build/'final_preservation.local.json'),
 'resources_relocated_within_bank':True,'archive_size_and_lba_preserved':True,'next_group':'await_next_user_task',
 'additional_automatic_testing_stopped_by_user':True}
for name in ('current_build.json','shibuki_current_build.json','shibuki_arrival_victory_accepted_build.json'):
 write(ROOT/'projects/ver_buki_riko'/name,v)
p=ROOT/'projects/ver_buki_riko/shibuki_pending_revision.json';pending=read(p);pending.update(kind='arrival_victory_revision_closed_user_accepted',pending=False,user_accepted=True,user_acceptance_quote=quote,runtime_verified=True,runtime_verified_scope='bank loading and idle0 only',all_target_frames_automatically_verified=False,current_build_pointer_changed=True);write(p,pending)
p=d/'provenance.json';prov=read(p);prov.update(user_accepted=True,user_acceptance_quote=quote,user_acceptance_date='2026-10-27');write(p,prov)
write(build/'static_summary.json',{'unittests_passed':179,'negative_inputs_passed':read(d/'negative_inputs.json'),'repeat_arc_equal':read(build/'determinism.json'),'checked_graphics_references':508,'checked_other_compositions':1776,'changed_sectors':len(manifest['modified_bin']['changed_sectors']),'all_disc_sectors_compared':manifest['full_disc_sectors_compared'],'protected_hashes_matched':len(rows)})
print(json.dumps({'build':rel(build),'accepted':True,'protected_hashes_matched':len(rows),'changed_sectors':len(manifest['modified_bin']['changed_sectors']),'working_save_snapshot_sha256':runtime['working_save_sha256']}))
