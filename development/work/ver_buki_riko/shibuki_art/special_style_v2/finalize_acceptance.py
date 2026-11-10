import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[4]
art = Path(__file__).resolve().parent
build = root / 'out/ver_buki_riko/shibuki_special_style_20261026T230854606760Z'
project = root / 'projects/ver_buki_riko'
frames = [88, 89, 90, 91, 97, 98, 99]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()

def rel(path):
    return path.relative_to(root).as_posix()

assert (root / 'AGENTS.md').is_file(), root
manifest = read(build / 'manifest.json')
assert sha(build / 'shibuki_riko.bin') == manifest['modified_bin']['sha256']
checks = []
backup = read(root / 'work/ver_buki_riko/shibuki_all_boss_save/20261026T162502779077Z/backup.json')
for entry in backup:
    for field in ['source', 'backup']:
        path = root / entry[field]
        actual = sha(path)
        checks.append({'path': rel(path), 'sha256': actual, 'matches': actual == entry['sha256']})
for name, expected in [
    ('MegaMan X4.bin', '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),
    ('out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin', '1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'),
]:
    actual = sha(root / name)
    checks.append({'path': name, 'sha256': actual, 'matches': actual == expected})
preservation = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'files': checks, 'all_match': all(x['matches'] for x in checks)}
write(build / 'final_preservation.local.json', preservation)
assert preservation['all_match'], 'Preservation mismatch; do not publish pointer'

provenance = read(art / 'provenance.json')
provenance['final_art'] = 'production06'
provenance['final_frames'] = frames
provenance['final_selected_source'] = 'generated_v1.png'
provenance['discarded_generated_candidate'] = {'image': 'compact97.png', 'prompt': 'compact_prompt.txt', 'used_in_final': False}
for path in sorted((art / 'production06').iterdir()):
    if path.is_file():
        provenance['files'][path.relative_to(art).as_posix()] = sha(path)
for name in ['compact97.png', 'compact_prompt.txt']:
    provenance['files'][name] = sha(art / name)
provenance['accepted_quote'] = '오케이 완벽하게 수정되었네'
provenance['accepted_date_local'] = '2026-10-27'
write(art / 'provenance.json', provenance)

summary = {
    'build': rel(build),
    'bin_sha256': manifest['modified_bin']['sha256'],
    'user_accepted': True,
    'user_quote': '오케이 완벽하게 수정되었네',
    'acceptance_scope': '정지 차지샷88..91·더블 사이클론97..99 디자인 수정',
    'ladder_user_accepted': True,
    'ladder_user_quote': '일단 사다리타기는 훌륭해. 완료처리해줘',
    'automated_runtime_verified_frames': [0],
    'idle_evidence': 'work/ver_buki_riko/live_poc/20261026T230935040085Z/verification.local.json',
    'special_style_automated_both_directions_complete': False,
    'save_kind': 'graphics_refreshed_test_copy; not an emulator F1 save',
    'test_save_refresh': rel(art / 'test_state/refresh.json'),
    'test_save_sha256': sha(art / 'test_state/SLUS_005.61.000'),
    'progress_preserved': read(art / 'test_state/refresh.json'),
    'additional_control_after_acceptance': False,
    'previous_build_runtime_report': 'out/ver_buki_riko/shibuki_weapon_palette_20261026T170706783998Z/runtime_summary.local.json',
    'previous_results_reused_as_new_art_runtime_proof': False,
    'final_preservation': rel(build / 'final_preservation.local.json'),
    'report': 'docs/SHIBUKI_SPECIAL_STYLE.md',
}
write(build / 'runtime_summary.local.json', summary)

pointer_backup = art / ('pointer_backup_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
pointer_backup.mkdir()
for name in ['current_build.json', 'shibuki_current_build.json']:
    shutil.copy2(project / name, pointer_backup / name)
pointer = read(project / 'shibuki_current_build.json')
pointer.update({
    'kind': 'shibuki_special_style_user_accepted',
    'build': rel(build),
    'cue': rel(build / 'shibuki_riko.cue'),
    'bin_sha256': manifest['modified_bin']['sha256'],
    'arc_sha256': sha(build / 'modified.arc'),
    'parent_build': manifest['parent_build'].replace('\\', '/'),
    'parent_bin_sha256': manifest['parent_bin_sha256'],
    'active_art_study': rel(art),
    'final_art': rel(art / 'production06'),
    'inherited_base_art': 'work/ver_buki_riko/shibuki_art/remaining_v1/production14',
    'style_revision_frames': frames,
    'style_revision_user_accepted': True,
    'style_revision_user_quote': summary['user_quote'],
    'style_revision_acceptance_date': '2026-10-27',
    'style_revision_runtime_complete': False,
    'new_animation_user_review_pending': False,
    'new_animation_user_review_scope': frames,
    'other_context_specific_reviews_remaining': True,
    'base_runtime_complete': False,
    'whole_character_completed': False,
    'runtime_summary': rel(build / 'runtime_summary.local.json'),
    'runtime_verified_frames': [0],
    'runtime_special_both_directions_frames': [],
    'inherited_runtime_summary': summary['previous_build_runtime_report'],
    'session': 'work/ver_buki_riko/emulator_sessions/20261026T230926347432Z',
    'session_closed': False,
    'session_paused': None,
    'session_pause_capture': None,
    'working_save': rel(art / 'test_state/refresh.json'),
    'working_save_kind': summary['save_kind'],
    'report': 'docs/SHIBUKI_SPECIAL_STYLE.md',
    'next_group': 'context_specific_runtime_review',
    'final_preservation': rel(build / 'final_preservation.local.json'),
})
for name in ['current_build.json', 'shibuki_current_build.json', 'shibuki_special_style_accepted_build.json']:
    write(project / name, pointer)
print(json.dumps({'preservation_matches': len(checks), 'accepted_build': rel(build), 'pointer_backup': rel(pointer_backup), 'bin_sha256': pointer['bin_sha256']}, ensure_ascii=False))
