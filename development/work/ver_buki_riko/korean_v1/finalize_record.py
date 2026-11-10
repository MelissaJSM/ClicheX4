"""Record observed Korean localization checks; does not write game/save data."""
import hashlib,json
from pathlib import Path

root=Path(__file__).resolve().parents[3]
base=root/'work/ver_buki_riko/korean_v1'
build=root/'out/ver_buki_riko/korean_20261028T045434647910Z'
proposal=base/'integrated_proposal_v5'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,value):
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def relative(p):return p.relative_to(root).as_posix()

manifest=read(build/'manifest.json')
recipe=read(proposal/'proposal.json')
assert manifest['modified_bin']['sha256']=='2dfc5c4b71dc85e7807f9ab691203cb7a6e130acac4d2d4261423b95bbf5210c'
assert read(base/'final_preservation.json')['all_unchanged']
assert read(base/'input_api_backup.json')['restored']
scope=[
 'title_and_character_selection_full_names',
 'load_menu_left_column_and_right_preview_alignment',
 'memory_card_1_and_2_data_and_confirmation_layout',
 'memory_card_2_data_3_loaded_ultimate_shibuki',
 'shibuki_stage_select_and_ultimate_pause',
 'mission_complete_menu_continue_without_saving',
 'cyber_peacock_intro_name_and_description',
 'korean_loading_stage_label_and_ready',
 'riko_intro_4_pages_natural_transitions_and_stage_entry',
 'shibuki_intro_6_pages_natural_transitions_and_stage_entry',
]
session='work/ver_buki_riko/emulator_sessions/20261028T045544924810Z'
screens={
 'load_data_selection':session+'/20261028T050017871158Z.png',
 'load_confirmation':session+'/20261028T050040936937Z.png',
 'shibuki_stage_select':session+'/20261028T050113303524Z.png',
 'ultimate_pause':session+'/20261028T050153160320Z.png',
 'mission_complete':session+'/20261028T050316983927Z.png',
 'cyber_peacock':session+'/20261028T050410548443Z.png',
 'stage_loading':session+'/20261028T050415276587Z.png',
 'selection_full_names':'work/ver_buki_riko/emulator_sessions/20261028T050430387337Z/20261028T050624708261Z.png',
 'shibuki_full_name_dialogue':'work/ver_buki_riko/emulator_sessions/20261028T050430387337Z/20261028T050817259375Z.png',
 'shibuki_stage_transition':'work/ver_buki_riko/emulator_sessions/20261028T050430387337Z/20261028T050914559481Z.png',
}
for path in screens.values():assert (root/path).is_file(),path
proofs=[
 '20261028T045225237146Z/page_verification_v2.json',
 '20261028T045402596100Z/page_verification_v2.json',
 '20261028T050750754271Z/page_verification.json',
 '20261028T050826816114Z/page_verification.json',
]
proof_paths=['work/ver_buki_riko/korean_runtime/'+p for p in proofs]
for p in proof_paths:assert read(root/p)['captured_page_verified'],p
report={
 'bin_sha256':manifest['modified_bin']['sha256'],
 'build':relative(build),'candidate':relative(proposal),
 'runtime_verified':True,'runtime_verified_scope':scope,
 'full_game_runtime_verified':False,'user_acceptance_of_korean_build':False,
 'natural_dialogue_pages_observed':{'riko':4,'shibuki':6},
 'independent_completed_pages_verified':proof_paths,
 'screenshots':screens,
 'static_checks':{'unit_tests_passed':208,'component_files_reproduced':25,'integrated_resources_read_back':21,'all_raw_sectors_compared':251793,'changed_sectors_edc_ecc_verified':623,'untarget_compositions_preserved':315,'boss_actor_frames_preserved':1226},
 'fixes':['load_menu_native_alignment','riko_text_length_4_byte_alignment'],
 'remaining_runtime_checks':['all_story_branches','all_8_boss_intros','weapon_get_sequences','ending_sequences','all_menu_palette_and_error_states'],
 'out_of_scope':['movie_baked_text_and_voice'],
 'preservation':relative(base/'final_preservation.json'),
 'input_settings_restored':relative(base/'input_api_backup.json'),
 'handoff_session':'work/ver_buki_riko/emulator_sessions/20261028T050933775480Z',
 'handoff_note':'Fresh boot with original input API and isolated card copies; no F1/F3 used. Load the memory card after fresh boot, not an old pre-localization save state.',
 'process_memory_written':False,
}
write(base/'runtime_verification.json',report)
manifest.update(runtime_verified=True,runtime_verified_scope=scope,full_game_runtime_verified=False,runtime_evidence=relative(base/'runtime_verification.json'))
write(build/'manifest.json',manifest)
candidate_path=root/'projects/ver_buki_riko/korean_candidate.json'
candidate=read(candidate_path)
candidate.update(kind='korean_localization_candidate',stage='KOREAN_APPLIED_RUNTIME_REVIEW',proposal=relative(proposal),proposal_sha256=hashlib.sha256((proposal/'proposal.json').read_bytes()).hexdigest(),coverage=recipe['coverage'],runtime_verified=True,runtime_verified_scope=scope,full_game_runtime_verified=False,game_bin_written=True,build=relative(build),bin_sha256=manifest['modified_bin']['sha256'],reproduction=relative(base/'reproduction_v5/verification.json'),runtime_evidence=relative(base/'runtime_verification.json'))
write(candidate_path,candidate)
project_path=root/'projects/ver_buki_riko/project.json'
project=read(project_path)
project.update(active_substage='KOREAN_APPLIED_RUNTIME_REVIEW',latest_integrated_build=relative(build),latest_integrated_bin_sha256=manifest['modified_bin']['sha256'])
project['character_names']['shibuki'].update(selection_display='텐코 시부키',dialogue_display='시부키',dialogue_speaker_display='텐코 시부키')
project['character_names']['riko']={'display':'Riko','full':'Yuzuha Riko','selection_display':'유즈하 리코','dialogue_display':'리코','dialogue_speaker_display':'유즈하 리코','text_replacement_implemented':True}
write(project_path,project)
print(json.dumps({'runtime_scope_count':len(scope),'independent_pages':len(proofs),'build':relative(build),'pointer_updated':True}))
