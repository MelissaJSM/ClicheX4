"""Verify the exact UI beam copy, reject malformed candidates, then freeze it."""
from pathlib import Path
import sys, json, hashlib, copy
ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.build_sprite_style_selection_v2 import check_selection, check_selection_body, check_zero_selection_body
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.c01_audio_build import read_disc
from scripts import build_sprite_consistency as builder
from src.psx_player import composition_frame
from src.psx_ui_atlas import tile_pixels, write_tile
sha = lambda b: hashlib.sha256(b).hexdigest()
folder = W / 'selection_shibuki_beam13'
plan = json.loads((W / 'staging_br_v13.json').read_text('utf8'))
source = ROOT / plan['source_bin']
assert sha(source.read_bytes()) == plan['source_sha256']
old = read_disc(source, ('ST0E_U1.ARC',))[0]['ST0E_U1.ARC']
new = (folder / 'ST0E_U1.ARC').read_bytes()
assert sha(new) == 'ea2167e98f8ae045c4353cca18cc571614e34949160cd85cc14ac9a6cb8e1c54'
plan['resources']['ST0E_U1.ARC'].update(path=(folder / 'ST0E_U1.ARC').relative_to(ROOT).as_posix(), after=sha(new))
plan['sync_shibuki_selection_beam'] = True

def once(path, body):
    if path.exists():
        assert path.read_bytes() == body
    else:
        path.write_bytes(body)

def save(path, obj):
    once(path, (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf8'))

def rejected(label, fn):
    try:
        fn()
    except (ValueError, AssertionError) as e:
        return {'case': label, 'reason': str(e)}
    raise AssertionError('Bad candidate accepted: ' + label)

check_selection(old, new, True, False, True)
check_selection_body(plan)
zero_proof = check_zero_selection_body(plan)
checks = [rejected('No explicit beam permission', lambda: check_selection(old, new, True, False))]
parts, tx = entry(new, 10), entry(new, 0x10102)
for label, offset in [('Portrait pixels', 50000), ('Zero unrelated texture', 70000)]:
    mutated = bytearray(tx); mutated[offset] ^= 1
    bad = replace_entry(new, 0x10102, bytes(mutated))
    checks.append(rejected(label, lambda bad=bad: check_selection(old, bad, True, False, True)))

def verify_declared_bad(label, data):
    path = folder / ('negative_' + label + '.arc')
    once(path, data)
    badplan = copy.deepcopy(plan)
    badplan['resources']['ST0E_U1.ARC'].update(path=path.relative_to(ROOT).as_posix(), after=sha(data))
    checks.append(rejected(label, lambda: check_selection_body(badplan)))

mutated = bytearray(parts)
beam_parts = composition_frame(parts, 2, 23)['parts']
for part in beam_parts:
    at = part['record_offset'] + 2
    mutated[at] = (mutated[at] + 1) & 255
verify_declared_bad('beam_shifted_one_pixel', replace_entry(new, 10, bytes(mutated)))

texture = bytearray(tx[90112:])
for part in beam_parts:
    tile = part['page'] * 256 + part['tile']
    pixels = bytearray(tile_pixels(texture, tile))
    if any(pixels):
        i = next(i for i, v in enumerate(pixels) if v)
        pixels[i] = 1 if pixels[i] != 1 else 2
        write_tile(texture, tile, pixels)
        break
else:
    raise AssertionError('Empty beam')
verify_declared_bad('beam_pixel_changed', replace_entry(new, 0x10102, tx[:90112] + texture))

mutated = bytearray(parts)
mutated[beam_parts[0]['record_offset']] ^= 0x20
bad = replace_entry(new, 10, bytes(mutated))
checks.append(rejected('Unknown part flags', lambda: check_selection(old, bad, True, False, True)))
checks.append(rejected('Conflicting preserved X bank', lambda: check_selection(old, new, True, True, True)))
checks.append(rejected('Nonboolean permission', lambda: check_selection(old, new, True, False, 1)))

allowed = builder.ALLOWED
builder.ALLOWED = {**allowed, 'ST0E_U1.ARC': {10, 0x10102}}
try:
    archive_proof = builder.check_resource('ST0E_U1.ARC', old, new)
    bad = bytearray(new); bad[-1] ^= 1
    checks.append(rejected('Outside artwork entry', lambda: builder.check_resource('ST0E_U1.ARC', old, bytes(bad))))
    checks.append(rejected('Resource length altered', lambda: builder.check_resource('ST0E_U1.ARC', old, new + b'\0')))
finally:
    builder.ALLOWED = allowed

proof = {'passed': True, 'candidate_sha256': sha(new), 'original_parent_sha256': sha(old),
         'archive': archive_proof, 'zero_selection': zero_proof,
         'x_body18_21_and_beam23_exact': True, 'negative_cases_rejected': checks,
         'root_review': 'work/sprite_style_unification_20261107/root_review_checkpoint48.json',
         'prior_record_offset_difference': '원 부모5300..5348→v13/후보4704..4752. 이전에 검증한 X 전신 재패킹으로 생긴 위치 차이다. 이번 빛기둥 수정은 v13 레코드 위치를 모두 보존한다.',
         'runtime_verified': False, 'active_pointer_changed': False}
save(folder / 'guard_checks_v2.json', proof)
save(folder / 'proposal.json', plan)
paths = [folder / 'ST0E_U1.ARC', folder / 'proposal.json', folder / 'guard_checks_v2.json',
         folder / 'report.json', folder / 'before.png', folder / 'after.png',
         W / 'root_review_checkpoint48.json', W / 'prepare_shibuki_selection_beam13.py',
         Path(__file__).resolve(), ROOT / 'scripts/build_sprite_style_selection_v2.py']
save(folder / 'FROZEN.json', {'frozen': True, 'asset_sha256': sha(new),
     'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())} for p in paths],
     'runtime_verified': False, 'final_user_accepted': False})
print(json.dumps({'passed': True, 'negative_cases': len(checks), 'candidate': sha(new),
                  'frozen': sha((folder / 'FROZEN.json').read_bytes())}))
