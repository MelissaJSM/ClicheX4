"""One-time publication of the tested candidate and its explicitly unresolved review."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from scripts.project import write_json
D=Path(__file__).parent;B=ROOT/'out/ver_buki_riko/riko_bank1_20261024T072210847890Z'
OLD=ROOT/'out/ver_buki_riko/riko_motion_20261024T063713991893Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T072313834739Z'
SPLIT=ROOT/'work/ver_buki_riko/master_split/20261024T072335721177Z/validation.local.json'
def rel(p):return p.relative_to(ROOT).as_posix()
manifest=json.loads((B/'manifest.json').read_text());split=json.loads(SPLIT.read_text())
assert split['archive_byte_identical'] and len(split['png_byte_identical_frames'])==156
assert sha256((B/'riko_motion.bin').read_bytes())==manifest['modified_bin']['sha256']
old=json.loads((OLD/'manifest.json').read_text());unchanged=[]
for n in old['frame_inputs']:
 filename=f'idle_{int(n):03d}.png' if int(n) in (0,1,2,146,147,148) else f'frame_{int(n):03d}.png'
 assert (B/filename).read_bytes()==(OLD/filename).read_bytes();unchanged.append(int(n))
V=B/('wall_saber_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));V.mkdir()
for path in ['projects/ver_buki_riko/current_build.json','projects/ver_buki_riko/art_selection.json','projects/ver_buki_riko/master_sheet.json','docs/STATUS.md']:
 p=ROOT/path;shutil.copyfile(p,V/('previous_'+p.name))
for name in ['recipe.json','original_roundtrip.json','guard_checks.json','packing_checks.json','art_checks.json','grip_checks.json','missing_frame_audit.json','unit_tests.log','generation_prompt.txt','revision_prompt.txt','body_review.png','effect_review.png','wall_transition_comparison.png','low_hp_original_review.png','wall_saber_offline.gif']:
 shutil.copyfile(D/name,V/name)
summary={'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'body_references':156,'preserved_effect_references':63,
 'unchanged_previous_pngs':sorted(unchanged),'original_roundtrip_byte_identical':True,'master':rel(M),'master_roundtrip':rel(SPLIT),
 'unit_tests_passed':73,'guard_cases_rejected':9,'new_body_scope':{'bank':1,'frames':[50,51,53,54,56,57,59,61,63,65]},
 'runtime_build':'out/ver_buki_riko/riko_bank1_20261024T070810249163Z','runtime_bin_byte_identical_to_candidate':True,
 'runtime':'work/ver_buki_riko/wall_saber_runtime/20261024T071550227238Z/verification.local.json',
 'ram_vram_verified_bank1':[50,51,54,56,57,59,61],'full_framebuffer_verified_bank1':[],
 'unobserved_bank1':[53,63,65],'original_low_hp_frames_remaining':[149,150,151,152,153,154],
 'low_hp_frames_observed':[149,151],'user_flagged_wall_transition_quality':True,
 'style_review_pending':True,'whole_character_completed':False,'process_memory_written':False,
 'agent_loaded_save_state':False,'boot_selection_path_continuously_observed':False}
write_json(V/'runtime_summary.json',summary)
pointer=json.loads((ROOT/'projects/ver_buki_riko/current_build.json').read_text())
pointer.update(kind='riko_wall_saber_candidate_needs_transition_revision',build=rel(B),cue=rel(B/'riko_motion.cue'),
 bin_sha256=manifest['modified_bin']['sha256'],previous_build=rel(OLD),previous_bin_sha256=old['modified_bin']['sha256'],
 previous_pointer_snapshot=rel(V/'previous_current_build.json'),runtime_summary=rel(V/'runtime_summary.json'),
 runtime_verified_frames=[],inherited_bank0_runtime_source='docs/RIKO_LADDER.md',
 session='work/ver_buki_riko/emulator_sessions/20261024T071038950106Z',session_closed=False,
 riko_reference_count=156,original_saber_effect_references_preserved=63,bank1_set=rel(D/'recipe.json'),
 all_current_frames_preview=rel(M/'riko_master_preview_2x.png'),wall_saber_bank1_implemented=True,
 bank1_ram_vram_verified_frames=summary['ram_vram_verified_bank1'],bank1_full_framebuffer_verified_frames=[],
 user_flagged_wall_transition_quality=True,low_hp_idle_original_frames=[149,150,151,152,153,154],
 next_task='Revise wall cling/saber anatomical continuity; produce low-HP idle149..154 before special-technique expansion',
 report='docs/RIKO_WALL_SABER.md',session_state_at_last_observation='Paused Zero menu; PID17864; session CUE is an earlier byte-identical BIN',
 session_state_evidence='work/ver_buki_riko/emulator_sessions/20261024T071038950106Z/20261024T072213843495Z.png')
(ROOT/'projects/ver_buki_riko/current_build.json').write_text(json.dumps(pointer,ensure_ascii=False,indent=2)+'\n','utf8')
master={'project':'ver_buki_riko','task':'zero_riko','kind':'editable_master_sheet','source_build':rel(B),
 'source_bin_sha256':manifest['modified_bin']['sha256'],'directory':rel(M),'master':rel(M/'master.local.json'),
 'sheet':rel(M/'riko_master_indexed.png'),'preview':rel(M/'riko_master_preview_2x.png'),'roundtrip':rel(SPLIT),
 'guard_checks':rel(V/'guard_checks.json'),'riko_references':156,'whole_character_completed':False,
 'wall_saber_art_review_pending':True,'low_hp_idle_frames_missing':[149,150,151,152,153,154],
 'next_group':'wall_transition_and_low_hp_idle','report':'docs/RIKO_WALL_SABER.md'}
(ROOT/'projects/ver_buki_riko/master_sheet.json').write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n','utf8')
selection=json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text())
selection.update(latest_candidate_build=rel(B),wall_saber_art_directory=rel(D),wall_saber_style_user_review_pending=True,
 wall_saber_runtime_summary=rel(V/'runtime_summary.json'),wall_saber_transition_user_flagged=True)
selection['runtime_limitations']['wall_saber_full_render_unverified']=[50,51,53,54,56,57,59,61,63,65]
selection['runtime_limitations']['low_hp_idle_original_remaining']=[149,150,151,152,153,154]
(ROOT/'projects/ver_buki_riko/art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n','utf8')
write_json(D/'publication.json',{'build':rel(B),'validation':rel(V),'master':rel(M),'split':rel(SPLIT)})
print(json.dumps({'validation':rel(V),'body':156,'previous_pngs_unchanged':len(unchanged)}))
