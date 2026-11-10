"""Publish the audited ladder candidate; keep prior pointers as immutable snapshots."""
from pathlib import Path
import sys,json,shutil,subprocess,platform
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import LADDER_BODY_FRAMES
D=Path(__file__).parent
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T063713991893Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T063755664713Z'
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T063759786740Z'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 project=ROOT/'projects/ver_buki_riko';old=read(project/'current_build.json')
 if old['bin_sha256']!='1393419d99e391440370fcc700f7aa68064b85414f6c8c773934cee3bdf07c26':raise ValueError('Current pointer changed; inspect before publishing')
 manifest=read(B/'manifest.json');guards=read(D/'guard_checks.json');jump=read(ROOT/'work/ver_buki_riko/jump_runtime/20261024T064133254430Z/verification.local.json')
 assert guards['bin_sha256']==jump['modified_bin_sha256']==manifest['modified_bin']['sha256']
 assert sha256((B/'riko_motion.bin').read_bytes())==manifest['modified_bin']['sha256']
 assert read(ROOT/'work/ver_buki_riko/master_split/20261024T063843348050Z/validation.local.json')['archive_byte_identical']
 V=B/('ladder_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));V.mkdir()
 for name in ('current_build.json','art_selection.json','master_sheet.json'):shutil.copyfile(project/name,V/('previous_'+name))
 shutil.copyfile(ROOT/'docs/STATUS.md',V/'previous_STATUS.md')
 for name in ('recipe.json','guard_checks.json','art_checks.json','packing_checks.json','grip_registration.json','reference_roles.json','generation_prompt.txt','all_body_review.png','climb_offline.gif','exit_offline.gif','slash_offline.gif'):shutil.copyfile(D/name,V/name)
 result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,capture_output=True,text=True)
 (V/'unit_tests.log').write_text(result.stdout+result.stderr,encoding='utf8')
 if result.returncode:raise RuntimeError('Unit tests failed; pointers not changed')
 summary={'source_build':rel(B),'modified_bin_sha256':manifest['modified_bin']['sha256'],'session':rel(S),
  'current_runtime_baseline':'work/ver_buki_riko/live_poc/20261024T064118048755Z/verification.local.json',
  'jump_runtime':'work/ver_buki_riko/jump_runtime/20261024T064133254430Z/verification.local.json',
  'verified_current_frames':jump['verified_frames'],'jump32_current_unobserved':True,
  'new_ladder_body_frames':sorted(LADDER_BODY_FRAMES),'new_ladder_runtime_verified':False,
  'prior_unchanged_evidence':old['runtime_summary'],'prior_evidence_inheritance_requires_identical_pngs':guards['previous_pngs_identical'],
  'character':1,'game_memory_written':False,'agent_save_state_loaded':False,'full_boot_navigation_observed':False,
  'new_art_user_review_pending':True,'known_limitations':['New ladder poses only statically checked','Weapon object offsets and timing need ladder gameplay','Wall saber bank1 not implemented'],
  'python_version':platform.python_version(),'code_sha256':{n:sha256((ROOT/n).read_bytes()) for n in ('src/psx_frame_edit.py','scripts/build_riko_idle.py','scripts/prepare_riko_scale.py','scripts/riko_master_sheet.py')}}
 write(V/'runtime_summary.json',summary)
 current={'project':'ver_buki_riko','task':'zero_riko','stage':'ZERO_PRODUCTION','kind':'riko_ladder_static_candidate',
  'build':rel(B),'cue':rel(B/'riko_motion.cue'),'bin_sha256':manifest['modified_bin']['sha256'],'source_sha256':manifest['source_sha256'],
  'previous_build':old['build'],'previous_bin_sha256':old['bin_sha256'],'previous_pointer_snapshot':rel(V/'previous_current_build.json'),
  'session':rel(S),'session_closed':False,'runtime_summary':rel(V/'runtime_summary.json'),'runtime_verified_frames':jump['verified_frames'],
  'riko_reference_count':146,'original_saber_effect_references_preserved':57,'existing_114_body_pngs_preserved':True,
  'motion_set':'work/ver_buki_riko/scale_frames/20261024T063636725634Z/motion_set.json','idle_frames':old['idle_frames'],'idle_revision':old['idle_revision'],
  'production_master':'projects/ver_buki_riko/master_sheet.json','all_current_frames_preview':rel(M/'riko_master_preview_2x.png'),
  'sword_art_user_review_pending':False,'sword_design_acceptance_record':'docs/DECISIONS.md',
  'ladder_art':rel(D),'ladder_style_user_review_pending':True,'ladder_runtime_verified':False,'wall_saber_bank1_implemented':False,
  'next_task':'Reach a ladder through ordinary gameplay; verify climb, both slash directions, recovery and exits; then bank1 wall saber',
  'report':'docs/RIKO_LADDER.md','agent_loaded_save_state':False,'whole_character_completed':False}
 write(project/'current_build.json',current)
 master={'project':'ver_buki_riko','task':'zero_riko','kind':'editable_master_sheet','source_build':rel(B),'source_bin_sha256':manifest['modified_bin']['sha256'],
  'directory':rel(M),'master':rel(M/'master.local.json'),'sheet':rel(M/'riko_master_indexed.png'),'preview':rel(M/'riko_master_preview_2x.png'),
  'roundtrip':'work/ver_buki_riko/master_split/20261024T063843348050Z/validation.local.json','guard_checks':rel(V/'guard_checks.json'),
  'riko_references':146,'whole_character_completed':False,'ladder_art_review_pending':True,'ladder_runtime_verified':False,
  'next_group':'ladder_runtime_then_bank1_wall_saber','report':'docs/RIKO_LADDER.md'}
 write(project/'master_sheet.json',master)
 art=read(project/'art_selection.json');art.update({'status':'short_grip_accepted_ladder_candidate_review_pending','sword_style_user_review_pending':False,
  'sword_acceptance':{'date':'2026-10-24','build_sha256':old['bin_sha256'],'user_instruction':'좋아 이대로 계속 작업부탁할게','scope':'Short grip design accepted as basis; remaining technical gaps not waived'},
  'runtime_verified_build':rel(B),'runtime_evidence':'docs/RIKO_LADDER.md','runtime_summary':rel(V/'runtime_summary.json'),
  'runtime_verified_frame_scope':jump['verified_frames'],'game_applied_scope':'146 body references in BIN; current16 existing poses checked; new32 ladder poses not runtime verified',
  'ladder_art_directory':rel(D),'ladder_style_user_review_pending':True,'ladder_runtime_verified':False,'ladder_body_references':32,
  'historical_selection_snapshot':rel(V/'previous_art_selection.json')})
 art['runtime_limitations']['new_ladder_runtime_unverified']=sorted(LADDER_BODY_FRAMES)
 write(project/'art_selection.json',art)
 write(D/'publication.json',{'build':rel(B),'validation':rel(V),'master':rel(M),'session':rel(S)})
 print(json.dumps({'validation':rel(V),'published_build':rel(B),'tests_passed':True}))
if __name__=='__main__':main()
