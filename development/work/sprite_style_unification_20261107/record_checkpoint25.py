import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
W = Path('work/sprite_style_unification_20261107')
paths = [
    'zero_audit/rin_extension/followthrough01/anchor_probe/normal_comparison.png',
    'shibuki_audit/rising_right_hand_native01/original_effect_comparison.png',
    'shibuki_audit/rising_runtime_followup01/us_vs_custom.png',
    'nana_audit/ultimate_dash_repaint/first_contacts_probe_v1/comparison.png',
    'nana_audit/ultimate_dash_repaint/dash71_legs_registered_v1/comparison.png',
    'nana_audit/rising_contact_review_v1/comparison.png',
    *[f'shibuki_audit/ultimate_air_common_probe03/comparison_{i:02}.png' for i in range(2)],
    *[f'shibuki_audit/ultimate_air_contacts01/{form}_comparison_{i:02}.png' for form in ('before', 'after') for i in range(2)],
    *[f'shibuki_audit/ultimate_air_native03/{form}_comparison.png' for form in ('before', 'after')],
]
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / p).as_posix(), 'sha256': hashlib.sha256((W / p).read_bytes()).hexdigest(), 'root_actually_viewed': True} for p in paths],
    'findings': {
        'rin': '146/156/158/197 new hair and clothing detail is retained, but new legs extend beyond accepted feet; reject packing until local authored lower-body correction. No global resize/row deletion.',
        'shibuki_air': '33/35/37/39/41/43 shared-layer and foot registration, plus45/47/49 both outfits, visually preserve new detail. No additional definite seam found. Firing composition and packed runtime still pending.',
        'shibuki_rising': 'OriginalUS comparison confirms pre-existing wrong raised hand in103/104. Newly authored base/Fourth104 restores overlap with actual effect footprint; raised arm height still under correction. Whole-body mirroring and moving native effects are not used.',
        'nana_dash': '67/79/93 local foot registration accepted as direction.71 local lower-leg art improves separation but shoes still read as one broad gray/black shape; further local correction required.',
        'nana_rising': 'Static originalUS hand-contact comparison confirms same wrong-side raised-hand issue in all4forms; Nana live flame contact not yet tested.',
    },
    'actual_gameplay_evidence_separate': 'runtime/rin_checkpoint10_summary.json',
    'all_characters_complete': False, 'user_acceptance': False,
}
(W / 'root_review_checkpoint25.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
