import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path('work/sprite_style_unification_20261107')
paths = [
    'shibuki_audit/ultimate_air_native01/before_comparison.png',
    'shibuki_audit/ultimate_air_native01/after_comparison.png',
    'nana_audit/ultimate_wall_repaint/packed_wall_diagnostic_v1/readback_1.png',
    'nana_audit/ultimate_wall_repaint/packed_wall_diagnostic_v1/readback_2.png',
]
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / p).as_posix(), 'sha256': hashlib.sha256((W / p).read_bytes()).hexdigest(), 'root_actually_viewed': True} for p in paths],
    'findings': {
        'shibuki': 'Ultimate air33/35/39 both costumes: new head/hair/garment detail improves flat old masses. Registration direction accepted; remaining1-2px hand/foot contacts and shared layers still pending. Not packed or runtime-tested.',
        'nana': 'Packed twelve wall poses, both costumes: six firing arms, shoulder connections, bare skin shading and original muzzle direction accepted. No additional certain detached limb/old jacket residue found in the two boards. Producer/independent freeze pending.',
    },
    'all_characters_complete': False, 'user_acceptance': False,
}
(W / 'root_review_checkpoint23.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
