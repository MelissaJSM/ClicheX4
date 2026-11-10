"""완료된 검사 파일을 검증하고 통합 후보/출처/실행 범위를 기록한다."""
import json, sys, platform
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.project import digest

def write_json(path, data):
    assert path.resolve().is_relative_to(ROOT)
    assert path.suffix == '.json'
    if path.exists() and path.name in {'shibuki_fourth_candidate.json','project.json','session.local.json'}:
        backup = Path(__file__).parent/('before_full_' + path.name)
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

build = ROOT/'out/ver_buki_riko/shibuki_fourth_remaining_20261027T014647676089Z'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def rel(path):
    return path.resolve().relative_to(ROOT).as_posix()
manifest = read(build/'manifest.json')
assert digest(build/'shibuki_riko.bin') == manifest['modified_bin']['sha256']
assert digest(build/'modified.arc') == manifest['modified_archive_sha256']
review = read(build/'armor_full_review/verification.json')
assert review['combinations_checked'] == 7296 and review['all_layers_equal']
repeat = ROOT/'work/ver_buki_riko/shibuki_fourth_remaining/20261027T014720828639Z/modified.arc'
assert repeat.read_bytes() == (build/'modified.arc').read_bytes()
write_json(build/'determinism.json', {'repeat_arc': rel(repeat), 'sha256': digest(repeat), 'byte_identical': True})
checks_path = ROOT/'work/ver_buki_riko/shibuki_armor_input_checks/20261027T015041958826Z/checks.json'
checks = read(checks_path)
for row in checks['preserved_inputs']:
    assert digest(ROOT/row['path']) == row['sha256'], row['path']
write_json(build/'preservation.json', {'source_checks': rel(checks_path), 'rechecked_after_runtime': True, 'inputs': checks['preserved_inputs']})
tags = ['20261027T014858298774Z', '20261027T014938107274Z', '20261027T015501206442Z', '20261027T020718521174Z']
full, armor, records, evidence = set(), set(), [], []
for tag in tags:
    path = ROOT/'work/ver_buki_riko/shibuki_armor_capture'/tag/'verification.local.json'
    data = read(path)
    assert data['modified_bin_sha256'] == manifest['modified_bin']['sha256']
    assert all(all(r['complete_entries_match'].values()) for r in data['checked_ram_entries'])
    full.update(data['verified_frames']); armor.update(data.get('verified_armor_only_frames', []))
    evidence.append({'path': rel(path), 'sha256': digest(path)})
    for row in data['results']:
        if row['matches']:
            assert row['ram_equal'] and row['vram_equal']
            records.append({k: row[k] for k in ['frame','armor','arm_type','direction_bit','weapon']})
assert len(full) == 46
runtime = {'evidence': evidence, 'verified_full_sprite_frames': sorted(full), 'verified_armor_only_frames': sorted(armor), 'verified_conditions': records, 'all_gameplay_situations_verified': False, 'fresh_disc_memory_card_load_verified': False, 'checkpoint_kind': 'asset-refreshed actual full-armor idle checkpoint', 'checkpoint': 'work/ver_buki_riko/shibuki_art/fourth_armor_remaining_v1/test_state/SLUS_005.61.000', 'checkpoint_sha256': '82eeb0ba1e850905c610b83f4e04d7a7a9a0491bbf173660817d937b2a909e46', 'session': 'work/ver_buki_riko/emulator_sessions/20261027T015551432642Z', 'fresh_boot_attempt': 'title and attract mode observed; memory-card menu load not established; then F3 loaded verified test checkpoint', 'process_memory_written': False}
assert digest(ROOT/runtime['checkpoint']) == runtime['checkpoint_sha256']
write_json(build/'runtime_summary.local.json', runtime)
artroot = ROOT/'work/ver_buki_riko/shibuki_art'
provenances = []
for folder, files in [('fourth_armor_motion_v1', ['run_generated.png','run_prompt.txt','run_pose_reference.png','normalize_run.py','register_layers.py','layers06/layers.json']), ('fourth_armor_remaining_v1', ['air_dash_generated.png','action_generated.png','back_other_generated.png','air_dash_prompt.txt','action_prompt.txt','back_other_prompt.txt','generation_sources.json','master_groups.json','register_remaining.py','layers06/layers.json'])]:
    directory = artroot/folder
    provenance = {'mode':'built-in image_gen', 'final_layers':'layers06', 'postprocess':'RGB555 palette registration onto accepted base body and original armor part allocation', 'files': [{'path': rel(directory/f), 'sha256': digest(directory/f)} for f in files], 'source_design_accepted':True, 'all_new_poses_user_accepted':False}
    write_json(directory/'provenance.json', provenance)
    provenances.append(rel(directory/'provenance.json'))
report = {'date':'2026-10-27', 'task':'fourth_armor_shibuki', 'graphics_integrated_for_available_armor_references':True, 'art_production_scope_complete':True, 'reference_scope':manifest['armor_frames_cumulative'], 'reference_count':len(manifest['armor_frames_cumulative']), 'valid_references_audited_including_blank_198':228, 'static_combinations_verified':7296, 'placeholders_preserved':[105,*range(175,183)], 'original_transparent_armor_frames_preserved':review['original_transparent_armor_frames'], 'original_transparent_character_poses_use_accepted_base_outfit':[133,134,135,136,137,158], 'all_runtime_verified':False, 'full_sprite_runtime_frame_count':len(full), 'unit_tests_passed':188, 'negative_checks':checks['negative_checks'], 'provenance':provenances, 'runtime_evidence':'runtime_summary.local.json', 'build_time_manifest_status_superseded_by_this_report':True, 'current_session_loaded_by_F3':True, 'python':platform.python_version()}
write_json(build/'integration_report.json', report)
candidate = {'project':'ver_buki_riko','task':'fourth_armor_shibuki','stage':'EXPANSION','kind':'fourth_armor_full_graphics_candidate','build':rel(build),'cue':rel(build/'shibuki_riko.cue'),'bin_sha256':manifest['modified_bin']['sha256'],'arc_sha256':manifest['modified_archive_sha256'],'source_sha256':manifest['source_sha256'],'accepted_base_build':'out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z','graphics_scope_complete':True,'full_animation_runtime_complete':False,'art_user_accepted':True,'art_acceptance_scope':'망토 대기 시안의 스타일 기준; 새 전체 자세는 사용자 최종 검토 전','production_authorized':True,'approval_date':'2026-10-27','explicit_style_approval':'일단 디자인은 되게 마음에 들어 이걸로 작업 계속해나가면될듯한데','user_quote':'좋아 잘만들어지고있는거같으니 계속 진행하자. 그냥 스프라이트 전체를 한번에 완성해도될정도로 잘나오고있어','source_art':['work/ver_buki_riko/shibuki_art/fourth_armor_v1/layers03','work/ver_buki_riko/shibuki_art/fourth_armor_motion_v1/layers06','work/ver_buki_riko/shibuki_art/fourth_armor_remaining_v1/layers06'],'review':rel(build/'armor_full_review/representative_poses.png'),'integration_report':rel(build/'integration_report.json'),'runtime_evidence':rel(build/'runtime_summary.local.json'),'scope':manifest['armor_frames_cumulative'],'static_combinations_verified':7296,'original_transparent_armor_frames':review['original_transparent_armor_frames'],'report':'docs/SHIBUKI_ARMOR_PRODUCTION_WORK.md','save_runtime_load_verified':False,'test_checkpoint':runtime['checkpoint'],'next':'전체 자세의 사용자 플레이 검토 및 팔 종류1·부분 장착·특수무기 상황별 실행 확인'}
write_json(ROOT/'projects/ver_buki_riko/shibuki_fourth_candidate.json', candidate)
projectpath = ROOT/'projects/ver_buki_riko/project.json'
project = read(projectpath);project['active_substage']='ARMOR_FULL_BUILD_REVIEW';write_json(projectpath,project)
sessionpath = ROOT/runtime['session']/'session.local.json'
session = read(sessionpath);session.update(save_state_loaded=True, loaded_checkpoint=runtime['checkpoint'], loaded_checkpoint_sha256=runtime['checkpoint_sha256'], original_memory_card_load_verified=False);write_json(sessionpath,session)
print(json.dumps({'build':rel(build),'runtime_full_frames':len(full),'armor_only_frames':sorted(armor),'protected_inputs':len(checks['preserved_inputs']),'candidate_updated':True}))
