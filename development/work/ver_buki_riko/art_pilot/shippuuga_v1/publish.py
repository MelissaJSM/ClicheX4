"""Record the accepted Shippuuga build without touching game inputs."""
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parents[4]
D = Path(__file__).parent
def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf8'))
def write(p, value):
    (ROOT / p).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()

B = 'out/ver_buki_riko/riko_bank1_20261025T134737617192Z'
M = 'work/ver_buki_riko/production_master/20261025T134829511811Z'
S = 'work/ver_buki_riko/emulator_sessions/20261025T134831800288Z'
C = 'work/ver_buki_riko/current_build_saves/20261025T135448033161Z'
split = 'work/ver_buki_riko/master_split/20261025T134905614200Z/validation.local.json'
sha = read(B + '/manifest.json')['modified_bin']['sha256']
assert sha == '3677819b8ccc524ef87d0ce78c67d14d52d744b26d8f65a6c3f87154d98e341d'
assert read(split)['archive_byte_identical']
assert len(read(split)['png_byte_identical_frames']) == 250
checkpoint = read(C + '/manifest.local.json')
assert checkpoint['bin_sha256'] == sha
assert checkpoint['full_current_bank0_equal'] and checkpoint['full_current_bank1_present']
assert read(rel(D / 'live_static.local.json'))['full_static_texture_equal']
backup = D / 'publication_backup'
backup.mkdir(exist_ok=True)
for path in ['projects/ver_buki_riko/current_build.json', 'projects/ver_buki_riko/master_sheet.json', 'docs/STATUS.md']:
    target = backup / Path(path).name
    if not target.exists():
        shutil.copyfile(ROOT / path, target)
current = read('projects/ver_buki_riko/current_build.json')
previous = read(rel(backup / 'current_build.json'))
runtime = {
    'build': B, 'bin_sha256': sha, 'session': S,
    'user_playtest_accepted': True,
    'user_quote': '내가해보니까 잘나왔어. 이제 남은게 그러면... 레디 하고 내려올때 포즈랑 승리포즈 돌아갈때 포즈 정도인가?',
    'automatic_body_frame_verification_complete': False,
    'automatic_ram_vram_frame_verified': [],
    'automatic_full_framebuffer_verified': [],
    'automatic_attempt': 'work/ver_buki_riko/dashslash_runtime/20261025T135006748665Z/verification.local.json',
    'attempt_limitation': 'Focus guard stopped input; no animation104 captured. User subsequently played and accepted.',
    'full_banks_in_new_f1': C + '/manifest.local.json',
    'full_static_texture_live': rel(D / 'live_static.local.json'),
    'f3_on_this_build_tested': False,
    'original_user_save_preserved': True,
    'whole_character_completed': False
}
write(rel(D / 'runtime_summary.json'), runtime)
current.update({
    'kind': 'riko_shippuuga_v1', 'build': B, 'cue': B + '/riko_motion.cue', 'bin_sha256': sha,
    'previous_build': previous['build'], 'previous_bin_sha256': previous['bin_sha256'],
    'previous_pointer_snapshot': rel(backup / 'current_build.json'),
    'session': S, 'session_closed': False, 'runtime_summary': rel(D / 'runtime_summary.json'),
    'runtime_verified_frames': [], 'runtime_verification_scope': 'Shippuuga current group; user playtest accepted, automatic per-frame check incomplete',
    'riko_reference_count': 250, 'original_saber_effect_references_preserved': 109,
    'existing_340_pngs_preserved': True, 'motion_set': rel(D / 'motion_set.json'),
    'all_current_frames_preview': M + '/riko_master_preview_2x.png',
    'next_task': 'Beam-in and landing, victory and beam-out, then ride chaser and ride armor player sprites',
    'report': 'docs/RIKO_SHIPPUUGA.md', 'remaining_report': 'docs/RIKO_REMAINING.md',
    'session_state_at_last_observation': 'Spaceport Zero bossFF HP48 energy48 x409.25 y2234; idle, new F1 bank data checked; F3 not tested',
    'session_state_evidence': C + '/manifest.local.json',
    'current_build_save': C, 'save_roundtrip': None,
    'current_save_validation': C + '/manifest.local.json',
    'current_static_texture_validation': rel(D / 'live_static.local.json'),
    'shippuuga_user_playtest_accepted': True, 'shippuuga_art_user_review_pending': False,
    'shippuuga_ram_vram_verified_frames': [], 'shippuuga_full_framebuffer_verified_frames': [],
    'whole_character_completed': False
})
write('projects/ver_buki_riko/current_build.json', current)
master = read('projects/ver_buki_riko/master_sheet.json')
master.update({
    'source_build': B, 'source_bin_sha256': sha, 'directory': M,
    'master': M + '/master.local.json', 'sheet': M + '/riko_master_indexed.png',
    'preview': M + '/riko_master_preview_2x.png', 'roundtrip': split,
    'riko_references': 250, 'preserved_effect_references': 109,
    'static_effects': M + '/static_effects.local.json',
    'next_group': 'beam_in_victory_beam_out', 'report': 'docs/RIKO_SHIPPUUGA.md',
    'remaining_report': 'docs/RIKO_REMAINING.md', 'shippuuga_art_review_pending': False,
    'whole_character_completed': False
})
write('projects/ver_buki_riko/master_sheet.json', master)
rai = 'work/ver_buki_riko/art_pilot/raijingeki_v1/runtime_summary.json'
r = read(rai)
r['user_quote'] = '일단 내가보기에는 충분히 잘나왔어 다음으로넘어가도좋다고봐'
write(rai, r)
inv = read('work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json')
groups = {'beam_in': [1, 2], 'victory_beam_out': [3, 4, 39, 40],
          'ride_armor': list(range(41, 65)), 'ride_chaser': list(range(65, 81)),
          'reused_hurt_for_death_stun': [33, 36, 37]}
audit = {'source_build': B, 'source_sha256': inv['source_sha256'],
         'source_inventory': 'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json',
         'classification': 'Local static mapping and original pixel inspection, not live verification', 'groups': {}}
for name, ids in groups.items():
    entries = [a for a in inv['animations'] if a['id'] in ids]
    refs = sorted({(a['graphics_bank'], s['frame']) for a in entries for s in a['sequence']})
    audit['groups'][name] = {'animation_ids': ids, 'references': refs, 'includes_effect_or_flash': name in ('beam_in', 'victory_beam_out')}
write(rel(D / 'remaining_audit.json'), audit)
print(json.dumps({'build': B, 'body_references': 250, 'effect_references': 109, 'accepted': True}))
