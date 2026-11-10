"""Bind only audited, physically frozen candidates to an isolated checkpoint."""
from pathlib import Path
import argparse, hashlib, json

ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=('br', 'rn'))
parser.add_argument('--rin-plan', default='rn_pending_v8a_components.json')
args = parser.parse_args()
plan = read(W / ('br_pending_v8f_components.json' if args.mode == 'br' else args.rin_plan))
plan['output'] = f"out/{plan['project']}/sprite_style_unification_20261107_v8"
plan['checkpoint_label'] = 'four_character_style_checkpoint_8'
plan['review_images'] = []
prior = read(W / f'staging_{args.mode}_v7.json')
for name, resource in plan['resources'].items():
    path = ROOT / resource['path']
    assert sha(path) == resource['after'], name
    # Unchanged candidates retain the already verified v7 binding.
    if resource['after'] != prior['resources'][name]['after']:
        assert (path.parent / 'FROZEN.json').is_file(), f'Not frozen: {path.parent}'
    if 'static_body_patch' in resource:
        patch = resource['static_body_patch']
        assert sha(ROOT / patch['recipe']) == patch['sha256']
if args.mode == 'br':
    pictures = [('riko', 'Boot material detail', 'riko/prepared_ground_boots_v13/normal_readback_00.png'),
                ('shibuki', 'Air pose detail', 'shibuki_audit/air_pack_probe01/readback/base_actual_00.png')]
else:
    rin_folder = Path(plan['resources']['PL01_U.ARC']['path']).parent
    pictures = [('rin', 'Ground pose detail', str((ROOT / rin_folder / 'normal_readback_00.png').relative_to(W))),
                ('nana', 'Dash pose detail', 'nana_audit/dash_repaint/packed_dash_candidate_v1/readback_1.png')]
for character, label, rel in pictures:
    p = W / rel
    assert p.is_file(), p
    plan['review_images'].append(dict(character=character, label=label, path=str(p.relative_to(ROOT))))
dest = W / f'staging_{args.mode}_v8.json'
encoded = json.dumps(plan, indent=2) + '\n'
if dest.exists():
    assert dest.read_text('utf8') == encoded, 'Checkpoint already bound to other resources'
else:
    dest.write_text(encoded, 'utf8')
print(dest)
