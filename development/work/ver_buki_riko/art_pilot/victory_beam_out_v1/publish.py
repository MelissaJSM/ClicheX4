"""Publish the graphics candidate; runtime victory review is assigned to the user."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def read(p):return json.loads((ROOT/p).read_text('utf8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n','utf8')
def rel(p):return Path(p).resolve().relative_to(ROOT).as_posix()
B='out/ver_buki_riko/riko_bank1_20261025T174124184782Z';M='work/ver_buki_riko/production_master/20261025T174229467826Z';S='work/ver_buki_riko/emulator_sessions/20261025T174250045099Z';split='work/ver_buki_riko/master_split/20261025T174253128407Z/validation.local.json'
manifest=read(B+'/manifest.json');sha=manifest['modified_bin']['sha256']
assert sha=='b6544c4ee1c6f54ae67bf19c800fe2bd769ba74126d53ee375017449f52e387e'
assert hashlib.sha256((D/'recipe.json').read_bytes()).hexdigest()==manifest['bank1_set_sha256']
assert read(split)['archive_byte_identical'] and len(read(split)['png_byte_identical_frames'])==266
assert read(rel(D/'preservation_audit.json'))['previous_png_count']==366
backup=D/'publication_backup';backup.mkdir(exist_ok=True)
for p in ('projects/ver_buki_riko/current_build.json','projects/ver_buki_riko/master_sheet.json','docs/STATUS.md'):
    if not (backup/Path(p).name).exists():shutil.copyfile(ROOT/p,backup/Path(p).name)
previous=read(rel(backup/'current_build.json'));current=read('projects/ver_buki_riko/current_build.json')
runtime={'build':B,'bin_sha256':sha,'session':S,'launched_from_disc':True,'save_state_loaded_by_agent':False,'new_f1_created':False,'agent_victory_runtime_verified':False,'user_review_pending':True,'user_assigned_runtime_check':True,'user_quote':'이번 테스트는  처음부터 플레이를해서 승리포즈 체크해야하니까 내가 체크를해볼게','verified_victory_frames':[],'whole_character_completed':False}
write(rel(D/'runtime_summary.json'),runtime)
current.update(kind='riko_victory_beam_out_v1',build=B,cue=B+'/riko_motion.cue',bin_sha256=sha,previous_build=previous['build'],previous_bin_sha256=previous['bin_sha256'],previous_pointer_snapshot=rel(backup/'current_build.json'),session=S,session_closed=False,runtime_summary=rel(D/'runtime_summary.json'),runtime_verified_frames=[],runtime_verification_scope='Victory and beam-out: static checks completed, live review assigned to user',riko_reference_count=266,original_saber_effect_references_preserved=114,existing_366_pngs_preserved=True,bank1_set=rel(D/'recipe.json'),all_current_frames_preview=M+'/riko_master_preview_2x.png',report='docs/RIKO_VICTORY_BEAM_OUT.md',next_task='User victory/departure playtest; ride chaser and ride armor player sprites next',session_state_at_last_observation='New disc launched; user will play from start; no further agent input',session_state_evidence=rel(D/'runtime_summary.json'),current_build_save=None,current_save_validation=None,current_static_texture_validation=None,victory_art_user_review_pending=True,victory_user_playtest_accepted=False,victory_ram_vram_verified_frames=[],victory_full_framebuffer_verified_frames=[],new_build_save_required=True)
write('projects/ver_buki_riko/current_build.json',current)
master=read('projects/ver_buki_riko/master_sheet.json');master.update(source_build=B,source_bin_sha256=sha,directory=M,master=M+'/master.local.json',sheet=M+'/riko_master_indexed.png',preview=M+'/riko_master_preview_2x.png',roundtrip=split,riko_references=266,preserved_effect_references=114,static_effects=M+'/static_effects.local.json',next_group='ride_chaser_and_ride_armor',report='docs/RIKO_VICTORY_BEAM_OUT.md',victory_art_review_pending=True)
write('projects/ver_buki_riko/master_sheet.json',master)
print(json.dumps({'build':B,'body':266,'preserved_effects':114,'runtime_review':'user'}))
