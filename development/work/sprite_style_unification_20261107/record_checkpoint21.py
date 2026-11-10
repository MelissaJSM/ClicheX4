import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path('work/sprite_style_unification_20261107')
paths = [
    *[f'shibuki_audit/rising_fire_native{page:02d}/{form}_comparison.png' for page in (1, 2) for form in ('base', 'fourth')],
    *[f'shibuki_audit/rising104_arm_native02/{form}_comparison.png' for form in ('base', 'fourth')],
    'shibuki_audit/rising_fire_contact_probe02/contact_spatial_probe.png',
    'nana_audit/ultimate_wall_repaint/before_a_registered_v1/comparison.png',
    *[f'nana_audit/ultimate_wall_repaint/{folder}/comparison_{page}.png' for folder in ('contacts_probe_v2', 'canonical_cases_probe_v2') for page in (1, 2)],
    'zero_audit/rin_extension/saber_followup03_registered_v1/normal_comparison.png',
    *[f'zero_audit/rin_extension/prepared_saber_followup03/{form}_readback_{page:02d}.png' for form in ('normal', 'black') for page in (0, 1)],
    'zero_audit/rin_extension/saber_followup04_registered_v1/normal_comparison.png',
]
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / path).as_posix(), 'sha256': hashlib.sha256((W / path).read_bytes()).hexdigest(), 'root_actually_viewed': True} for path in paths],
    'findings': {
        'shibuki': 'New Rising Fire base/Fourth details reviewed. Corrected104 new arm preserves old fist/effect contact; charged cyan spatial probe is not a phase simulation. Ultimate and packing still pending.',
        'nana': 'New wall6 body/contact and canonical weapon-case comparisons reviewed. New hair/cloth detail and hand/foot registration direction accepted. Bare outfit and6 firing arms still pending.',
        'rin': 'Packed168 normal/red readbacks accepted for candidate; resolves frozen root-review pending externally. Next236/238/240/242 registration direction accepted, pending packing and verification.',
    },
    'actual_gameplay_evidence_separate': 'runtime/riko_allboss_summary.json',
    'all_characters_complete': False, 'user_acceptance': False,
}
(W / 'root_review_checkpoint21.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
