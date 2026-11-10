from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[4]
ART=Path(__file__).parent
BUILD=ROOT/'out/ver_buki_riko/shibuki_weapon_palette_20261026T170706783998Z'
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,data): Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(path): return Path(path).resolve().relative_to(ROOT).as_posix()
def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

manifest=read(BUILD/'manifest.json')
assert sha(BUILD/'shibuki_riko.bin')==manifest['modified_bin']['sha256']
assert sha(BUILD/'modified.arc')==manifest['modified_archive_sha256']
backups=ROOT/'work/ver_buki_riko/shibuki_all_boss_save/20261026T162502779077Z'
preserved=[]
for entry in read(backups/'backup.json'):
    actual=sha(ROOT/entry['source']); copied=sha(ROOT/entry['backup'])
    assert actual==copied==entry['sha256'],entry['source']
    preserved.append({'file':entry['source'],'sha256':actual,'backup_sha256':copied,'unchanged':True})
for file,expected in [('MegaMan X4.bin','3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),('out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin','1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246')]:
    actual=sha(ROOT/file);assert actual==expected,file
    preserved.append({'file':file,'sha256':actual,'unchanged':True})
write(BUILD/'final_preservation.local.json',preserved)

runs=[];verified=set();directions={'left':set(),'right':set()}
for file,side,flag in [('weapon_runs.json','right',64),('weapon_left_runs.json','left',0)]:
    for entry in read(ART/file):
        path=Path(entry['output']);data=read(path/'verification.local.json');trace=read(path/'trace.json')
        assert data['modified_bin_sha256']==manifest['modified_bin']['sha256']
        assert entry['selection_verified'] and trace['failure'] is None
        assert all(row[1]==0 and row[10]==0 and row[11]==255 for row in trace['rows'])
        matches={row['frame'] for row in data['results'] if row['ram_equal'] and row['vram_equal'] and row['render_matches']}
        selected=[row for row in data['results'] if row['weapon']==entry['weapon']]
        assert selected and all(row['base_palette_observed'] for row in selected)
        exact_direction={row['frame'] for row in selected if row['flags15_bit6']==flag and row['ram_equal'] and row['vram_equal'] and any(m['flip_x']==(flag==64) for m in row['render_matches'])}
        verified.update(matches);directions[side].update(exact_direction)
        runs.append({'weapon':entry['weapon'],'name':entry['name'],'direction':side,'evidence':rel(path/'verification.local.json'),'trace':rel(path/'trace.json'),'weapon_selection_verified':True,'selected_body_base_palette_verified':True,'ram_vram_and_screen_frames':sorted(matches),'selected_weapon_direction_screen_frames':sorted(exact_direction)})
special={95,96,97,98,99,103,104,138,139,231,232}
assert special<=directions['left'] and special<=directions['right']
save=ROOT/'work/ver_buki_riko/current_build_saves/20261026T172505420062Z'
save_manifest=read(save/'manifest.local.json')
working=ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/sstates'
for f in save_manifest['files']:
    assert sha(save/f['file'])==sha(working/f['file'])==f['sha256']
idle=ROOT/'work/ver_buki_riko/live_poc/20261026T172519613434Z/verification.local.json'
idle_data=read(idle)
assert idle_data['modified_ram_buffer_matches'] and idle_data['modified_vram_upload_matches'] and idle_data['framebuffer_matches']
summary={'build':rel(BUILD),'bin_sha256':manifest['modified_bin']['sha256'],'checkpoint_method':'asset_refreshed_copy_of_user_F1_then_actual_emulator_F1_F3','original_user_state_unchanged':True,'user_progress_unchanged_by_graphics_refresh':True,'process_memory_written':False,'weapon_tests':runs,'ram_vram_and_screen_frames':sorted(verified),'new_special_frames_both_directions_verified':sorted(special),'current_emulator_F1':rel(save/'manifest.local.json'),'current_F3_idle_verification':rel(idle),'session':'work/ver_buki_riko/emulator_sessions/20261026T170727349064Z','session_paused':True,'pause_capture':'work/ver_buki_riko/emulator_sessions/20261026T170727349064Z/20261026T173614721541Z.png','menu_resume_scan':'0x35','menu_resume_key':'/','runtime_all_base_frames_complete':False,'pending_runtime':['full_arrival_ready_sequence','victory_and_return','ride_chaser','ride_armor','ladder','charged_soul_body_vanish','hover_and_nova_armor_conditions','special_status_hurt_233_236','aiming_laser_enemy_hit','all_body_flash_palettes'],'fresh_boot_demo':'Shibuki visually observed before F3; automated full-bank capture not obtained; not counted as equivalent to checkpoint comparisons','new_art_user_review_pending':True,'preservation':rel(BUILD/'final_preservation.local.json')}
write(BUILD/'runtime_summary.local.json',summary)

pointer={'project':'ver_buki_riko','task':'x_shibuki','stage':'EXPANSION','kind':'shibuki_base_batch_runtime_checked_candidate','build':rel(BUILD),'cue':rel(BUILD/'shibuki_riko.cue'),'bin_sha256':manifest['modified_bin']['sha256'],'source_sha256':manifest['source_sha256'],'riko_accepted_build':'projects/ver_buki_riko/riko_accepted_build.json','riko_preserved_byte_for_byte':True,'parent_accepted_build':'projects/ver_buki_riko/shibuki_low_hp_accepted_build.json','accepted_base_references_preserved':123,'base_sprite_references_applied':228,'base_placeholder_references_preserved':[105,175,176,177,178,179,180,181,182],'base_sprite_art_complete':True,'base_runtime_complete':False,'whole_character_completed':False,'new_animation_user_review_pending':True,'armor_implemented':False,'text_replacement_implemented':False,'art_selection':'projects/ver_buki_riko/shibuki_art_selection.json','active_art_study':'work/ver_buki_riko/shibuki_art/remaining_v1','final_art':'work/ver_buki_riko/shibuki_art/remaining_v1/production14','runtime_summary':rel(BUILD/'runtime_summary.local.json'),'runtime_verified_frames':sorted(verified),'runtime_special_both_directions_frames':sorted(special),'session':summary['session'],'session_closed':False,'session_paused':True,'session_pause_capture':summary['pause_capture'],'session_menu_key':'/','working_save':rel(save/'manifest.local.json'),'user_save_backup':rel(backups/'backup.json'),'report':'docs/SHIBUKI_REMAINING.md','next_group':'review_batch_and_context_specific_runtime','ladder_runtime_deferred':True}
pointer_backup=save/'previous_pointers';pointer_backup.mkdir(exist_ok=True)
for name in ['current_build.json','shibuki_current_build.json']:
    target=ROOT/'projects/ver_buki_riko'/name
    if not (pointer_backup/name).exists(): shutil.copy2(target,pointer_backup/name)
    write(target,pointer)
print(json.dumps({'build':rel(BUILD),'protected_files':len(preserved),'weapon_trials':len(runs),'verified_frames':len(verified),'both_directions_new_frames':len(special),'pointer_updated':True}))
