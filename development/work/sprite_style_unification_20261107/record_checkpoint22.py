import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path('work/sprite_style_unification_20261107')
paths = [
    *[f'zero_audit/rin_extension/prepared_saber_followup04/{f}_readback_00.png' for f in ('normal', 'black')],
    *[f'zero_audit/rin_extension/prepared_saber_followup05_v2/{f}_readback_{p:02d}.png' for f in ('normal', 'black') for p in (0, 1)],
    *[f'nana_audit/ultimate_wall_repaint/costume_pair_probe_v2/comparison_{p}.png' for p in (1, 2)],
    *[f'shibuki_audit/rising_ultimate_native{p:02d}/{f}_comparison.png' for p in (1, 2) for f in ('ultimate_before', 'ultimate_after')],
    *[f'shibuki_audit/rising_ultimate_pack_probe01/{f}_readback_{p:02d}.png' for f in ('before', 'after') for p in (0, 1, 2)],
    'shibuki_audit/rising_base_pack_probe01/fourth_readback_01.png',
    'shibuki_audit/rising103_sleeve_native03/comparison.png',
    *[f'nana_audit/ultimate_wall_repaint/{f}/comparison.png' for f in ('firing_a_before_joint_probe_v2', 'firing_b_before_joint_probe_v4', 'firing_a_after_joint_probe_v5')],
    *[f'zero_audit/rin_extension/prepared_ice01/{f}_readback_{p:02d}.png' for f in ('normal', 'black') for p in (0, 1, 2)],
    'shibuki_audit/rising_base_pack_probe02/fourth_readback_01.png',
]
assert len(paths) == 30
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / p).as_posix(), 'sha256': hashlib.sha256((W / p).read_bytes()).hexdigest(), 'root_actually_viewed': True} for p in paths],
    'findings': {
        'shibuki': 'Ultimate Rising both costumes accepted as candidate after four native and six packed boards. Fourth103 white/red sleeve in base01 rejected; new dark purple sleeve native03 and actual base02 packed comparison accepted. Actual gameplay is still separate.',
        'nana': 'Six wall bare costume bodies and six jacket firing arms plus first three bare firing arms accepted as registration candidates. Shoulder/hand connection and original muzzle preserved. Last three bare arms and final packing pending.',
        'rin': 'Follow-up172 and180 normal/red packed readbacks accepted;180 includes matching derived attack flash silhouette. Ice191 six normal/red boards accepted as candidate, preserving compact crouch and raised-hand contact. Not a full weapon-object runtime test.',
    },
    'actual_gameplay_evidence_separate': 'runtime/nana_checkpoint9_summary.json',
    'all_characters_complete': False, 'user_acceptance': False,
}
(W / 'root_review_checkpoint22.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
