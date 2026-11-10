"""Bind reviewed task-local candidates; active game pointers remain unchanged."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ap = argparse.ArgumentParser()
ap.add_argument('mode', choices=['br', 'rn'])
ap.add_argument('--nana-wall', type=Path)
a = ap.parse_args()
prior = read(W / f'staging_{a.mode}_v9.json')
p = read(W / ('br_pending_v10_rising.json' if a.mode == 'br' else 'rn_pending_v10_rin191.json'))
if a.mode == 'rn':
    assert a.nana_wall is not None, 'Reviewed, frozen Nana wall directory is required'
    d = a.nana_wall.resolve()
    assert d.is_relative_to(W / 'nana_audit')
    arc = d / 'PL02_U.ARC'
    assert sha(arc) == 'e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'
    p['resources']['PL02_U.ARC']['path'] = arc.relative_to(ROOT).as_posix()
    p['resources']['PL02_U.ARC']['after'] = sha(arc)
p['output'] = f"out/{p['project']}/sprite_style_unification_20261107_v10"
p['checkpoint_label'] = 'four_character_style_checkpoint_10'
p['review_images'] = []
p['candidate_freeze_bindings'] = {}
for name, row in p['resources'].items():
    resource = ROOT / row['path']
    assert sha(resource) == row['after'], name
    if row['after'] != prior['resources'][name]['after']:
        frozen = resource.parent / 'FROZEN.json'
        record = read(frozen)
        # Different producers use either an explicit file map or candidate/proof bindings.
        if isinstance(record.get('files'), list):
            assert record['asset_sha256'] == row['after']
            for bound in record['files']:
                assert sha(ROOT / bound['path']) == bound['sha256'], bound['path']
        elif 'files' in record:
            for rel, expected in record['files'].items():
                assert sha(resource.parent / rel) == expected, rel
        else:
            assert record['candidate_sha256'] == row['after']
            assert sha(resource.parent / 'proposal.json') == record['proposal_sha256']
            for proof in record.get('proofs', {}).values():
                assert sha(ROOT / proof['path']) == proof['sha256']
        p['candidate_freeze_bindings'][name] = {'path': frozen.relative_to(ROOT).as_posix(), 'sha256': sha(frozen)}
    if 'static_body_patch' in row:
        assert sha(ROOT / row['static_body_patch']['recipe']) == row['static_body_patch']['sha256']
pictures = ([
    ('riko', '리코 부츠 세부', 'riko/prepared_ground_boots_v13/normal_readback_00.png'),
    ('shibuki', '시부키 라이징 파이어', 'shibuki_audit/rising_base_pack_probe02/fourth_readback_01.png'),
] if a.mode == 'br' else [
    ('rin', '린 빙열참', 'zero_audit/rin_extension/prepared_ice01/normal_readback_00.png'),
    ('nana', '나나 얼티밋 벽 사격', 'nana_audit/ultimate_wall_repaint/packed_wall_diagnostic_v1/readback_2.png'),
])
for character, label, rel in pictures:
    image = W / rel
    assert image.is_file()
    p['review_images'].append({'character': character, 'label': label, 'path': image.relative_to(ROOT).as_posix()})
dest = W / f'staging_{a.mode}_v10.json'
text = json.dumps(p, ensure_ascii=False, indent=2) + '\n'
if dest.exists():
    assert dest.read_text('utf8') == text, 'Existing checkpoint has different bindings'
else:
    dest.write_text(text, 'utf8')
print(dest)
