"""Update local project pointers only, retaining previous pointers and evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def rel(p):return Path(p).resolve().relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n','utf8')
def run():
 if (D/'publication.json').exists():raise ValueError('Already published; preserve previous snapshots')
 build=Path(read(D/'builds.json')['build']['output']);manifest=read(build/'manifest.json')
 master=Path(read(D/'master_export.json')['output']);split=Path(read(D/'master_split.json')['output'])
 if not read(split/'validation.local.json')['archive_byte_identical']:raise ValueError('Master roundtrip missing')
 if not read(D/'verify_result.json')['reproducible']:raise ValueError('Repeated build differs')
 if len(read(D/'preservation_audit.json')['previous_pngs_preserved'])!=225:raise ValueError('Previous art changed')
 v=build/('hurt_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));v.mkdir()
 for name in ('current_build.json','master_sheet.json','art_selection.json'):
  shutil.copyfile(ROOT/'projects/ver_buki_riko'/name,v/('previous_'+name))
 shutil.copyfile(ROOT/'docs/STATUS.md',v/'previous_STATUS.md')
 for name in ('runtime_summary.json','input_audit.json','preservation_audit.json','packing_checks.json','art_checks.json',
              'screen_negative_controls.json','unit_tests_final.log','generation_prompt.txt','compact_edit_prompt.txt',
              'body_review.png','actual_hurt_verified.png','hurt_transition_offline.gif'):
  shutil.copyfile(D/name,v/name)
 previous=read(ROOT/'projects/ver_buki_riko/current_build.json');current=dict(previous)
 current.update(kind='riko_basic_hurt_and_flash_revision',build=rel(build),cue=rel(build/'riko_motion.cue'),
  bin_sha256=manifest['modified_bin']['sha256'],previous_build=previous['build'],previous_bin_sha256=previous['bin_sha256'],
  previous_pointer_snapshot=rel(v/'previous_current_build.json'),previous_runtime_summary=previous['runtime_summary'],
  session='work/ver_buki_riko/emulator_sessions/20261024T082751880685Z',session_closed=False,
  session_state_at_last_observation='Paused Zero menu; HP5, remaining lives1 after ordinary-input tests',
  session_state_evidence='work/ver_buki_riko/emulator_sessions/20261024T082751880685Z/20261024T083803613602Z.png',
  runtime_summary=rel(v/'runtime_summary.json'),runtime_verified_frames=[135,136,137,138,147],
  riko_reference_count=166,existing_225_pngs_preserved=True,motion_set=rel(D/'motion_set.json'),
  all_current_frames_preview=rel(master/'riko_master_preview_2x.png'),hurt_frames=[135,136,137,138],
  hurt_right_full_render_verified=[135,136,137,138],hurt_left_full_render_separate_time_verified=[135],
  hurt_left_full_render_unverified=[136,137,138],hurt_style_user_review_pending=True,
  unchanged_previous_runtime_evidence_inherited=previous['runtime_summary'],
  next_task='Complete left hurt screen comparison; investigate CLUT2 strong knockback139..145; continue ladder and wall runtime gaps',
  report='docs/RIKO_HURT.md')
 write(ROOT/'projects/ver_buki_riko/current_build.json',current)
 m=read(ROOT/'projects/ver_buki_riko/master_sheet.json')
 m.update(source_build=rel(build),source_bin_sha256=manifest['modified_bin']['sha256'],directory=rel(master),
  master=rel(master/'master.local.json'),sheet=rel(master/'riko_master_indexed.png'),preview=rel(master/'riko_master_preview_2x.png'),
  roundtrip=rel(split/'validation.local.json'),riko_references=166,hurt_guard_checks=rel(v/'input_audit.json'),
  hurt_art_review_pending=True,next_group='strong_knockback_clut2_and_remaining_runtime',report='docs/RIKO_HURT.md')
 write(ROOT/'projects/ver_buki_riko/master_sheet.json',m)
 a=read(ROOT/'projects/ver_buki_riko/art_selection.json')
 a.update(status='accepted_design_basis_with_hurt_candidate_review_pending',
  game_applied_scope='166 body/flash references and63 original saber effects; new hurt4 right rendered, left4 loaded/one separate-time rendered',
  latest_candidate_build=rel(build),latest_candidate_bin_sha256=manifest['modified_bin']['sha256'],
  hurt_art_directory=rel(D),hurt_style_user_review_pending=True,hurt_runtime_summary=rel(v/'runtime_summary.json'))
 a['runtime_limitations']['hurt_left_full_render_unverified']=[136,137,138]
 a['runtime_limitations']['strong_knockback_original_frames_remaining']=list(range(139,146))
 write(ROOT/'projects/ver_buki_riko/art_selection.json',a)
 write(D/'publication.json',{'build':rel(build),'validation':rel(v),'master':rel(master),'split':rel(split)})
 print(json.dumps(read(D/'publication.json')))
if __name__=='__main__':run()
