import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
W = Path('work/sprite_style_unification_20261107')
paths = [
    *[f'zero_audit/rin_extension/followthrough_registered_v1/{color}_comparison.png' for color in ('normal', 'black')],
    'nana_audit/ultimate_dash_repaint/before_second_registered_v1/comparison.png',
    'nana_audit/ultimate_dash_repaint/second_contact_grids_v1/081_feet.png',
    *[f'zero_audit/rin_extension/prepared_followthrough01/{color}_readback_{i:02}.png' for color in ('normal', 'black') for i in range(2)],
    *[f'zero_audit/rin_extension/followthrough205_review/{name}_{color}_strip.png' for name in ('rising_start', 'rising_recovery', 'ladder_entry') for color in ('normal', 'black')],
    *[f'shibuki_audit/rising_right_hand_native04/{form}_comparison.png' for form in ('base', 'fourth')],
]
result = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'art_review_images': [{'path': (W / p).as_posix(), 'sha256': hashlib.sha256((W / p).read_bytes()).hexdigest(), 'root_actually_viewed': True} for p in paths],
    'findings': {
        'rin': 'Local lower-body redraw preserves newly detailed head/hands/clothing and corrects feet in146/156/158/197. Packed5references including exact212copy accepted in normal/red. Six native-sequence strips reviewed;199/202 remain old art and are explicitly pending.',
        'nana': '69/75/77 hair/cloth quality follows accepted new air/idle.75still merges two shoes,81steps too widely relative to original contacts. Local leg redraw requested; not accepted for packing yet.',
        'shibuki': 'Base/Fourth103right-hand preparation and104right-arm raise preserve new head/clothing detail. Art direction accepted. Alpha-threshold and effect-contact checks, plus actual packed readback, remain before integration.',
    },
    'rin_candidate_sha256': 'd3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8',
    'all_characters_complete': False, 'user_acceptance': False,
}
(W / 'root_review_checkpoint26.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'actual_reviewed_images': len(paths)}))
