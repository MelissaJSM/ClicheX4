"""Bind reviewed frozen incremental assets; never alter active game pointers."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = argparse.ArgumentParser()
p.add_argument('mode', choices=['br', 'rn'])
p.add_argument('--asset', nargs=3, action='append', metavar=('ARC_NAME', 'DIRECTORY', 'EXPECTED_SHA256'), required=True)
p.add_argument('--review-checkpoints', nargs='+', type=int, default=[28, 29, 30])
a = p.parse_args()
plan = read(W / f'staging_{a.mode}_v11.json')
seen = set()
for name, directory, expected in a.asset:
    assert name in plan['resources'] and name not in seen
    seen.add(name)
    directory = (ROOT / directory).resolve()
    assert directory.is_relative_to(W)
    arc = directory / name
    assert sha(arc) == expected
    frozen_path = directory / 'FROZEN.json'
    frozen = read(frozen_path)
    if isinstance(frozen.get('files'), list):
        assert frozen['asset_sha256'] == expected
        for item in frozen['files']:
            assert sha(ROOT / item['path']) == item['sha256']
    elif 'files' in frozen:
        for rel, digest in frozen['files'].items():
            assert sha(directory / rel) == digest
    else:
        assert frozen['candidate_sha256'] == expected
        assert sha(directory / 'proposal.json') == frozen['proposal_sha256']
        for proof in frozen.get('proofs', {}).values():
            assert sha(ROOT / proof['path']) == proof['sha256']
    row = plan['resources'][name]
    row['path'] = arc.relative_to(ROOT).as_posix()
    row['after'] = expected
    if name == 'PL01_U.ARC':
        recipe = directory / 'static_effects.json'
        assert sha(recipe) == frozen['static_recipe_sha256']
        row['static_body_patch'] = {'recipe': recipe.relative_to(ROOT).as_posix(), 'sha256': sha(recipe)}
    plan.setdefault('candidate_freeze_bindings', {})[name] = {
        'path': frozen_path.relative_to(ROOT).as_posix(), 'sha256': sha(frozen_path)}

for name, row in plan['resources'].items():
    assert sha(ROOT / row['path']) == row['after'], name
    if 'static_body_patch' in row:
        assert sha(ROOT / row['static_body_patch']['recipe']) == row['static_body_patch']['sha256']
for binding in plan.get('candidate_freeze_bindings', {}).values():
    assert sha(ROOT / binding['path']) == binding['sha256']
plan['output'] = f"out/{plan['project']}/sprite_style_unification_20261107_v12"
plan['checkpoint_label'] = 'four_character_style_checkpoint_12'
plan['review_images'] = []
plan['root_visual_review_records'] = [
    {'path': (W / f'root_review_checkpoint{i}.json').relative_to(ROOT).as_posix(),
     'sha256': sha(W / f'root_review_checkpoint{i}.json')} for i in a.review_checkpoints]
dest = W / f'staging_{a.mode}_v12.json'
text = json.dumps(plan, ensure_ascii=False, indent=2) + '\n'
if dest.exists():
    assert dest.read_text('utf8') == text, 'Checkpoint already bound to a different candidate'
else:
    dest.write_text(text, 'utf8')
print(dest)
