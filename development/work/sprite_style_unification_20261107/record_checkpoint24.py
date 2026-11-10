import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
W = Path('work/sprite_style_unification_20261107')
paths = [
    'zero_audit/rin_extension/ice_spin_registered_v1/normal_comparison.png',
    *[f'zero_audit/rin_extension/spin200_review/{name}.png' for name in (
        'air_spin_normal_strip', 'air_spin_black_strip', 'rotation_normal_closed_art_cycle', 'rotation_normal_effects_reference')],
    'shibuki_audit/ultimate_air_native02_corrected02/before_comparison.png',
    'shibuki_audit/ultimate_air_native02_corrected02/after_comparison.png',
    'nana_audit/ultimate_dash_repaint/before_first_registered_v2/comparison.png',
]
result = {'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / p).as_posix(), 'sha256': hashlib.sha256((W / p).read_bytes()).hexdigest(), 'root_actually_viewed': True} for p in paths],
    'findings': {
        'rin': '144/161/163 new contact registration and normal/red real100 sequence accepted. Separate closed art cycle and effect reference reviewed; actual100 ends175->160, not175->161. No additional certain head/cuff separation or sudden body-width change found. Candidate200 accepted, gameplay unverified.',
        'shibuki': '37/41/43 both costumes reviewed. Local correction resolves41 third-hand artifact; original two fists and dark accessory remain. Shared layers and firing arms still pending.',
        'nana': '67/71/79/93 new dash detail reviewed.67/79/93 hair/cloth direction accepted, foot-x registration remains.71 near/far shoes still merge visually and needs local correction before packing.',
    }, 'actual_gameplay_evidence_separate': 'runtime/shibuki_checkpoint10_summary.json',
    'all_characters_complete': False, 'user_acceptance': False}
(W / 'root_review_checkpoint24.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
