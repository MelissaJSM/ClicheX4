"""네 캐릭터의 동결 자원을 별도 중간 검토판에 연결한다. 활성 포인터는 보존한다."""
from pathlib import Path
import json, hashlib

ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

for mode, prior in [('br', 'v7h'), ('rn', 'v7f')]:
    plan = read(W / f'{mode}_pending_{prior}_components.json')
    plan['output'] = f"out/{plan['project']}/sprite_style_unification_20261107_v7"
    plan['checkpoint_label'] = 'four_character_style_checkpoint_7'
    plan['review_images'] = []
    if mode == 'br':
        frozen = ['riko/prepared_spin_clothes_v1', 'shibuki_audit/prepared_ultimate_wall01',
                  'shibuki_audit/prepared_arrival_victory01']
        pictures = [('riko', 'Spin clothing detail', 'riko/prepared_spin_clothes_v1/normal_readback_00.png'),
                    ('shibuki', 'Arrival clothing detail', 'shibuki_audit/arrival_targets01/base_comparison.png')]
    else:
        frozen = ['zero_audit/rin_extension/prepared_ground_first_v1',
                  'nana_audit/dash_repaint/packed_dash_candidate_v1']
        zero = read(W / frozen[0] / 'proposal.json')
        plan['resources']['PL01_U.ARC'].update(path=zero['resource'], after=zero['after_sha256'],
                                              static_body_patch=zero['static_body_patch'])
        nana = read(W / frozen[1] / 'proposal.json')
        for name, q in nana['files'].items():
            # Keep the supported full-disc parent's before hash, not the sequential ARC parent.
            plan['resources'][name].update(path=q['path'], after=q['after'])
        pictures = [('rin', 'Ground attack clothing detail', frozen[0] + '/normal_readback_00.png'),
                    ('nana', 'Dash clothing detail', frozen[1] + '/readback_1.png')]
    for folder in frozen:
        assert (W / folder / 'FROZEN.json').is_file(), f'Not frozen: {folder}'
    for character, label, rel in pictures:
        p = W / rel
        assert p.is_file()
        plan['review_images'].append(dict(character=character, label=label, path=str(p.relative_to(ROOT))))
    for q in plan['resources'].values():
        assert sha(ROOT / q['path']) == q['after']
    dest = W / f'staging_{mode}_v7.json'
    encoded = json.dumps(plan, indent=2) + '\n'
    if dest.exists():
        assert dest.read_text('utf8') == encoded
    else:
        dest.write_text(encoded, 'utf8')
    print(dest)
